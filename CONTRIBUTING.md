# Contributing

Thank you for wanting to contribute! A few quick guidelines to keep contributions focused and easy to review.

- Open a branch per feature or fix: `git checkout -b feat/some-feature`.
- Keep large model files out of Git. Use Git LFS or external storage. If a model must be committed, add a clear version file and small example inputs.
- When moving files, prefer `git mv` so history is preserved.
- Run the backend smoke test before opening a PR:

  python -c "import requests; print(requests.get('<http://127.0.0.1:8004/health>').status_code)"

- Add tests for logic changes (unit or integration) and update `README.md` when you change run instructions.

Maintainers: add PR checklist and CI notes here.
