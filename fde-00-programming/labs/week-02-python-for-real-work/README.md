# Week 02: Python for real work: PII masking and validation

**Goal:** map a raw source row to a validated `Complaint`, with personal data masked and every failure explained.

## Brief

The data protection officer has one condition for the pilot: no raw email addresses, social security numbers, card, phone or account numbers stored in narratives. The ML lead has another: every row that is dropped must say why.

## Concepts

Dictionaries and comprehensions, `re.subn`, ordering of regex rules, tuples as return values, pydantic models and `ValidationError`, defensive programming.

## Steps

In `src/complaints_ingest/clean.py`:

1. `mask_pii(text)`: apply the patterns in `_PII_PATTERNS` **in order**, replacing matches with their placeholder, and return `(masked_text, count)`. `None` returns `(None, 0)`. Why does the order matter? (Try putting `[ACCOUNT]` before `[CARD]`.)
2. `to_complaint(row, field_map)`:
   - Rename source keys to canonical names using `field_map`; ignore unknown keys.
   - Parse the two date fields with `parse_date`, `timely` and `consumer_disputed` with `parse_bool`, join list-valued `tags` with `", "`, and `normalise_text` everything else.
   - If any of `REQUIRED_FIELDS` is missing, return `(None, "missing required fields: ...", 0)`.
   - Mask the narrative, build the `Complaint`, and turn a `ValidationError` into `(None, "invalid <field>: <message>", 0)`.
3. Run `pytest tests/test_clean.py -m exercise` until green. Then run `complaints-ingest ingest-synthetic --count 2000` and `complaints-ingest report`.
4. Read `tests/fixtures/cfpb_api_page.json`: which row is rejected and why?

## Check

```bash
pytest tests/test_clean.py -m exercise
complaints-ingest ingest-synthetic --count 2000 && complaints-ingest runs
```

## Evidence

The run log line showing PII values masked, and a list of three kinds of personal data your masking does **not** catch, with an example of each.

## Stretch

Add an IBAN pattern (`[IBAN]`) with tests, without breaking the existing ones. What false positives do you risk?
