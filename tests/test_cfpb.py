from datetime import date

import httpx
import pytest

from complaints_ingest.cfpb import CFPBClient, iter_csv, parse_page


@pytest.mark.exercise
def test_parse_page_hits(api_page):
    rows = parse_page(api_page)
    assert [r["complaint_id"] for r in rows] == ["8800001", "8800002", "8800003"]


@pytest.mark.exercise
@pytest.mark.parametrize("payload", [None, "text", {}, {"hits": {}}, {"hits": {"hits": []}}])
def test_parse_page_empty(payload):
    assert parse_page(payload) == []


@pytest.mark.exercise
def test_parse_page_plain_list():
    assert parse_page([{"complaint_id": "1"}, "junk"]) == [{"complaint_id": "1"}]


def _page(ids):
    return {"hits": {"hits": [{"_source": {"complaint_id": str(i)}} for i in ids]}}


@pytest.mark.exercise
def test_client_pages_until_short_page():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        seen.append(params)
        start = int(params["frm"])
        size = int(params["size"])
        ids = range(start, min(start + size, 5))
        return httpx.Response(200, json=_page(ids))

    client = CFPBClient("https://example.test/api", page_size=2, pause_seconds=0,
                        transport=httpx.MockTransport(handler))
    rows = list(client.iter_complaints(since=date(2026, 9, 1), until=date(2026, 9, 30),
                                       product="Credit card"))
    client.close()
    assert [r["complaint_id"] for r in rows] == ["0", "1", "2", "3", "4"]
    assert seen[0]["date_received_min"] == "2026-09-01"
    assert seen[0]["date_received_max"] == "2026-09-30"
    assert seen[0]["product"] == "Credit card"
    assert [p["frm"] for p in seen] == ["0", "2", "4"]


@pytest.mark.exercise
def test_client_respects_limit():
    def handler(request):
        size = int(request.url.params["size"])
        start = int(request.url.params["frm"])
        return httpx.Response(200, json=_page(range(start, start + size)))

    client = CFPBClient("https://example.test/api", page_size=4, pause_seconds=0,
                        transport=httpx.MockTransport(handler))
    assert len(list(client.iter_complaints(limit=6))) == 6


@pytest.mark.exercise
def test_client_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("complaints_ingest.cfpb.time.sleep", lambda _s: None)
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=_page([1]))

    client = CFPBClient("https://example.test/api", page_size=10,
                        transport=httpx.MockTransport(handler))
    assert len(list(client.iter_complaints())) == 1
    assert calls["n"] == 3


def test_client_raises_on_client_error(monkeypatch):
    client = CFPBClient("https://example.test/api",
                        transport=httpx.MockTransport(lambda r: httpx.Response(400)))
    with pytest.raises(httpx.HTTPStatusError):
        list(client.iter_complaints())


def test_client_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr("complaints_ingest.cfpb.time.sleep", lambda _s: None)
    client = CFPBClient("https://example.test/api", max_retries=2,
                        transport=httpx.MockTransport(lambda r: httpx.Response(429)))
    with pytest.raises(httpx.HTTPStatusError):
        list(client.iter_complaints())


def test_iter_csv_streams_rows(csv_path):
    rows = list(iter_csv(csv_path))
    assert len(rows) == 5
    assert rows[0]["Complaint ID"] == "8800101"
    assert rows[0]["Timely response?"] == "Yes"
