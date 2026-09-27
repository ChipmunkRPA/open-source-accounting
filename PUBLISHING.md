# Publishing open-source-accounting

Canonical public repository: https://github.com/ChipmunkRPA/open-source-accounting

The repository now exists. Do not run the legacy creation-only publisher against it. For ongoing development:

```bash
git clone https://github.com/ChipmunkRPA/open-source-accounting.git
cd open-source-accounting
git switch -c feature/topic-or-module
# Make changes; never copy .env, data, credentials or a different .git directory.
python scripts/check_content.py
python scripts/content_progress.py
python scripts/release_preflight.py --check
# Run backend/frontend tests described in readme.md.
git add <reviewed-source-files>
git commit -m "Describe the code/content change"
git push -u origin feature/topic-or-module
```

Open a pull request, record actual validation and review gaps in `progress.md`, and preserve content-version provenance. Configure protected branches and a private vulnerability reporting channel before accepting broad contributions. Do not presume branch protection or private reporting has already been enabled.

Generated frontend bundles can be rebuilt from source; do not commit local credentials, personal uploads, database contents, dependency directories, or Terraform state. Public source publication is independent from production Cloud Run deployment and Stripe activation.

An initial source-import workflow, when present, only expands a hash-verified repository payload into readable source files. It does not deploy the website or access cloud credentials. It must refuse conflicting existing source files and never force-push. Remove the one-time workflow and payload after successful source verification.


## Existing renamed repository

The target is the existing public `ChipmunkRPA/open-source-accounting`. The earlier create-new-repository script should not be used for this repository. The connector staging attempt is incomplete and must not be treated as a release.

```bash
gh auth login
python3 scripts/publish_existing_repository.py
# Review the printed file paths and hashes before applying.
python3 scripts/publish_existing_repository.py --apply
```

The publisher refuses existing application code, unexpected bootstrap files, different accounts, private/archived repositories, and non-fast-forward pushes. It cleans only the temporary source-transport objects in the current working tree, preserves remote Git history, and verifies the resulting commit. It requires Git, GitHub CLI, Python, and network access. Running it was not possible without GitHub CLI credentials in this workspace. This script has been syntax-checked; live execution remains untested.
