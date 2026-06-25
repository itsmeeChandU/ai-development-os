# Development Strategy Plan

```json
{
  "blockers": [
    {
      "evidence": "manifests/development_strategy_router.json",
      "gate": "closed",
      "id": "strategy:m5_cross_border_supply_chain:external-inputs",
      "issue": "development mode needs external inputs before final readiness",
      "module": "development_strategy_router",
      "next_valid_move": "Collect or block: customs/tariff evidence, country regulations, licensed broker or compliance expert when needed",
      "owner": "architect",
      "unsafe_to_bypass": true
    },
    {
      "evidence": "manifests/development_strategy_router.json",
      "gate": "closed",
      "id": "strategy:m1_data_api_product:external-inputs",
      "issue": "development mode needs external inputs before final readiness",
      "module": "development_strategy_router",
      "next_valid_move": "Collect or block: API terms, credentials, rate limits, source rights",
      "owner": "architect",
      "unsafe_to_bypass": true
    }
  ],
  "country": "US",
  "country_requirements_template": {
    "proof_boundary": "Country and import/export requirements must come from current official sources or qualified logistics/compliance experts before action.",
    "required_fields": [
      "country",
      "product_category",
      "import_rules_source",
      "export_rules_source",
      "tariff_or_hs_code_status",
      "certification_requirements",
      "restricted_party_or_sanctions_check",
      "logistics_constraints",
      "local_partner_or_broker_needed",
      "next_valid_move"
    ]
  },
  "external_contract_template": {
    "proof_boundary": "AI can draft a checklist; signed contracts and qualified review are external gates.",
    "required_fields": [
      "contract_type",
      "counterparty",
      "scope",
      "rights_granted",
      "data_or_ip_terms",
      "liability_boundary",
      "termination",
      "review_owner",
      "launch_gate"
    ]
  },
  "field": "cross-border supply chain",
  "field_playbooks": [
    {
      "default_mode": "M1_DATA_API_PRODUCT",
      "field": "data_product",
      "first_agents": [
        "research",
        "data",
        "surgeon",
        "reviewer"
      ],
      "first_artifacts": [
        "source contract",
        "fixture",
        "freshness policy"
      ]
    },
    {
      "default_mode": "M5_CROSS_BORDER_SUPPLY_CHAIN",
      "field": "import_export",
      "first_agents": [
        "research",
        "procurement",
        "compliance",
        "operations"
      ],
      "first_artifacts": [
        "country requirements matrix",
        "tariff/customs evidence",
        "logistics blockers"
      ]
    }
  ],
  "generated_at": "2026-06-25T15:18:43+00:00",
  "idea": "Build a blocked-safe importer/exporter source readiness copilot for product operators using fixture data, official-source placeholders, country requirement gaps, and explicit external-gate blockers.",
  "kind": "development_strategy_plan",
  "modes": [
    {
      "agent_mix": [
        "research",
        "procurement",
        "compliance",
        "operations",
        "qualified expert"
      ],
      "external_inputs": [
        "customs/tariff evidence",
        "country regulations",
        "licensed broker or compliance expert when needed"
      ],
      "id": "M5_CROSS_BORDER_SUPPLY_CHAIN",
      "proof_gates": [
        "country requirements matrix",
        "import/export blocker",
        "supplier/legal review",
        "logistics plan"
      ],
      "use_when": "Import/export, country-specific sourcing, tariffs, customs, certifications, logistics, or regional compliance."
    },
    {
      "agent_mix": [
        "research",
        "data",
        "architect",
        "surgeon",
        "reviewer"
      ],
      "external_inputs": [
        "API terms",
        "credentials",
        "rate limits",
        "source rights"
      ],
      "id": "M1_DATA_API_PRODUCT",
      "proof_gates": [
        "data source contract",
        "fixture",
        "freshness check",
        "integration test"
      ],
      "use_when": "Products that require APIs, data feeds, credentials, freshness, lineage, rights, or repeatable ingestion."
    }
  ],
  "next_valid_move": "Assign agents by mode, collect external inputs, and keep final claims blocked until evidence exists.",
  "status": "ready_with_external_gates"
}
```
