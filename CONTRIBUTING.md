# Contributing

Use a focused branch/PR with a clear scope. Do not submit client documents,
credentials, personal financial data, copyrighted standards text, or screenshots
of subscription research products. Use original prose and fictional examples.

## Content changes

1. Select an issue from `content/ROADMAP.md`; identify the relevant framework,
   period, source scope, and intended audience.
2. Write an original article or exercise. Cite the specific official sources
   actually examined. Mark inaccessible primary text as a gap. A search snippet
   is not evidence that a standard was reviewed.
3. Include an illustrative fact pattern, missing facts, alternatives, and clear
   limits. Keep calculation assumptions separate from accounting judgments.
4. Add/update the manifest with a new immutable version and SHA-256. List source
   IDs from `content/references/sources.json`. Keep review status unreviewed.
5. For a correction, explain the change and affected claims; do not silently
   overwrite a released version or preserve a superseded approval.
6. Run `python scripts/check_content.py` and the relevant tests.
7. A different qualified reviewer must document actual technical review. Source
   rights approval is independent. Software test passes do not approve accounting.

Contributions to code are offered under MIT; contributions to original content
are offered under CC BY 4.0, as documented in the repository. Do not add a claimed
license to material you are not authorized to contribute. Identify substantive
AI assistance and verify its output.

## Code changes

```bash
python -m pip install -e './backend[dev]'
PYTHONPATH=backend pytest backend/tests
cd frontend && npm install && npm run typecheck && npm run build
```

Add tests for permissions, subscription boundaries, workspace isolation, source
changes, and error handling. Do not weaken a source gate merely to make a sample
answer longer. Pin and review new third-party dependencies. Never submit `.env`,
live keys, database files, uploads, or cloud state.

## Review checklist

Describe behavior, tests executed, tests not executed, migration impact, rights
impact, and privacy implications. Use the PR template. Do not claim a model call,
professional review, GitHub publication, or deployment that was not performed.
