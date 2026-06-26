# External Harness Adoption Packet

## Harness

- id:
- name:
- source:
- license:
- inspected ref:
- decision:

## Target

- repo:
- product goal:
- integration mode: observe / project_local_optional / operator_global_optional

## Adopted Patterns

| pattern | local mapping | reason | proof boundary |
|---|---|---|---|
|  |  |  |  |

## Command Mapping

| external command or capability | AI Development OS command | allowed effects | blocked effects |
|---|---|---|---|
|  |  |  |  |

## Security And Install Gates

- source verified:
- license checked:
- operator approval required:
- config/security scan command:
- duplicate hook/plugin check:
- secrets/credentials boundary:

## Proof Commands

```bash
python3 scripts/workflow_manifest_check.py
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check
python3 scripts/ai_dev_os_check.py
python3 scripts/self_test_flow.py
```

## Blockers

| id | module | issue | owner | evidence | gate | next_valid_move | unsafe_to_bypass |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | closed |  | true |

## Handoff

- changed files:
- commands run:
- generated artifacts:
- blocked claims:
- unsafe or external gates:
- next valid move:
