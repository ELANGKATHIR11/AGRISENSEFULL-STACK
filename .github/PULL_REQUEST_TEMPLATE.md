# Pull Request

Please fill out this template before opening a PR. This project integrates ML components (crop recommendation, soil analysis, disease management, weed management, and chatbot) and often requires environment notes.

## Summary
A short description of the change and why it is needed.

## Related issues
- Closes: 

## Checklist (required)
- [ ] I updated `CHANGELOG.md` or `docs/` if behavior changed.
- [ ] I added/updated unit tests and ensured they run with `AGRISENSE_DISABLE_ML=1`.
- [ ] I verified no secrets or large model artifacts are included in this PR.
- [ ] I added migration notes to `docs/` if I changed persistence schema.
- [ ] I ran `pytest -q scripts/test_backend_inprocess.py scripts/test_edge_endpoints.py` locally and attached the output below.

## Test output (paste here)
```
# paste pytest output or a short summary here
```

## Environment & ML notes (required)
- Does this change require ML models to be present at runtime? (yes/no):
- If yes, which components require models? (check all that apply):
  - [ ] crop recommendation
  - [ ] soil analysis
  - [ ] disease management
  - [ ] weed management
  - [ ] chatbot
- If models are required, state how to reproduce a minimal environment (paths, env vars, or mock artifacts):

## Admin / runtime variables changed
List any required environment variables added/changed (e.g., `AGRISENSE_ADMIN_TOKEN`, `MQTT_BROKER`, `AGRISENSE_ALERT_ON_RECOMMEND`).

## Additional notes
Any other details reviewers should know (backwards-compatibility notes, expected traffic, performance considerations).
