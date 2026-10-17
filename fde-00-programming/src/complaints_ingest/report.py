"""Summary queries for the CLI report and the API."""

from __future__ import annotations

from sqlalchemy import Engine, case, func, select

from complaints_ingest.store import complaints


def counts_by_product(engine: Engine, limit: int = 20) -> list[dict]:
    """Complaints per product, largest first."""
    # >>> SOLUTION: week-04 GROUP BY query
    stmt = (
        select(complaints.c.product, func.count().label("complaints"))
        .group_by(complaints.c.product)
        .order_by(func.count().desc(), complaints.c.product)
        .limit(limit)
    )
    with engine.connect() as conn:
        return [{"product": p, "complaints": n} for p, n in conn.execute(stmt)]
    # <<< SOLUTION


def counts_by_month(engine: Engine) -> list[dict]:
    if engine.dialect.name == "postgresql":
        month = func.to_char(complaints.c.date_received, "YYYY-MM")
    else:
        month = func.strftime("%Y-%m", complaints.c.date_received)
    stmt = select(month.label("month"), func.count()).group_by("month").order_by("month")
    with engine.connect() as conn:
        return [{"month": m, "complaints": n} for m, n in conn.execute(stmt)]


def top_issues(engine: Engine, limit: int = 10) -> list[dict]:
    stmt = (
        select(complaints.c.issue, func.count().label("n"))
        .where(complaints.c.issue.is_not(None))
        .group_by(complaints.c.issue)
        .order_by(func.count().desc(), complaints.c.issue)
        .limit(limit)
    )
    with engine.connect() as conn:
        return [{"issue": i, "complaints": n} for i, n in conn.execute(stmt)]


def top_companies(engine: Engine, limit: int = 10) -> list[dict]:
    stmt = (
        select(complaints.c.company, func.count().label("n"))
        .group_by(complaints.c.company)
        .order_by(func.count().desc(), complaints.c.company)
        .limit(limit)
    )
    with engine.connect() as conn:
        return [{"company": c, "complaints": n} for c, n in conn.execute(stmt)]


def timely_response_rate(engine: Engine) -> float | None:
    stmt = select(
        func.sum(case((complaints.c.timely.is_(True), 1), else_=0)),
        func.count(complaints.c.timely),
    )
    with engine.connect() as conn:
        timely, known = conn.execute(stmt).one()
    return round(timely / known, 4) if known else None


def summary(engine: Engine) -> dict:
    with engine.connect() as conn:
        total, first, last = conn.execute(
            select(func.count(), func.min(complaints.c.date_received),
                   func.max(complaints.c.date_received))
        ).one()
    return {
        "total_complaints": total,
        "date_received_min": first.isoformat() if first else None,
        "date_received_max": last.isoformat() if last else None,
        "timely_response_rate": timely_response_rate(engine),
        "by_product": counts_by_product(engine, limit=10),
        "top_issues": top_issues(engine, limit=5),
        "top_companies": top_companies(engine, limit=5),
    }
