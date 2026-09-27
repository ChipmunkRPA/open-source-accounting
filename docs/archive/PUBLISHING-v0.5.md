# Publish a new public GitHub repository

## Authoring-environment status

The connected GitHub account was identified as **ChipmunkRPA**. Repository lookup
for `ChipmunkRPA/open-accounting` returned 404 on September 27, 2026. The available
connection can work with repository contents but does not expose repository creation.
**No GitHub repository or remote commit was created by the authoring session.**

The following script is provided for execution on your own machine, where you can
authorize GitHub CLI. Never paste a token into source files or a chat message.

## Review and publish

Install Git and GitHub CLI, extract the release ZIP, then run from `open-accounting`:

```bash
gh auth login
python scripts/release_preflight.py --write
python scripts/publish_github.py --owner ChipmunkRPA --dry-run
# Review release-manifest.json. The next command publishes to the public internet.
python scripts/publish_github.py --owner ChipmunkRPA --confirm-public
```

The script verifies that the CLI user matches the target personal account; checks
that the repository is absent; rescans the files; checks the manifest hashes;
creates a clean temporary Git snapshot; and calls `gh repo create` with public
visibility. It then verifies public visibility and the pushed main-branch SHA.

It refuses existing repositories, account mismatches, changed files, suspected
credentials, and ambiguous connection failures. It never converts a private
repository, reuses unrelated Git history, or force-pushes. It does not deploy the
web application, create Cloud resources, set billing secrets, or activate paid plans.
The command requires GitHub permissions to create and push repository contents,
including the included GitHub Actions workflow.

After publication, clone the repository normally to a durable local checkout.
The temporary staging directory is deleted by the publication script.

## When using the connected assistant instead

Create a new public repository for this project and make it accessible to the
GitHub connection. Do not select or expose an unrelated private repository. The
assistant can then read the new repository and use the available content/commit
operations. A new initialized README can provide the initial branch/commit.
The publishing script intentionally refuses existing repositories; it is an
alternative to this connected-tool route, not a step to run afterward.

## Follow-up repository settings

Enable private vulnerability reporting, branch protection/rules appropriate to the
project, and required CI checks. Review issue/PR templates and contributor rights.
Those administration actions were not performed in the authoring session.

The code is MIT; original educational content is CC BY 4.0. The hosted $89.99/year
Agent plan remains an application service setting, not a restriction on either
open license. Publisher standards and marks are not relicensed by this repository.
