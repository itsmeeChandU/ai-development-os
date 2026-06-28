# Reviewer Instructions

## Review Goal

Assess whether the product and process are strong enough to continue toward a
controlled private beta, and identify what must change before any external
customer, legal, compliance, financial, supplier, or launch claims.

## Review Order

1. Read `START_HERE.md`.
2. Read `review_docs/CLAIM_BOUNDARIES_AND_OPEN_GATES.md`.
3. Read the brief for your review role.
4. Inspect the source under `sources/importer-source-readiness-copilot/`.
5. Inspect generated evidence under `evidence/`.
6. Run the product locally if you are doing technical or product review.
7. Fill in `review_docs/REVIEW_RESPONSE_TEMPLATE.md`.

## Running The Product

Requirements:

- Python 3.11 or newer.
- No credentials are required.
- No paid APIs or live external actions are used.

Commands:

```bash
cd sources/importer-source-readiness-copilot
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
python3 scripts/serve_operator_app.py
```

Open:

```text
http://127.0.0.1:8765/
```

Useful API routes:

- `/api`
- `/api/operator-workflow`
- `/api/readiness`
- `/api/external-gates`
- `/api/continuation`
- `/api/board-go-live`

## Review Standards

Use evidence, not general impressions.

For every finding, include:

- severity
- file or artifact path
- why it matters
- recommended fix
- whether it blocks private beta, public launch, or only future scale

## Do Not Assume

Do not assume:

- buyer validation exists
- a qualified Canadian customs/compliance review has happened
- legal/privacy review has happened
- finance approval has happened
- contracts or data rights are signed
- production deployment has been approved
- public launch is allowed

Those are intentionally open gates.
