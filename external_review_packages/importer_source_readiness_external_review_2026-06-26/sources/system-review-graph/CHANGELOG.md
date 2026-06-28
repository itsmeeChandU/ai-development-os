# Changelog

All notable changes to System Review Graph are documented here.

## Unreleased

## 0.5.4 - 2026-06-08

Changed:

- Reduced the README badge strip to the highest-signal PyPI, CI, Python,
  license, MCP, system map, scanner, blueprint, and Linux atlas badges.
- Removed immature/noisy launch badges and the PyPI download-stats link from
  the README until download statistics are meaningful.
- Tightened PyPI keywords to a smaller set of stronger discovery tags.

## 0.5.3 - 2026-06-08

Added:

- GitHub Actions CI workflow for lint, tests, package builds, wheel smoke
  tests, example report builds, and atlas generation.
- PyPI Trusted Publishing workflow for automated release uploads.
- PyPI release guide with pending-publisher setup fields for
  `system-review-graph`.
- Live PyPI, PyPI downloads, and CI badges in the README.
- PyPI project and CI links in package metadata.
- Extra PyPI keywords for agent tooling, MCP, repo maps, architecture graphs,
  monorepos, software audit, and system architecture discovery.

Changed:

- Converted README logo, badge, docs, credit, and package links to absolute
  public URLs so they render correctly on PyPI.
- Made the PyPI release guide wheel smoke test version-independent.

## 0.5.2 - 2026-06-08

Added:

- Centered README badge/tag strip for project identity, language support,
  methodology, MCP, Linux atlas, quick start, and credit surfaces.

Changed:

- Updated creator, copyright, package author, notice, README attribution, and
  citation metadata to `Sai Chandra Madduri`.

## 0.5.1 - 2026-06-08

Added:

- README language-support matrix for automatic scanner detection versus
  language-neutral manifest/report support.
- Scanner regression coverage for Python, JavaScript/TypeScript, C/C++, Java,
  Kotlin, C#/.NET, Go, Rust, docs, tests, and config/build surfaces.
- Roadmap pause criteria for letting the project breathe after the public
  baseline.
- Credit and citation files: `AUTHORS.md`, `NOTICE.md`, and `CITATION.cff`.
- Project visual assets for README identity and GitHub social preview.

## 0.5.0 - 2026-06-08

Audit-register release.

Added:

- Generated report registers for coverage, evidence, gaps, and actions.
- Register sections in Markdown and HTML reports, including source links,
  artifact paths, schema contracts, blueprint evidence, known boundaries,
  review questions, and rebuild phases.
- Expansion-index entry for the register layer so reviewers can quickly find
  what is covered, proven, open, and actionable.
- Tests that require generated Markdown reports to include the register layer.
- Regenerated bundled examples, including the Linux kernel blueprint atlas,
  with the new audit-register sections.

## 0.4.0 - 2026-06-08

Blueprint-depth release.

Added:

- `blueprint` report depth.
- `blueprint_sections` manifest support for source-evidence-backed system flows.
- Blueprint Mermaid map and detailed Markdown source-evidence, operational-flow,
  control-point, review-question, and known-gap sections.
- Blueprint summary table in HTML reports.
- MCP atlas context now includes blueprint sections.
- Linux kernel root atlas upgraded to a blueprint report with 11 major
  source-backed flows: build/config, boot/init, process scheduler, syscall
  boundary, memory, VFS/block IO, networking, driver model/probe, LSM security,
  modules/BPF/tracing, and Rust integration.

## 0.3.0 - 2026-06-08

Large-repository atlas release.

Added:

- `child_maps` manifest support for map-of-maps reports.
- Map-of-maps Mermaid visualization and child-map tables in Markdown and HTML reports.
- Atlas links in Mermaid relationship graphs and Graphviz DOT output.
- `scan --atlas` for root atlases plus child subsystem manifests.
- `scan --atlas --build-reports` for root and child report generation.
- `system-review-graph-mcp` stdio MCP server.
- MCP tools for validate, doctor, build, scan, and atlas-context loading.
- CI template step for merge-time system atlas regeneration.
- Linux kernel atlas stress-test example.

## 0.2.0 - 2026-06-08

Roadmap completion release.

Added:

- README Mermaid visualizations.
- HTML report output.
- Graphviz DOT output.
- JSON Schema for manifests.
- Stronger validation for duplicate IDs and unresolved explicit graph edges.
- `doctor` command for manifest quality checks.
- `scan` command for mixed-language starter manifests.
- Starter language detection for C, C++, Java, C#, Python, JavaScript/TypeScript, Go, and Rust.
- Generated HTML and DOT outputs for all bundled examples.

## 0.1.0 - 2026-06-08

Initial public release.

Added:

- Manifest-first system review graph builder.
- Markdown and JSON report generation.
- Mermaid lifecycle, artifact/schema, gate, and relationship visualizations.
- `overview`, `standard`, and `deep` report depth levels.
- Per-system drill-downs for artifacts, gates, and workflow touchpoints.
- CLI commands: `build`, `validate`, `init-example`, and `list-examples`.
- Bundled starter manifests for local and PyPI installs.
- Public examples for FastAPI, DuckDB, OpenTelemetry Collector, and a fictional AI Ops system.
- Tests, packaging metadata, release docs, and open-source project docs.
