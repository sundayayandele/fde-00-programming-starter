# Datasets

Datasets are downloaded at run time and never committed. `data/` is git-ignored except its README.

## Primary: CFPB Consumer Complaint Database (banking)

| Field | Value |
| --- | --- |
| Publisher | US Consumer Financial Protection Bureau |
| Landing page | https://www.consumerfinance.gov/data-research/consumer-complaints/ |
| Search API (used by `ingest-api`) | `https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/` |
| Bulk CSV (used by `ingest-csv`) | `https://files.consumerfinance.gov/ccdb/complaints.csv.zip` (`make download-csv`) |
| Licence / terms | US federal government open data, generally public domain in the US; CFPB states complaints are not verified and narratives are published only with consent and scrubbed of personal information. **Verify the current terms on the landing page before redistribution.** |
| Size | Millions of complaints; the unzipped CSV is several GB |
| Update cadence | Daily |
| Version | Record the download date and `sha256` (written by `make download-csv` to `data/complaints.csv.sha256`) |

### Verify before a production pull

Field and parameter names below are from CFPB's public documentation as of mid-2026, written without live access during the build. Check them against the API docs (`.../search/api/v1/` documentation on the landing page) and adjust `schema.py` / `cfpb.py` if needed. The pipeline reports renamed fields as schema drift rather than failing silently.

| Used here | Purpose |
| --- | --- |
| `size`, `frm`, `sort=created_date_desc`, `format=json`, `no_aggs=true` | Paging and ordering |
| `date_received_min`, `date_received_max`, `product` | Filters |
| Response `hits.hits[]._source` | Records |
| `complaint_what_happened` | Narrative field in the API (`Consumer complaint narrative` in the CSV) |
| Paging cap of 10,000 results per query (`MAX_OFFSET`) | Use date windows or the CSV for more |

## Synthetic data

`complaints_ingest.synthetic.make_complaints(n, seed)` produces API-shaped rows with invented companies and planted PII. Used for offline labs, tests and benchmarks. Never report synthetic numbers as CFPB statistics.

## Extension datasets (stretch labs)

| Dataset | Domain | Where | Licence | Notes |
| --- | --- | --- | --- | --- |
| Banking77 | Banking intents | Hugging Face `PolyAI/banking77` | CC BY 4.0 (verify) | 13k short customer queries, 77 intents |
| Bitext customer support | Retail banking / support | Hugging Face `bitext/Bitext-customer-support-llm-chatbot-training-dataset` (verify id) | CDLA-Sharing 1.0 (verify) | Synthetic support conversations |

Stretch labs map these to the same pipeline with a new field map; see week 4.
