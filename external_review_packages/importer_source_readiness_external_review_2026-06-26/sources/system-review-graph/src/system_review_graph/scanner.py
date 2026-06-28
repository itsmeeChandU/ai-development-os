"""Language-neutral starter manifest scanner."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

LANGUAGE_RULES = [
    {
        "id": "python",
        "name": "Python Surface",
        "extensions": {".py"},
        "markers": {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"},
        "stack": ["Python"],
    },
    {
        "id": "javascript_typescript",
        "name": "JavaScript / TypeScript Surface",
        "extensions": {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
        "markers": {"package.json", "tsconfig.json", "vite.config.ts", "next.config.js"},
        "stack": ["JavaScript", "TypeScript"],
    },
    {
        "id": "c_cpp",
        "name": "C / C++ Surface",
        "extensions": {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh"},
        "markers": {"CMakeLists.txt", "Makefile", "configure.ac"},
        "stack": ["C", "C++"],
    },
    {
        "id": "java",
        "name": "Java Surface",
        "extensions": {".java", ".kt"},
        "markers": {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"},
        "stack": ["Java", "Kotlin"],
    },
    {
        "id": "csharp_dotnet",
        "name": "C# / .NET Surface",
        "extensions": {".cs", ".csproj", ".sln"},
        "markers": {"Directory.Build.props", "global.json"},
        "stack": ["C#", ".NET"],
    },
    {
        "id": "go",
        "name": "Go Surface",
        "extensions": {".go"},
        "markers": {"go.mod", "go.sum"},
        "stack": ["Go"],
    },
    {
        "id": "rust",
        "name": "Rust Surface",
        "extensions": {".rs"},
        "markers": {"Cargo.toml", "Cargo.lock"},
        "stack": ["Rust"],
    },
]

SKIP_DIRS = {
    ".git",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "target",
    "dist",
    "build",
    "htmlcov",
    "__pycache__",
}

PREFERRED_ATLAS_DIRS = [
    "arch",
    "block",
    "certs",
    "crypto",
    "Documentation",
    "drivers",
    "fs",
    "include",
    "init",
    "io_uring",
    "ipc",
    "kernel",
    "lib",
    "mm",
    "net",
    "rust",
    "samples",
    "scripts",
    "security",
    "sound",
    "tools",
    "usr",
    "virt",
]


def _iter_files(root: Path, limit: int) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
        if len(files) >= limit:
            break
    return files


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    if not cleaned:
        return "subsystem"
    if cleaned[0].isdigit():
        return f"s_{cleaned}"
    return cleaned


def _top_dirs(files: list[Path], root: Path, extensions: set[str]) -> list[str]:
    dirs: set[str] = set()
    for path in files:
        if path.suffix.lower() not in extensions:
            continue
        relative = path.relative_to(root)
        if len(relative.parts) > 1:
            dirs.add(relative.parts[0] + "/")
        else:
            dirs.add(_relative(path, root))
    return sorted(dirs)[:12]


def _marker_hits(files: list[Path], root: Path, markers: set[str]) -> list[str]:
    hits = []
    for path in files:
        if path.name in markers:
            hits.append(_relative(path, root))
    return sorted(hits)[:20]


def _directory_exists(root: Path, names: set[str]) -> list[str]:
    return sorted(
        f"{path.name}/"
        for path in root.iterdir()
        if path.is_dir() and path.name.lower() in names
    )


def _detect_stacks(files: list[Path], root: Path) -> list[str]:
    stacks: list[str] = []
    for rule in LANGUAGE_RULES:
        if _top_dirs(files, root, rule["extensions"]) or _marker_hits(files, root, rule["markers"]):
            stacks.extend(str(item) for item in rule["stack"])
    seen: set[str] = set()
    ordered: list[str] = []
    for stack in stacks:
        if stack not in seen:
            seen.add(stack)
            ordered.append(stack)
    return ordered


def _count_files(root: Path, limit: int = 2000) -> int:
    count = 0
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            count += 1
        if count >= limit:
            break
    return count


def _atlas_candidates(root: Path, max_subsystems: int) -> list[Path]:
    preferred_rank = {name.lower(): index for index, name in enumerate(PREFERRED_ATLAS_DIRS)}
    candidates: list[tuple[int, int, str, Path]] = []
    for path in root.iterdir():
        if not path.is_dir() or path.name in SKIP_DIRS or path.name.startswith("."):
            continue
        file_count = _count_files(path)
        if file_count == 0:
            continue
        rank = preferred_rank.get(path.name.lower(), len(preferred_rank) + 1)
        candidates.append((rank, -file_count, path.name.lower(), path))
    candidates.sort()
    return [path for _, _, _, path in candidates[:max_subsystems]]


def scan_repository(root: Path, title: str | None = None, file_limit: int = 6000) -> dict[str, Any]:
    """Create a starter manifest from a repository directory."""

    root = root.resolve()
    files = _iter_files(root, file_limit)
    systems: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    workflows: list[dict[str, Any]] = []
    detected_language_ids: list[str] = []

    for rule in LANGUAGE_RULES:
        code_surfaces = _top_dirs(files, root, rule["extensions"])
        marker_hits = _marker_hits(files, root, rule["markers"])
        if not code_surfaces and not marker_hits:
            continue
        language_label = rule["name"].replace(" Surface", "")
        detected_language_ids.append(rule["id"])
        artifact_id = f"{rule['id']}_source_surface"
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "name": rule["name"],
                "kind": "source_surface",
                "path": ", ".join(code_surfaces or marker_hits),
                "owner": "unknown",
                "schema": "SourceSurface",
                "purpose": f"Detected {language_label} source and build surfaces.",
                "redaction": "safe_to_share",
            }
        )
        systems.append(
            {
                "system_id": rule["id"],
                "name": rule["name"],
                "purpose": f"Detected {language_label} code and build surfaces for review.",
                "owner": "unknown",
                "language_stack": rule["stack"],
                "architecture_style": "detected source surface",
                "lifecycle": "source files -> build/test docs -> inferred system role",
                "code_surfaces": code_surfaces,
                "artifacts": [artifact_id],
                "decision_gates": ["manual_review_gate"],
                "truth_boundary": "Detected from repository files; runtime behavior is not proven.",
                "ideal_target": (
                    "Replace this starter node with exact subsystem ownership "
                    "and workflows."
                ),
            }
        )

    docs_dirs = _directory_exists(root, {"docs", "doc", "documentation"})
    test_dirs = _directory_exists(root, {"test", "tests", "spec", "specs", "__tests__"})
    config_files = [
        _relative(path, root)
        for path in files
        if path.name
        in {
            "Dockerfile",
            "docker-compose.yml",
            "compose.yml",
            "Makefile",
            "CMakeLists.txt",
            "pyproject.toml",
            "package.json",
            "pom.xml",
            "go.mod",
            "Cargo.toml",
        }
    ][:30]

    if docs_dirs:
        artifacts.append(
            {
                "artifact_id": "documentation_surface",
                "name": "Documentation Surface",
                "kind": "docs",
                "path": ", ".join(docs_dirs),
                "owner": "unknown",
                "schema": "DocumentationSurface",
                "purpose": "Detected documentation directories that may explain system behavior.",
                "redaction": "safe_to_share",
            }
        )
    if test_dirs:
        artifacts.append(
            {
                "artifact_id": "test_surface",
                "name": "Test Surface",
                "kind": "tests",
                "path": ", ".join(test_dirs),
                "owner": "unknown",
                "schema": "TestSurface",
                "purpose": "Detected test directories that may prove behavior.",
                "redaction": "safe_to_share",
            }
        )
    if config_files:
        artifacts.append(
            {
                "artifact_id": "config_build_surface",
                "name": "Config And Build Surface",
                "kind": "config",
                "path": ", ".join(config_files),
                "owner": "unknown",
                "schema": "ConfigSurface",
                "purpose": "Detected build, package, container, or configuration files.",
                "redaction": "safe_to_share",
            }
        )

    if detected_language_ids:
        first_step = "inspect_source_surfaces"
        workflows.append(
            {
                "step_id": first_step,
                "name": "Inspect Source Surfaces",
                "actor": "Reviewer",
                "consumes": [
                    f"{language_id}_source_surface"
                    for language_id in detected_language_ids
                ],
                "produces": ["candidate_system_map"],
                "gates": ["manual_review_gate"],
                "next_steps": ["refine_workflows"],
                "purpose": "Turn detected code/build surfaces into a human-reviewed system map.",
            }
        )
        workflows.append(
            {
                "step_id": "refine_workflows",
                "name": "Refine Workflows",
                "actor": "Maintainer",
                "consumes": ["candidate_system_map"],
                "produces": ["system_review_manifest"],
                "gates": ["manual_review_gate"],
                "next_steps": [],
                "purpose": "Replace inferred surfaces with exact workflows, gates, and boundaries.",
            }
        )

    repo_name = root.name
    return {
        "title": title or f"{repo_name} Starter System Review Graph",
        "one_line": (
            "Starter manifest generated from repository language, build, docs, "
            "and test surfaces."
        ),
        "scope": f"Generated starter manifest for {root}.",
        "bigger_picture": (
            "This is an inferred starter map. It detects language and project surfaces, "
            "then asks maintainers or agents to refine actual workflows, gates, and boundaries."
        ),
        "current_truth": {
            "scanner": "language_neutral_starter",
            "file_limit": file_limit,
            "files_seen": len(files),
            "detected_languages": detected_language_ids,
            "runtime_behavior_proven": False,
        },
        "source_links": [],
        "schemas": [
            {
                "name": "SourceSurface",
                "kind": "detected_contract",
                "required_fields": ["path", "language_stack", "build_markers"],
                "purpose": "A detected source/build surface that needs human review.",
                "privacy_notes": "Only paths and coarse metadata are included.",
            },
            {
                "name": "DocumentationSurface",
                "kind": "detected_contract",
                "required_fields": ["path", "purpose"],
                "purpose": "Detected docs that may explain system behavior.",
            },
            {
                "name": "TestSurface",
                "kind": "detected_contract",
                "required_fields": ["path", "purpose"],
                "purpose": "Detected tests that may prove behavior.",
            },
            {
                "name": "ConfigSurface",
                "kind": "detected_contract",
                "required_fields": ["path", "purpose"],
                "purpose": "Detected build/config/deployment surface.",
            },
        ],
        "artifacts": artifacts,
        "decision_gates": [
            {
                "gate_id": "manual_review_gate",
                "name": "Manual Review Gate",
                "inputs": ["detected surfaces", "maintainer knowledge"],
                "outputs": ["accepted", "needs_refinement", "rejected"],
                "human_gate": True,
                "risk_boundary": (
                    "Scanner output is a starting point, not proof of runtime behavior."
                ),
                "rules": [
                    {"if": "surface matches real subsystem", "then": "accepted"},
                    {"if": "surface is too broad or ambiguous", "then": "needs_refinement"},
                    {"if": "surface is generated/noise", "then": "rejected"},
                ],
            }
        ],
        "systems": systems,
        "workflows": workflows,
        "edges": [],
        "architecture_patterns": [
            {
                "name": "Mixed-language repository",
                "works_for": (
                    "C, C++, Java, C#, Python, JavaScript/TypeScript, Go, "
                    "Rust, and mixed repos"
                ),
                "mapping": (
                    "Detect language/build/test/doc surfaces first, then refine "
                    "into exact systems and workflows."
                ),
                "redaction": "Publish paths and contracts, not private records or secrets.",
            }
        ],
        "walkthroughs": [
            {
                "name": "From scan to real system review",
                "story": (
                    "Run scan, inspect detected surfaces, replace broad language "
                    "nodes with real subsystems, then add workflows and gates."
                ),
                "example": {
                    "scan": "system-review-graph scan --repo . --out system_review_manifest.json",
                    "refine": ["systems", "artifacts", "workflows", "decision_gates"],
                },
            }
        ],
        "review_questions": [
            "Which detected language surfaces are real subsystems?",
            "Which directories are generated or vendor noise?",
            "Where are APIs, CLIs, configs, migrations, docs, and tests?",
            "Which workflows move data or decisions end to end?",
            "Which gates block unsafe or unreviewed behavior?",
        ],
        "rebuild_recipe": [
            {
                "phase": "scan",
                "goal": "Generate a starter manifest from repository surfaces.",
                "commands": [
                    "system-review-graph scan --repo . --out system_review_manifest.json"
                ],
            }
        ],
        "known_boundaries": [
            "Scanner output is inferred from file paths and markers.",
            "Runtime behavior, production deployment, and ownership are not proven.",
            (
                "Maintainers or agents should refine workflows, gates, and "
                "boundaries before audit use."
            ),
        ],
    }


def scan_repository_atlas(
    root: Path,
    title: str | None = None,
    file_limit: int = 6000,
    max_subsystems: int = 24,
) -> dict[str, Any]:
    """Create a root atlas manifest and child subsystem manifests for a large repository."""

    root = root.resolve()
    repo_name = root.name
    root_files = _iter_files(root, file_limit)
    candidates = _atlas_candidates(root, max_subsystems)
    child_maps: list[dict[str, Any]] = []
    systems: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    children: list[dict[str, Any]] = []

    for candidate in candidates:
        subsystem_id = _safe_id(candidate.name)
        child_manifest_path = f"subsystems/{subsystem_id}/system_review_manifest.json"
        child_report_path = f"../subsystems/{subsystem_id}/reports/system_review_graph.md"
        child_manifest = scan_repository(
            candidate,
            title=f"{repo_name} / {candidate.name} Subsystem System Review Graph",
            file_limit=file_limit,
        )
        child_manifest["scope"] = (
            f"Generated starter subsystem map for {candidate.relative_to(root)} in {root}."
        )
        child_manifest["current_truth"]["atlas_parent"] = repo_name
        child_manifest["current_truth"]["subsystem_path"] = _relative(candidate, root)
        stacks = []
        for child_system in child_manifest["systems"]:
            stacks.extend(child_system.get("language_stack") or [])
        stacks = sorted({str(stack) for stack in stacks})
        child_maps.append(
            {
                "map_id": subsystem_id,
                "name": f"{candidate.name}/ subsystem map",
                "path": child_manifest_path,
                "report_path": child_report_path,
                "purpose": "Drill-down map generated from this top-level repository directory.",
                "scope": _relative(candidate, root),
                "owner": "unknown",
                "systems": [str(system.get("system_id")) for system in child_manifest["systems"]],
                "status": "inferred_from_source_tree",
                "review_hint": (
                    "Open this child manifest/report to refine exact workflows, ownership, "
                    "runtime behavior, and gates."
                ),
            }
        )
        artifact_id = f"{subsystem_id}_child_map"
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "name": f"{candidate.name}/ Child System Map",
                "kind": "child_system_map",
                "path": child_manifest_path,
                "owner": "unknown",
                "schema": "SubsystemMap",
                "purpose": "Machine-readable child map for a top-level subsystem boundary.",
                "redaction": "safe_to_share",
            }
        )
        systems.append(
            {
                "system_id": subsystem_id,
                "name": f"{candidate.name}/",
                "purpose": (
                    "Top-level repository subsystem inferred from directory boundary. "
                    "Use the child map for language surfaces and first review targets."
                ),
                "owner": "unknown",
                "language_stack": stacks,
                "architecture_style": "top-level source-tree subsystem",
                "lifecycle": "open child map -> inspect source surfaces -> refine real workflows",
                "code_surfaces": [_relative(candidate, root)],
                "artifacts": [artifact_id],
                "decision_gates": ["subsystem_review_gate"],
                "truth_boundary": (
                    "Directory boundary is source-grounded; runtime responsibility and exact "
                    "behavior require maintainer or deeper agent review."
                ),
                "ideal_target": (
                    "Replace inferred directory node with exact subsystem workflows, APIs, "
                    "contracts, risks, and tests."
                ),
                "example": {
                    "child_map": child_manifest_path,
                    "detected_child_systems": child_maps[-1]["systems"],
                },
            }
        )
        children.append(
            {
                "subsystem_id": subsystem_id,
                "manifest_path": child_manifest_path,
                "manifest": child_manifest,
            }
        )

    root_manifest = {
        "title": title or f"{repo_name} System Review Atlas",
        "one_line": (
            "Map-of-maps generated for a large repository: root atlas links to "
            "subsystem manifests."
        ),
        "scope": f"Generated atlas for {root}.",
        "bigger_picture": (
            "Large repositories should not be reviewed as one flat graph. The atlas keeps "
            "the root map small, links child subsystem maps, and gives reviewers or agents "
            "a navigable context bundle they can expand without losing the whole-system view."
        ),
        "current_truth": {
            "scanner": "language_neutral_atlas",
            "file_limit_per_map": file_limit,
            "root_files_seen": len(root_files),
            "subsystem_count": len(candidates),
            "max_subsystems": max_subsystems,
            "runtime_behavior_proven": False,
            "map_strategy": "root atlas plus linked child subsystem manifests",
        },
        "source_links": [],
        "child_maps": child_maps,
        "schemas": [
            {
                "name": "SubsystemMap",
                "kind": "atlas_contract",
                "required_fields": ["map_id", "path", "scope", "systems", "status"],
                "purpose": (
                    "A child system review map that a root atlas can link, upload, and "
                    "hand to reviewers or agents."
                ),
                "example": {
                    "map_id": "drivers",
                    "path": "subsystems/drivers/system_review_manifest.json",
                    "report_path": "../subsystems/drivers/reports/system_review_graph.md",
                    "scope": "drivers/",
                    "systems": ["c_cpp"],
                    "status": "inferred_from_source_tree",
                },
                "privacy_notes": "Only path-level source metadata is included by default.",
            }
        ],
        "artifacts": artifacts,
        "decision_gates": [
            {
                "gate_id": "subsystem_review_gate",
                "name": "Subsystem Review Gate",
                "inputs": ["root directory boundary", "child subsystem map", "maintainer review"],
                "outputs": ["accepted", "needs_deeper_map", "split_or_merge", "rejected"],
                "human_gate": True,
                "risk_boundary": (
                    "Atlas output is a navigation structure and source-surface hypothesis, "
                    "not proof of runtime behavior."
                ),
                "rules": [
                    {"if": "directory boundary matches real subsystem", "then": "accepted"},
                    {
                        "if": "directory contains multiple unrelated systems",
                        "then": "split_or_merge",
                    },
                    {"if": "child map lacks workflows or gates", "then": "needs_deeper_map"},
                    {"if": "directory is generated/vendor noise", "then": "rejected"},
                ],
            }
        ],
        "systems": systems,
        "workflows": [
            {
                "step_id": "scan_root_boundaries",
                "name": "Scan Root Boundaries",
                "actor": "System Review Graph scanner",
                "consumes": [],
                "produces": [artifact["artifact_id"] for artifact in artifacts],
                "gates": ["subsystem_review_gate"],
                "next_steps": ["open_child_maps"],
                "purpose": "Detect top-level subsystem boundaries and generate child maps.",
            },
            {
                "step_id": "open_child_maps",
                "name": "Open Child Maps",
                "actor": "Reviewer or agent",
                "consumes": [artifact["artifact_id"] for artifact in artifacts],
                "produces": ["subsystem_review_context"],
                "gates": ["subsystem_review_gate"],
                "next_steps": ["refine_atlas"],
                "purpose": (
                    "Load child manifests to understand each subsystem without losing the "
                    "root map."
                ),
            },
            {
                "step_id": "refine_atlas",
                "name": "Refine Atlas",
                "actor": "Maintainer",
                "consumes": ["subsystem_review_context"],
                "produces": ["accepted_system_review_atlas"],
                "gates": ["subsystem_review_gate"],
                "next_steps": ["regenerate_on_merge"],
                "purpose": "Replace inferred boundaries with reviewed workflows, APIs, and gates.",
            },
            {
                "step_id": "regenerate_on_merge",
                "name": "Regenerate On Merge",
                "actor": "CI",
                "consumes": ["accepted_system_review_atlas"],
                "produces": ["fresh_review_reports", "drift_findings"],
                "gates": ["subsystem_review_gate"],
                "next_steps": [],
                "purpose": (
                    "Keep the atlas current after merges so reviewers can see system drift, "
                    "new features, and changed review targets."
                ),
            },
        ],
        "edges": [],
        "architecture_patterns": [
            {
                "name": "Map-of-maps for huge repositories",
                "works_for": "Monorepos, kernels, platform repos, multi-language systems",
                "mapping": (
                    "Create a small root atlas, link child maps by subsystem boundary, "
                    "and regenerate reports in CI."
                ),
                "redaction": "Publish path-level maps, sanitized contracts, and review hints.",
            },
            {
                "name": "Merge-time system drift check",
                "works_for": "Projects that want architecture reports on every merge",
                "mapping": (
                    "Run atlas scan/build in CI, diff the generated report, and route changed "
                    "subsystem maps to reviewers."
                ),
                "redaction": (
                    "Keep private data and secrets out of manifests; expose interfaces only."
                ),
            },
        ],
        "walkthroughs": [
            {
                "name": "Review a huge repository without flattening it",
                "story": (
                    "Start at the atlas report, choose the subsystem that changed or looks risky, "
                    "open the child manifest, then refine that child into exact workflows "
                    "and gates."
                ),
                "example": {
                    "scan": (
                        "system-review-graph scan --repo /path/to/repo --atlas "
                        "--out atlas --max-subsystems 24"
                    ),
                    "ci": (
                        "system-review-graph scan --repo . --atlas --out reports/system-review "
                        "--build-reports"
                    ),
                    "review": [
                        "Read reports/system-review/reports/system_review_graph.md",
                        "Open changed child manifests under reports/system-review/subsystems/",
                        "Promote accepted inferred maps into reviewed manifests",
                    ],
                },
            }
        ],
        "review_questions": [
            "Which child maps changed since the last merge?",
            "Which subsystem boundary is too broad and needs splitting?",
            "Which subsystem lacks workflow, gate, schema, or test evidence?",
            "Can reviewers reproduce the map from the declared rebuild recipe?",
            "Where does the atlas overclaim beyond source-surface evidence?",
        ],
        "rebuild_recipe": [
            {
                "phase": "atlas-scan",
                "goal": "Generate root and child subsystem maps.",
                "commands": [
                    (
                        "system-review-graph scan --repo . --atlas --out "
                        "reports/system-review --max-subsystems 24"
                    )
                ],
            },
            {
                "phase": "merge-regeneration",
                "goal": "Regenerate reports in CI after a merge or major milestone.",
                "commands": [
                    (
                        "system-review-graph scan --repo . --atlas --out "
                        "reports/system-review --build-reports"
                    )
                ],
            },
        ],
        "known_boundaries": [
            "Atlas boundaries are inferred from source-tree directories and markers.",
            "A child map gives review context; it does not prove runtime behavior by itself.",
            "Very large systems still need maintainers or deeper agents to refine real workflows.",
            "CI regeneration can detect drift, but deciding meaning still needs review gates.",
        ],
    }
    return {"root": root_manifest, "children": children}
