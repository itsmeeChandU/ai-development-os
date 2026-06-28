# Review Use Terms

This repo and any package generated from it are for private technical, product,
security, compliance, and investor-readiness review.

## Review Scope

Reviewers may inspect:

- source code
- generated reports
- fixture data
- operator dashboard
- customer source-packet workflow
- evidence ledger
- blockers and claim boundaries
- proof commands and test output

## Not In Scope

Reviewers should not treat this package as:

- customs advice
- tariff advice
- legal advice
- CFIA approval
- supplier recommendation
- buyer validation
- production launch approval
- broker, lawyer, accountant, or qualified expert signoff

## Required Reviewer Response Shape

```text
decision: approved_with_scope / blocked / needs_more_evidence / wrong_source / wrong_claim / requires_different_reviewer
scope:
evidence_reviewed:
findings:
blocked_claims:
next_valid_move:
reviewer:
reviewed_at:
```

Review findings become evidence only for the stated scope.
