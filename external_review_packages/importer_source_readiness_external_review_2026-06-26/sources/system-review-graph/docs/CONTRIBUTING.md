# Contributing

Thank you for helping improve System Review Graph.

Good contributions include:

- new manifest examples,
- renderers,
- schema validators,
- architecture patterns,
- CI integrations,
- language-specific scanners that generate starter manifests,
- docs and walkthroughs.

## Local Setup

```bash
python -m pip install -e .
python -m pytest
python -m ruff check .
```

## Contribution Rules

- Do not commit private production data.
- Use fictional or sanitized examples.
- Keep the manifest format language-neutral.
- Prefer simple JSON over framework-specific assumptions.
- Make risk boundaries explicit.

## Design Goal

The report should help a new person understand what a system does without needing tribal knowledge.

