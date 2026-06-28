# Roadmap

System Review Graph is intentionally small today. The goal is to become a
practical bridge between code review, system design, audits, and AI-agent repo
orientation.

## Completed So Far

- Validation for duplicate IDs, unknown references, and unresolved explicit graph nodes.
- Real public repo examples for FastAPI, DuckDB, and OpenTelemetry Collector.
- HTML rendering for easier visual navigation.
- Optional Graphviz DOT export.
- JSON Schema for manifests.
- `doctor` command for report quality checks.
- `scan` command that creates starter manifests for mixed-language repositories.
- Starter language detection for C, C++, Java, C#, Python, JavaScript/TypeScript, Go, and Rust.
- README Mermaid visuals.
- Map-of-maps atlas support for huge repositories.
- `scan --atlas` with child subsystem manifests and optional report builds.
- MCP stdio server with scan/build/validate/doctor/load-atlas-context tools.
- Blueprint-depth reports with source evidence, operational flows, control points, and known gaps.
- Linux kernel blueprint with major source-backed operational paths.
- Generated coverage, evidence, gap, and action registers in Markdown and HTML reports.
- Merge-time atlas generation pattern for CI.
- Committed GitHub Actions CI workflow for lint, tests, package build, wheel
  smoke test, example report builds, and atlas generation.
- Committed PyPI Trusted Publishing workflow for automated release uploads.
- Linux kernel atlas stress-test example.
- README language-support matrix that distinguishes the language-neutral
  manifest model from automatic scanner detection.
- Regression coverage that proves the scanner detects the supported language,
  docs, tests, and config surfaces.

## Near Term

- Add more real public repo examples across languages and architectures.
- Refine atlas scoring beyond top-level directories into changed files, ownership, docs, and tests.
- Add automated source-evidence extraction for blueprint sections.
- Add register export formats for teams that want CSV/JSON audit ledgers.
- Detect OpenAPI, protobuf, SQL migrations, package metadata, docs, and tests in more detail.
- Add deeper language-specific scanners for Python, TypeScript, Go, Rust, Java, C#, C, and C++.
- Add an interactive review mode that asks missing-methodology questions.
- Add hosted documentation pages.

## Let It Breathe

The project is ready to pause after the current public baseline if maintainers
want real usage feedback before adding more machinery. The next useful signals
should come from:

- one or two outside users trying `scan` on their own repos,
- one maintainer reviewing whether the generated registers feel audit-friendly,
- one large-repo test beyond Linux,
- one private-system/sanitized-manifest test,
- one MCP-capable agent using `load-atlas-context` during a real review.

## Later

- Publish to PyPI.
- Add examples contributed by other maintainers.
