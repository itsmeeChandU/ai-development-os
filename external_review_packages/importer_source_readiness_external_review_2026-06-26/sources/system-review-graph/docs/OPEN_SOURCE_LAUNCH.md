# Open Source Launch Guide

This project is ready for a small public launch once maintainers are comfortable
with the README and examples.

## What Makes A Repo Findable

People usually discover open-source developer tools through:

- GitHub search,
- GitHub topics,
- PyPI search,
- README keywords,
- examples in the repo,
- blog posts and walkthroughs,
- Hacker News, Reddit, X, LinkedIn, Discord/Slack communities,
- mentions in related repos and issues,
- package metadata links.

## Current Positioning

Name: `system-review-graph`

Short description:

```text
Generate system-level review graphs: what a repo actually does, not just what code exists.
```

Suggested GitHub topics:

```text
architecture
audit
code-review
documentation
developer-tools
mermaid
reverse-engineering
software-architecture
system-design
system-review
```

## Launch Checklist

- README explains the problem in the first screen.
- Quick start works from a fresh clone.
- Examples are visible without running code.
- Generated reports are committed.
- Package metadata is complete.
- Changelog exists.
- Security/support/conduct docs exist.
- A release tag exists.
- GitHub topics are set.
- PyPI name is checked before publishing.
- README includes visual examples.
- README includes license, version, and citation badges.
- `CITATION.cff`, `AUTHORS.md`, and `NOTICE.md` are present for clear credit.
- A social preview image exists under `assets/social-preview.svg` and can be
  uploaded in GitHub repository settings.
- CI and PyPI publishing workflows exist under `.github/workflows/`.
- PyPI pending publisher is configured for `.github/workflows/publish.yml` with
  the `pypi` environment.
- Wheel install smoke test passes.

## Where To Share

Start small:

1. GitHub release.
2. LinkedIn/X post with one screenshot or Mermaid report snippet.
3. Python and developer-tool communities.
4. Architecture and platform-engineering communities.
5. Open-source maintainers who write onboarding docs.

Good launch message:

```text
I built System Review Graph, a small Python CLI that turns a sanitized manifest
into a system-level blueprint. It is meant to complement code-review graphs:
code graph = what code exists; system review graph = what the system does,
what it trusts, what it blocks, and where reviewers should inspect next.
```
