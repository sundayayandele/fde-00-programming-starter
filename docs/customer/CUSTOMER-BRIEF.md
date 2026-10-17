# Customer brief: complaint data you can trust

> Fictional engagement used for the lab. "Northfield Bank" is an invented mid-sized retail bank;
> the data is the public CFPB complaint database standing in for the bank's own complaints.

## Situation

Northfield's complaints team reports monthly from spreadsheet exports. Numbers differ between teams, nobody can say how many complaints were dropped or duplicated, and narratives sometimes contain card and phone numbers. The bank wants to pilot ML triage of complaints next quarter (fde-01) and has been told the data is "not ready".

## What they asked for

1. A daily, automated feed of complaints into one database.
2. A report they can defend: counts by product, issue, company and month; timely-response rate.
3. Proof of quality for every load: what was rejected and why, duplicates, missing fields.
4. No raw card, account or phone numbers stored in narratives.
5. Runs on their platform team's OpenShift, and on a cloud for the pilot.

## Success criteria (agreed)

| Criterion | Target | How we show it |
| --- | --- | --- |
| Daily load completes | Every day, before 07:00 UTC | `ingest_runs`; `IngestStale` alert |
| Re-runs are safe | Same input → same row count | Idempotency tests on SQLite and Postgres |
| Every rejection explained | 100% of rejected rows carry a reason | Quality report `rejection_reasons` |
| PII in narratives | Typed placeholders for emails, SSNs, card, phone, account numbers | Unit tests; `pii_values_masked` per run |
| Throughput | Full-history backfill finishes inside a working day | Benchmark: ~160k records/min on Postgres (synthetic) |
| Portability | Same image on desktop, OpenShift, AWS, Azure, GCP | Smoke test on each path |

## Out of scope for this phase

Classification and routing (fde-01), LLM summarisation (fde-02), names and street addresses in PII masking (fde-03 evaluates NER).

## Stakeholders

| Role | Interest |
| --- | --- |
| Head of complaints | One trusted number per month |
| Data protection officer | No unnecessary personal data stored |
| Platform team | Runs on OpenShift with restricted security context |
| ML lead | Clean, de-duplicated training data next quarter |
