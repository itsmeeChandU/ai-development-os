# Prompt To Product

A simple prompt can create a lot. It cannot safely create everything.

## Simple Prompt Is Enough When

- the app is self-contained
- no private data is required
- no paid API is required
- no account login is required
- no regulated claim is made
- no money or external action happens
- screenshots or tests can prove the result

Example:

```text
Build a local habit tracker web app with add/edit/delete habits, streaks,
calendar view, local storage, tests, and a README. Start the dev server.
```

## More Context Is Needed When

- the user or buyer is unclear
- the product needs real data
- the product depends on APIs or credentials
- the product has multiple modules
- the system already exists
- legal, financial, medical, privacy, or public claims are involved
- launch quality matters

## External Tools May Be Needed

Load tools only when the work proves a need:

- GitHub MCP: issues, PRs, repo management.
- Docs MCP / Context7: current library/API docs.
- Browser / Playwright: UI verification, screenshots, auth flows.
- Figma MCP: design systems and UI translation.
- Database tools: schema inspection, migrations, loaded data checks.
- Search/web: current APIs, pricing, laws, docs, open-source alternatives.
- Ruflo or memory MCP: local coordination and continuity.

## Product Generation Checklist

Before claiming a generated product is complete:

- run it locally
- test the main user flow
- inspect mobile and desktop UI
- run focused tests
- check generated artifacts
- list missing data/API credentials
- write launch/readiness status
- write next valid moves

