"""Seeded synthetic complaints in the CFPB API shape.

Used for offline labs, tests and repeatable throughput benchmarks. Synthetic data is
never reported as real CFPB statistics.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

PRODUCTS = {
    "Credit reporting or other personal consumer reports": [
        "Incorrect information on your report", "Improper use of your report",
        "Problem with a company's investigation into an existing problem"],
    "Debt collection": ["Attempts to collect debt not owed", "Written notification about debt",
                        "Communication tactics"],
    "Checking or savings account": ["Managing an account", "Opening an account",
                                    "Closing an account"],
    "Credit card": ["Problem with a purchase shown on your statement", "Fees or interest",
                    "Getting a credit card"],
    "Mortgage": ["Trouble during payment process", "Struggling to pay mortgage",
                 "Applying for a mortgage or refinancing an existing mortgage"],
    "Money transfer, virtual currency, or money service": ["Fraud or scam",
                                                           "Other transaction problem"],
    "Student loan": ["Dealing with your lender or servicer", "Struggling to repay your loan"],
    "Vehicle loan or lease": ["Managing the loan or lease", "Struggling to pay your loan"],
}
COMPANIES = ["Alpha Bank", "Beacon Financial", "Cedar Credit Union", "Delta Lending",
             "Equinox Card Services", "Fjord Mortgage", "Granite Collections", "Harbor Payments"]
STATES = ["CA", "TX", "FL", "NY", "GA", "IL", "PA", "OH", "NC", "NJ"]
CHANNELS = ["Web", "Referral", "Phone", "Postal mail", "Email"]
RESPONSES = ["Closed with explanation", "Closed with non-monetary relief",
             "Closed with monetary relief", "In progress"]
NARRATIVES = [
    "I disputed an item on my report on XX/XX/XXXX and the company has not corrected it.",
    "The collector keeps calling me about a debt I do not owe. Call me back at 555-201-3344.",
    "A charge of {$200.00} appeared on my card that I did not make. Email me at jane@example.com.",
    "My account was closed without notice and my funds are still held.",
    "I sent the payment on time but the servicer applied it late and charged a fee.",
    "",
]


def make_complaints(n: int, *, seed: int = 42, start: date = date(2026, 1, 1),
                    days: int = 270) -> list[dict]:
    """Return n raw complaints shaped like CFPB API `_source` records."""
    rng = random.Random(seed)  # noqa: S311 - reproducible test data, not security
    rows = []
    for i in range(n):
        product = rng.choice(list(PRODUCTS))
        received = start + timedelta(days=rng.randrange(days))
        narrative = rng.choice(NARRATIVES)
        rows.append({
            "complaint_id": str(9_000_000 + i),
            "date_received": f"{received.isoformat()}T12:00:00-05:00",
            "date_sent_to_company": (received + timedelta(days=rng.randrange(3))).isoformat(),
            "product": product,
            "sub_product": None,
            "issue": rng.choice(PRODUCTS[product]),
            "sub_issue": None,
            "complaint_what_happened": narrative,
            "company_public_response": None,
            "company": rng.choice(COMPANIES),
            "state": rng.choice(STATES),
            "zip_code": f"{rng.randrange(10000, 99999)}",
            "tags": rng.choice([None, None, "Older American", "Servicemember"]),
            "consumer_consent_provided": "Consent provided" if narrative else "N/A",
            "submitted_via": rng.choice(CHANNELS),
            "company_response": rng.choice(RESPONSES),
            "timely": rng.choice(["Yes"] * 9 + ["No"]),
            "consumer_disputed": "N/A",
        })
    return rows
