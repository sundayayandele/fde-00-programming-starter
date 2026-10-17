import json

import pytest

from complaints_ingest.cli import main


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'sub' / 'cli.db'}"


def test_init_db_and_runs(db_url, capsys):
    assert main(["--database-url", db_url, "init-db"]) == 0
    assert main(["--database-url", db_url, "runs"]) == 0
    assert "tables ready" in capsys.readouterr().out


@pytest.mark.exercise
def test_ingest_synthetic_then_report(db_url, capsys):
    assert main(["--database-url", db_url, "ingest-synthetic", "--count", "50"]) == 0
    assert "stored 50" in capsys.readouterr().out
    assert main(["--database-url", db_url, "report", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["total_complaints"] == 50
    assert main(["--database-url", db_url, "report"]) == 0
    assert "By product:" in capsys.readouterr().out
    assert main(["--database-url", db_url, "runs"]) == 0
    assert "synthetic" in capsys.readouterr().out


@pytest.mark.exercise
def test_ingest_csv(db_url, csv_path, capsys):
    assert main(["--database-url", db_url, "ingest-csv", str(csv_path)]) == 0
    out = capsys.readouterr().out
    assert "rejected 1" in out
    assert "rejection reasons" in out


@pytest.mark.exercise
def test_ingest_api_uses_client(db_url, api_page, monkeypatch, capsys):
    from complaints_ingest import cli
    from complaints_ingest.cfpb import parse_page

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def iter_complaints(self, **kwargs):
            assert kwargs["limit"] == 10
            return iter(parse_page(api_page))

        def close(self):
            pass

    monkeypatch.setattr(cli, "CFPBClient", FakeClient)
    assert main(["--database-url", db_url, "ingest-api", "--days", "3", "--limit", "10"]) == 0
    assert "stored 2" in capsys.readouterr().out
