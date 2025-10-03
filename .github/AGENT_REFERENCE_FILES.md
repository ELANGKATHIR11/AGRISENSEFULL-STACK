Agent reference files (authoritative)

For any automated agent or human making changes in this repository, the following files are the authoritative references and MUST be consulted before making edits, running tests, or changing behaviors:

1. `.github/copilot-instructions.md`
   - Purpose: primary orientation and edit rules for automated assistants. Contains developer workflows, ML/CI guidance, small contract for API shapes, and PR checklist.
2. `.github/PULL_REQUEST_TEMPLATE.md`
   - Purpose: PR submission checklist; requires test outputs and explicit ML environment notes for any change that touches ML components (crop recommendation, soil analysis, disease management, weed management, chatbot).

Agent rules

- Always read both files fully before starting changes.
- If a change affects API shapes, ML loading, persistence, or environment variables, update the relevant sections in these files and ensure tests are added/updated.
- When running tests or CI steps, prefer to run with `AGRISENSE_DISABLE_ML=1` for fast validation, and include instructions for reproducing the ML-enabled run when models are required.
- Do not commit secrets, large model artifacts, or any binary ML model files without explicit approval and release notes.

Location

- This file is intentionally small and lives at `.github/AGENT_REFERENCE_FILES.md` to be easily found by reviewers and automation.

If you want to add another authoritative file to this list, propose it in a PR and reference why it should be considered required reading for agents.