# Toolchain

This is the default open-source stack. Do not install everything blindly. Pick
from this registry based on the task and record additions in
`manifests/tool_registry.yaml`.

## Coding Agents And Agent Runtimes

- OpenAI Codex CLI: https://github.com/openai/codex
- OpenAI Agents SDK Python: https://github.com/openai/openai-agents-python
- OpenAI Agents SDK JS/TS: https://github.com/openai/openai-agents-js
- OpenHands: https://github.com/OpenHands/openhands
- Aider: https://github.com/Aider-AI/aider
- SWE-agent: https://github.com/SWE-agent/SWE-agent
- Continue: https://github.com/continuedev/continue
- Cline: https://github.com/cline/cline

## Multi-Agent Frameworks

- LangGraph: https://github.com/langchain-ai/langgraph
- CrewAI: https://github.com/crewAIInc/crewAI
- AutoGen: https://github.com/microsoft/autogen
- smolagents: https://github.com/huggingface/smolagents
- PydanticAI: https://github.com/pydantic/pydantic-ai

## Tooling And Context

- Model Context Protocol: https://github.com/modelcontextprotocol
- MCP reference/community servers: https://github.com/modelcontextprotocol/servers
- GitHub MCP server: https://github.com/github/github-mcp-server
- Context7 MCP: https://github.com/upstash/context7
- Playwright: https://github.com/microsoft/playwright
- Browser Use: https://github.com/browser-use/browser-use

## Engineering Hygiene

- uv: https://github.com/astral-sh/uv
- Ruff: https://github.com/astral-sh/ruff
- ruff-pre-commit: https://github.com/astral-sh/ruff-pre-commit
- pre-commit: https://github.com/pre-commit/pre-commit
- just: https://github.com/casey/just
- mise: https://github.com/jdx/mise
- Docker: https://github.com/docker
- Testcontainers: https://github.com/testcontainers

## Observability And Evaluation

- OpenTelemetry: https://github.com/open-telemetry
- Langfuse: https://github.com/langfuse/langfuse
- Phoenix: https://github.com/Arize-ai/phoenix
- Promptfoo: https://github.com/promptfoo/promptfoo
- Inspect AI: https://github.com/UKGovernmentBEIS/inspect_ai

## Local Coordination

- Ruflo: use when available as a local MCP coordination/memory layer.
- Git worktrees: use for isolated branches and parallel lanes.
- Repo skills: use `.agents/skills/*` for repeatable agent workflows.
- `AGENTS.md`: use for durable repo rules.

Ruflo is optional support, not repo truth. Repo truth comes from code, tests,
data, generated artifacts, commits, and handoffs.

