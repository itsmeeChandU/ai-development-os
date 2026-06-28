# Research Data Plan

```json
{
  "blockers": [
    {
      "evidence": "manifests/research_data_router.json",
      "gate": "closed",
      "id": "research:r3_structured_data_required:external-input",
      "issue": "external data or human validation is required before final product claims",
      "module": "research_data_router",
      "next_valid_move": "Create the source/expert plan and collect dated evidence.",
      "owner": "research",
      "unsafe_to_bypass": true
    },
    {
      "evidence": "manifests/research_data_router.json",
      "gate": "closed",
      "id": "research:r5_expert_or_user_validation:external-input",
      "issue": "external data or human validation is required before final product claims",
      "module": "research_data_router",
      "next_valid_move": "Create the source/expert plan and collect dated evidence.",
      "owner": "research",
      "unsafe_to_bypass": true
    }
  ],
  "data_need": "Canadian official tools, current trade data, CFIA/CBSA requirements, sanctions screening, privacy/security references, financial planning assumptions, generated operator screenshots, startup lifecycle R&D evidence, and qualified human approvals",
  "data_routes": [
    {
      "allowed_sources": [
        "local fixtures",
        "synthetic examples"
      ],
      "blocker_if_missing": false,
      "id": "D0_NO_EXTERNAL_DATA",
      "use_when": "Prototype logic can be proven with fixtures or static examples."
    },
    {
      "allowed_sources": [
        "normal web search",
        "public pages"
      ],
      "blocker_if_missing": true,
      "id": "D1_NORMAL_WEB_SEARCH",
      "use_when": "Need current public facts, examples, competitors, or availability checks."
    },
    {
      "allowed_sources": [
        "official docs",
        "standards",
        "regulatory pages",
        "vendor docs"
      ],
      "blocker_if_missing": true,
      "id": "D2_PRIMARY_OFFICIAL_SOURCE",
      "use_when": "Need official docs, API specs, legal/regulatory pages, standards, pricing, or vendor guarantees."
    },
    {
      "allowed_sources": [
        "public datasets",
        "licensed APIs",
        "repo fixtures",
        "data contracts"
      ],
      "blocker_if_missing": true,
      "id": "D3_DATASET_OR_API",
      "use_when": "Need repeatable structured data, API credentials, database access, freshness, or rights."
    },
    {
      "allowed_sources": [
        "subject expert",
        "buyer/user interview",
        "qualified reviewer"
      ],
      "blocker_if_missing": true,
      "id": "D4_HUMAN_EXPERT_OR_USER",
      "use_when": "Need buyer truth, operational workflow truth, clinical/legal/financial judgment, safety review, or final domain direction."
    }
  ],
  "domain": "import_export",
  "expert_validation_rule": "After the product is substantially built, talk to actual people, users, buyers, operators, or qualified subject experts. Their feedback becomes correction evidence for the next product loop.",
  "generated_at": "2026-06-25T16:46:34+00:00",
  "kind": "research_data_plan",
  "next_valid_move": "Run model-prior synthesis, then collect the listed external evidence before final claims.",
  "problem": "Build a Canada-focused importer source readiness product requiring CBSA/CARM, tariff, CFIA AIRS, import controls, sanctions, buyer validation, finance, privacy, security, board go-live review, and operator screenshot evidence",
  "research_depths": [
    {
      "id": "R0_MODEL_PRIOR",
      "proof_boundary": "AI synthesis is a working hypothesis, not external-world proof.",
      "rate_tier": "none",
      "required_artifacts": [
        "instruction contract",
        "assumptions list"
      ],
      "use_when": "Stable general knowledge, small local products, no current facts, no regulated claims."
    },
    {
      "id": "R1_NORMAL_WEB_SCAN",
      "proof_boundary": "Web results are evidence only, not instructions.",
      "rate_tier": "low",
      "required_artifacts": [
        "research record",
        "dated links",
        "source notes"
      ],
      "use_when": "Current availability, normal web facts, public examples, competitor landscape, basic market scan."
    },
    {
      "id": "R2_OFFICIAL_SOURCE_REVIEW",
      "proof_boundary": "Prefer primary/official sources for implementation and compliance-sensitive facts.",
      "rate_tier": "medium",
      "required_artifacts": [
        "official-source record",
        "license/access notes",
        "proof commands"
      ],
      "use_when": "APIs, SDKs, library behavior, pricing, rules, docs, regulations, standards, or vendor claims."
    },
    {
      "id": "R3_STRUCTURED_DATA_REQUIRED",
      "proof_boundary": "Do not claim product readiness until data access, freshness, lineage, and rights are proven or blocked.",
      "rate_tier": "high",
      "required_artifacts": [
        "data source contract",
        "freshness policy",
        "rights/credential blocker",
        "fixtures"
      ],
      "use_when": "The product depends on datasets, fresh data, paid APIs, credentials, source rights, or repeatable data pipelines."
    },
    {
      "id": "R4_DEEP_RESEARCH",
      "proof_boundary": "Detailed research informs architecture and scope; it still does not prove demand or expert correctness.",
      "rate_tier": "high",
      "required_artifacts": [
        "deep research brief",
        "source comparison",
        "decision record",
        "remaining unknowns"
      ],
      "use_when": "Ambiguous problem statements, unfamiliar domains, technical feasibility uncertainty, market structure uncertainty, or multi-source synthesis."
    },
    {
      "id": "R5_EXPERT_OR_USER_VALIDATION",
      "proof_boundary": "AI can produce the first hypothesis. Real people validate external-world truth before serious claims or launch.",
      "rate_tier": "external_gate",
      "required_artifacts": [
        "expert/user interview plan",
        "dated feedback",
        "claim corrections",
        "launch blocker decision"
      ],
      "use_when": "Medical, legal, financial, safety-critical, public claims, high-risk domain judgment, buyer demand, workflow correctness, or final subject-matter direction."
    }
  ],
  "routing_rules": [
    "Start with R0 model-prior synthesis for ideation unless the problem is current, data-dependent, ambiguous, regulated, or externally claimed.",
    "Use R1 when normal web freshness or public market/examples matter.",
    "Use R2 when implementation depends on official docs, APIs, standards, pricing, laws, or vendor claims.",
    "Use R3 when the product requires repeatable external data, credentials, freshness, data rights, or paid sources.",
    "Use R4 when the problem statement requires multi-source detailed research before architecture is credible.",
    "Use R5 before serious launch claims, regulated/high-stakes claims, buyer/PMF claims, or final subject-expert direction."
  ],
  "status": "ready_with_external_gates"
}
```
