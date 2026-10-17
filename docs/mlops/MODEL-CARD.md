# Data card: stored complaints (this phase has no model)

Phase 0 trains no model. This card documents the dataset the pipeline produces, which `fde-01` and `fde-04` train on.

| Field | Value |
| --- | --- |
| Name | `complaints` table, produced by `complaints-ingest` 1.0.0 |
| Source | CFPB Consumer Complaint Database (API and bulk CSV); synthetic generator for tests |
| Unit | One complaint, keyed by `complaint_id` |
| Fields | 18 canonical fields (see `schema.py`) + `ingested_at` |
| Required | `complaint_id`, `date_received`, `product`, `company` |
| Transformations | Whitespace normalised; placeholders (`None`, `N/A`, `nan`, empty) → NULL; yes/no → boolean; dates parsed from ISO, ISO timestamps, `MM/DD/YY(YY)`; list tags joined; PII masked in `narrative` |
| Known gaps | Narratives exist only where consumers consented (a minority of complaints); `consumer_disputed` is not collected for recent years; product and issue taxonomies changed over time |
| Personal data | CFPB scrubs narratives; this pipeline additionally masks emails, SSNs, card, phone and account numbers. Names and addresses are not masked |
| Intended use | Reporting; training complaint-routing classifiers; building evaluation and fine-tuning sets |
| Not intended for | Judging individual companies' conduct (complaints are not verified by CFPB); any use that re-identifies consumers |
| Quality evidence | Per-run quality report in `ingest_runs.quality_json` |
