# open-source-accounting — publication status

The project has been renamed to **open-source-accounting**.

## Local release prepared

The prepared v0.6 release includes the application, 63 original educational content items, 58 study questions, 26 source/license reference records, and a generated topic-by-topic content progress tracker. All new educational material is an AI-assisted editorial draft, not professionally approved guidance.

The code includes Google Cloud Identity Platform/Firebase authentication with mandatory verified-email and TOTP (Google Authenticator compatible) or SMS second-factor checks for authenticated application access. Public educational pages remain accessible without signing in. General AI chat remains free; hosted Agent work is configured for US$89.99/year.

Recorded local validation: 203 Python tests and 16 mocked MFA-controller tests passed; TypeScript checks and the demo frontend build passed. These are not live-provider tests. Google Cloud deployment, real MFA enrollment/sign-in, SMS delivery, a complete Firebase SDK production bundle build, and live Gemini/Stripe integration remain outstanding.

## Publication is NOT verified complete

The connector-based source staging attempt encountered integrity mismatches. The temporary transport files must not be treated as runnable source or imported without their expected checksums. The complete verified local release is supplied separately in the conversation.

To publish that release into this existing repository after reviewing it:

```bash
# Run inside the extracted open-source-accounting release.
gh auth login
python3 scripts/publish_existing_repository.py
# Inspect the preview before applying:
python3 scripts/publish_existing_repository.py --apply
```

The publisher targets only ChipmunkRPA/open-source-accounting, preserves Git history, refuses unexpected existing application code, never force-pushes, and checks the remote commit after a successful push. The script is syntax-checked; its live authenticated execution has not been performed in the development environment.

Publishing source code does not deploy the website, configure the Google Cloud project, or make draft accounting content suitable for professional reliance.
