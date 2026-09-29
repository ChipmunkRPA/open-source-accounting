# Public publication boundary

Run `python3 scripts/check_public.py --dist` after a clean frontend build. Only generated `frontend/dist` is a deployable public frontend artifact. Never publish the repository directory, local `.private` checkout, environment files, databases or dependency caches. CI rejects unexpected source paths and generated modules using an explicit allowlist. Review file contents as well as paths: an allowlist cannot recognize arbitrary confidential text.

The complete hosted application is maintained in the separate private repository. No production deployment or paid resources are authorized by these instructions. Earlier public Git history remains public; separation does not revoke historical MIT grants. Do not rewrite history or force-push.
