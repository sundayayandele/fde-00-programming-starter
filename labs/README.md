# Labs

One folder per curriculum week. Phase 0 runs weeks 0–4.

| Week | Lab | Exercises |
| --- | --- | --- |
| 0 | [Set up](week-00-setup/README.md) | none |
| 1 | [Python basics](week-01-python-basics/README.md) | `normalise_text`, `parse_bool`, `parse_date` |
| 2 | [Python for real work](week-02-python-for-real-work/README.md) | `mask_pii`, `to_complaint` |
| 3 | [Developer tooling](week-03-developer-tooling/README.md) | `null_counts` |
| 4 | [Data handling](week-04-data-handling/README.md) | `parse_page`, `upsert_complaints`, `counts_by_product`, results table |

Each lab has: goal, brief, concepts, steps (naming the files and TODOs), check (the command that proves it works), evidence (for your portfolio) and a stretch task.

`make exercises` lists what is left. Exercise tests carry `@pytest.mark.exercise`; the starter's `make test` and CI skip them so your build stays green while you work.
