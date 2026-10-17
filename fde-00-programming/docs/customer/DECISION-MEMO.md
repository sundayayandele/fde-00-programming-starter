# Decision memo: complaint-data pipeline pilot

**To:** Head of Complaints, Northfield Bank (fictional) · **From:** Forward-deployed engineer · **Date:** 2026-10-12

## Recommendation

Adopt the ingestion service for the ML-triage pilot: a daily scheduled job writing to the bank's managed Postgres, with the report API for the complaints team. Start on the platform team's OpenShift cluster; keep the cloud stack as a fallback.

## Why

- **Defensible numbers.** Every load records rows read, stored and rejected, with reasons, duplicates and schema drift. Re-running a day does not double-count (tested).
- **Personal data reduced at the door.** Emails, SSNs, card, phone and account numbers in narratives are replaced with typed placeholders before storage, and counted per run.
- **Fast enough.** Measured 161,805 records per minute into Postgres on a 2-vCPU machine (synthetic data); a full multi-million-row history backfill fits in well under a day. Daily deltas are network-bound and take minutes.
- **Low running cost.** Estimated USD 10–30 per month on a hyperscaler at pilot size, dominated by the managed database (see COST-TCO). On existing OpenShift, the marginal cost is one small pod and one daily job.

## Options considered

| Option | Verdict |
| --- | --- |
| Keep spreadsheet exports | Rejected: no audit trail, PII exposure, blocks ML |
| Buy a complaints analytics product | Deferred: 3–6 month procurement; does not produce training data |
| This pipeline on OpenShift + managed Postgres | **Recommended** |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Source changes field names | Schema drift reported per run; alert on unexpected fields |
| Names and addresses not masked | Documented; NER evaluation in the next phase before any LLM use |
| Job silently stops | `IngestStale` alert after 26 hours |

## Decision needed

Approve a four-week pilot with read access to the complaints export and a Postgres database provisioned by the platform team.
