# ADR-007: Mask PII in narratives even though the source redacts them

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Sunday Ayandele (owner)

## Context

CFPB publishes narratives only with consumer consent and scrubs personal information (dates and names become `XX/XX/XXXX`, `XXXX`). A bank adopting this pipeline would point it at its own complaint data, which is not scrubbed. Later phases send stored text to LLMs.

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| A. Trust the source | No extra work | Unsafe the moment the source changes |
| B. Regex masking of emails, SSNs, card, phone and account numbers at ingest | Cheap, deterministic, testable, counted per run | Misses names and addresses; some false positives on long numbers |
| C. NER-based PII detection (e.g. Presidio) | Catches names, addresses | Heavier dependency, slower, needs evaluation |

## Decision

Option B in this phase, with counts per run (`pii_values_masked`). Masks are typed placeholders (`[EMAIL]`, `[CARD]` ...) so downstream models still see that a value was there.

## Consequences

- Names and street addresses are not masked; documented in the threat model. `fde-03` adds a PII-leak red-team test and evaluates an NER layer.
- Any number of 8–12 digits is treated as an account number; monetary amounts with separators (`{$200.00}`) are not affected (tested).
