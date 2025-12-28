Quick testing and CI notes

This project historically contains multiple copies of `agrisense_app` in the
workspace which can cause import-time conflicts during testing. Follow these
recommendations when running tests locally or in CI:

- Use the repository-root `AGRISENSEFULL-STACK` as the canonical package root.
- Activate the project's virtualenv (create one if missing) and install
  dependencies from `agrisense_app/backend/requirements.txt`.
- Run unit tests with the ML-disabled flag to avoid importing heavy ML
  libraries during fast test runs:

  $env:AGRISENSE_DISABLE_ML='1'
  .venv\Scripts\python.exe -m pytest

- Integration tests are marked with `@pytest.mark.integration` and are
  excluded from default unit runs. Run them explicitly:

  .venv\Scripts\python.exe -m pytest -m integration

- If you need to run tests against a specific copy of `agrisense_app`, set
  PYTHONPATH to the desired directory before running pytest.

Small housekeeping tasks to consider:
- Consolidate duplicate `agrisense_app` copies into one directory and remove
  the duplicate to avoid future import confusion.
- Keep tests free of network calls at import time; use fixtures or explicit
  main guards for manual scripts.
