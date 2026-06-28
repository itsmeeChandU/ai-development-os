# Architecture Patterns

System Review Graph is intentionally language- and architecture-neutral.

## Open-Source Library

Map:

- package modules -> systems,
- public APIs -> artifacts,
- type contracts -> schemas,
- validation and CI -> decision gates,
- examples -> walkthroughs.

## Mixed-Language Repository

Map:

- C/C++ build surfaces such as `CMakeLists.txt`, `Makefile`, `src/`, `include/` -> systems/artifacts,
- Java build surfaces such as `pom.xml`, `build.gradle`, `src/main/java` -> systems/artifacts,
- C#/.NET surfaces such as `.sln`, `.csproj`, `Directory.Build.props` -> systems/artifacts,
- Python surfaces such as `pyproject.toml`, `src/`, package modules -> systems/artifacts,
- JavaScript/TypeScript surfaces such as `package.json`, `tsconfig.json`, app directories -> systems/artifacts,
- Go surfaces such as `go.mod`, packages, commands -> systems/artifacts,
- Rust surfaces such as `Cargo.toml`, crates, modules -> systems/artifacts,
- docs/tests/configs -> evidence artifacts,
- maintainer review -> decision gate.

The built-in `scan` command detects broad language/build/test/doc surfaces and
creates a starter manifest. It does not claim to prove runtime behavior.

## Huge Repository Or Monorepo

Map:

- root repository -> atlas,
- top-level packages/directories -> child maps,
- child maps -> local systems, artifacts, schemas, gates, and review questions,
- changed child maps -> pull-request review focus,
- CI regeneration -> architecture drift signal.

Use:

```bash
system-review-graph scan --repo . --atlas --out reports/system-review-atlas --build-reports
```

This is useful for kernels, database engines, browser engines, platform
monorepos, language runtimes, and company-internal source trees where one flat
graph would hide the important context.

For blueprint-depth reports, add source-backed flow sections:

- entry point -> source evidence,
- operational flow -> step table,
- control points -> gates and failure modes,
- known gaps -> what the report still does not prove.

## Web Application

Map:

- frontend, backend, database, background workers -> systems,
- routes and pages -> artifacts,
- request/response objects -> schemas,
- auth and permission checks -> decision gates,
- user journey -> workflows.

## Microservices

Map:

- each service -> system,
- APIs, queues, topics, tables -> artifacts,
- OpenAPI/AsyncAPI/protobuf -> schemas,
- retry/auth/rate-limit/saga checks -> decision gates,
- request path or event path -> workflows.

## Data Platform

Map:

- source loaders, warehouse, marts, reports, quality checks -> systems,
- tables, views, dashboards, extracts -> artifacts,
- table contracts -> schemas,
- freshness/quality/rights checks -> decision gates,
- load-transform-report path -> workflows.

## ML Or AI System

Map:

- data ingest, feature store, trainer, evaluator, serving, monitor -> systems,
- datasets, model cards, eval reports, endpoints -> artifacts,
- feature/model/prediction contracts -> schemas,
- eval thresholds and human review -> decision gates,
- training and inference paths -> workflows.

## Agent System

Map:

- planner, researcher, executor, reviewer, memory, UI -> systems,
- task queues, tool calls, memory logs, reports -> artifacts,
- task/action/outcome contracts -> schemas,
- human gate and risk policies -> decision gates,
- task lifecycle -> workflows.

## Private Enterprise System

Map:

- do not expose raw database or secrets,
- expose sanitized logical contracts,
- expose decision gates,
- expose redaction policy,
- expose counts and example fake rows,
- expose service boundaries.

The reviewer does not need production data to understand the operating system.

## Embedded Or Hardware-Adjacent Systems

Map:

- firmware, host service, telemetry pipeline, safety monitor -> systems,
- message formats and logs -> artifacts,
- hardware interface contracts -> schemas,
- safety thresholds -> decision gates,
- boot/calibration/fault lifecycle -> workflows.
