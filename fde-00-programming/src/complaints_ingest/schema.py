"""Canonical complaint record and the field mappings for each CFPB source format.

The CFPB publishes the same complaints two ways: a search API (JSON, snake_case
fields) and a bulk CSV download (title-case headers). Both map onto one canonical
record so the rest of the pipeline never cares where a row came from.

Field names follow the public CFPB documentation as of October 2026. If CFPB renames
a field, the quality report flags it as schema drift instead of failing silently.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

CANONICAL_FIELDS: tuple[str, ...] = (
    "complaint_id",
    "date_received",
    "date_sent_to_company",
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "narrative",
    "company_public_response",
    "company",
    "state",
    "zip_code",
    "tags",
    "consumer_consent_provided",
    "submitted_via",
    "company_response",
    "timely",
    "consumer_disputed",
)

# CFPB search API (`_source` of each hit) -> canonical
API_FIELD_MAP: dict[str, str] = {
    "complaint_id": "complaint_id",
    "date_received": "date_received",
    "date_sent_to_company": "date_sent_to_company",
    "product": "product",
    "sub_product": "sub_product",
    "issue": "issue",
    "sub_issue": "sub_issue",
    "complaint_what_happened": "narrative",
    "company_public_response": "company_public_response",
    "company": "company",
    "state": "state",
    "zip_code": "zip_code",
    "tags": "tags",
    "consumer_consent_provided": "consumer_consent_provided",
    "submitted_via": "submitted_via",
    "company_response": "company_response",
    "timely": "timely",
    "consumer_disputed": "consumer_disputed",
}

# CFPB bulk CSV header -> canonical
CSV_FIELD_MAP: dict[str, str] = {
    "Complaint ID": "complaint_id",
    "Date received": "date_received",
    "Date sent to company": "date_sent_to_company",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Consumer consent provided?": "consumer_consent_provided",
    "Submitted via": "submitted_via",
    "Company response to consumer": "company_response",
    "Timely response?": "timely",
    "Consumer disputed?": "consumer_disputed",
}

# Fields every valid record must have.
REQUIRED_FIELDS: tuple[str, ...] = ("complaint_id", "date_received", "product", "company")


class Complaint(BaseModel):
    """One cleaned complaint, ready to store."""

    complaint_id: str = Field(min_length=1, max_length=32)
    date_received: date
    date_sent_to_company: date | None = None
    product: str
    sub_product: str | None = None
    issue: str | None = None
    sub_issue: str | None = None
    narrative: str | None = None
    company_public_response: str | None = None
    company: str
    state: str | None = Field(default=None, max_length=8)
    zip_code: str | None = Field(default=None, max_length=10)
    tags: str | None = None
    consumer_consent_provided: str | None = None
    submitted_via: str | None = None
    company_response: str | None = None
    timely: bool | None = None
    consumer_disputed: bool | None = None
