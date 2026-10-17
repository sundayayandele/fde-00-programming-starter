# Week 01: Python basics on messy records

**Goal:** write small, pure functions that turn messy field values into clean Python values, and prove them with parametrised tests.

## Brief

Northfield's exports contain `"  Credit   card "`, `"N/A"`, `"Yes"`, `"no"`, `"09/05/26"` and `"2026-09-02T12:00:00-05:00"` in the same columns. Every downstream number depends on reading these correctly. Unknown values must become `None`, never a guess.

## Concepts

Strings and whitespace, `None`, truthiness traps (`bool("False")`), regular expressions, `datetime.strptime` and `fromisoformat`, type hints, doctests, `pytest.mark.parametrize`.

## Steps

All in `src/complaints_ingest/clean.py`:

1. `normalise_text(value)`: collapse runs of whitespace to one space, strip, and return `None` for `None`, empty strings and placeholders (`none`, `null`, `n/a`, `nan`, any case). Non-strings become strings.
2. `parse_bool(value)`: `True` for yes/y/true/1, `False` for no/n/false/0 (any case, surrounding spaces ignored), real `bool`s unchanged, everything else `None`.
3. `parse_date(value)`: accept `date`/`datetime` objects, ISO dates, ISO timestamps with offset or `Z`, and `MM/DD/YY` or `MM/DD/YYYY`. Return a `date` or `None`.
4. Run `pytest tests/test_clean.py -k "normalise or bool or date"` until green.
5. Add two test cases of your own to each parametrised test, one of which you expect to be tricky (for example `"  YES "`, or `"2026-02-30"`).

## Check

```bash
pytest tests/test_clean.py -k "normalise or bool or date" -m exercise
make lint
```

## Evidence

The test output, and one sentence on a case where returning `None` is better than raising an error (and one where it is worse).

## Stretch

Make `parse_date` reject dates in the future and before 2011 (when the CFPB started collecting complaints). Where should that rule live: in the parser or in validation? Write your answer as a short ADR using `docs/adr/ADR-000-template.md`.
