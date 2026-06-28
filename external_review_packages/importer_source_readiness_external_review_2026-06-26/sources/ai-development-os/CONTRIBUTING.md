# Contributing

Contributions are welcome when they strengthen the core goal: helping AI agents
turn prompts and existing product state into verified working software.

## Contribution Rules

By submitting a contribution, you agree that:

1. your contribution follows `CONTRIBUTOR_TERMS.md`
2. your contribution may be included in this project under `AGPL-3.0-or-later`
3. the project owner may offer separate licenses for the project, including
   commercial/private/association licenses
4. you preserve the attribution and notice requirements
5. you do not imply official association, endorsement, or partnership unless a
   separate written agreement exists
6. you are responsible for the rights, licenses, data, and secrets in your own
   contribution

## Required Developer Certificate

Every commit should include a sign-off:

```text
Signed-off-by: Your Name <you@example.com>
```

This follows the Developer Certificate of Origin process in `DCO.txt`.

## What To Contribute

Good contributions include:

- better state reconstruction workflows
- stronger system review graph patterns
- prompt-to-product templates
- tool/research registry improvements with sources
- validation scripts
- generated artifact patterns
- agent handoff and lane coordination patterns

## What Not To Contribute

Do not contribute:

- proprietary code or private customer material
- secrets, credentials, tokens, keys, or passwords
- copied content without rights
- claims that cannot be proven
- licensing changes that weaken the project posture
- attribution removal
- official association language without written approval

## Pull Request Checklist

- [ ] I read `AGENTS.md`
- [ ] I read `CONTRIBUTOR_TERMS.md`
- [ ] I signed off my commits
- [ ] I ran `python3 scripts/ai_dev_os_check.py`
- [ ] I ran `git diff --check`
- [ ] I updated docs/templates/manifests if the process changed
- [ ] I did not add secrets or private data

