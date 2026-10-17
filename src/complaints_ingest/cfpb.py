"""Read complaints from the CFPB search API or the CFPB bulk CSV.

Source: CFPB Consumer Complaint Database (https://www.consumerfinance.gov/data-research/consumer-complaints/).
API parameter names follow CFPB's public API documentation as of October 2026; confirm
them against the live docs before a production pull (see docs/datasets/DATASETS.md).
"""

from __future__ import annotations

import csv
import time
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import httpx

API_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
MAX_OFFSET = 10_000  # the search API caps simple from/size paging; use the bulk CSV beyond this
USER_AGENT = "fde-00-programming (learning project; github.com/sundayayandele)"


def parse_page(payload: object) -> list[dict]:
    """Extract raw complaint dicts from one API response.

    The API returns an Elasticsearch-style body: {"hits": {"hits": [{"_source": {...}}]}}.
    Tolerate a plain list too, so recorded fixtures and future formats keep working.
    """
    raise NotImplementedError("TODO week-04 parse the API response: see labs/")


class CFPBClient:
    """Small, polite client for the CFPB search API (retries, back-off, page size)."""

    def __init__(self, base_url: str = API_URL, *, page_size: int = 500, max_retries: int = 4,
                 pause_seconds: float = 0.5, transport: httpx.BaseTransport | None = None) -> None:
        self.page_size = page_size
        self.max_retries = max_retries
        self.pause_seconds = pause_seconds
        self._http = httpx.Client(timeout=60, transport=transport, follow_redirects=True,
                                  headers={"User-Agent": USER_AGENT})
        self.base_url = base_url

    def _get(self, params: dict) -> object:
        delay = 1.0
        for attempt in range(self.max_retries + 1):
            response = self._http.get(self.base_url, params=params)
            if response.status_code == 200:
                return response.json()
            if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            response.raise_for_status()
        raise RuntimeError("unreachable")

    def iter_complaints(self, *, since: date | None = None, until: date | None = None,
                        product: str | None = None, limit: int | None = None) -> Iterator[dict]:
        """Yield raw complaint dicts, newest first, until `limit` or the paging cap."""
        fetched = 0
        offset = 0
        while offset < MAX_OFFSET:
            size = self.page_size if limit is None else min(self.page_size, limit - fetched)
            if size <= 0:
                return
            params: dict[str, object] = {"size": size, "frm": offset, "sort": "created_date_desc",
                                         "format": "json", "no_aggs": "true"}
            if since:
                params["date_received_min"] = since.isoformat()
            if until:
                params["date_received_max"] = until.isoformat()
            if product:
                params["product"] = product
            rows = parse_page(self._get(params))
            if not rows:
                return
            yield from rows
            fetched += len(rows)
            offset += len(rows)
            if len(rows) < size:
                return
            time.sleep(self.pause_seconds)

    def close(self) -> None:
        self._http.close()


def iter_csv(path: str | Path) -> Iterator[dict]:
    """Stream rows from the CFPB bulk CSV (or a sample of it) without loading it all."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)
