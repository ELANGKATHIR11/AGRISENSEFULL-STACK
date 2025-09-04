Archive of removed chatbot backend artifacts
=========================================

This folder documents the chatbot backend artifacts and scripts that were removed on branch
`remove/chatbot-backend` on 2025-09-04. The files were intentionally removed from the active
tree to declutter the main app; this README preserves a record and provides quick restore steps.

Removed items (examples):

- `agrisense_app/backend/chatbot_answer_encoder/` (SavedModel)
- `agrisense_app/backend/chatbot_question_encoder/` (SavedModel)
- `agrisense_app/backend/chatbot_index.npz`, `chatbot_index.json`
- `agrisense_app/backend/chatbot_q_index.npz`, `chatbot_qa_pairs.json`
- `agrisense_app/backend/chatbot_metrics.json`
- `agrisense_app/backend/chatbot_lgbm_ranker.joblib`
- `agrisense_app/backend/chatbot_merged_clean.csv`
- `agrisense_app/backend/chatbot_augmented_qa.csv`
- `scripts/train_chatbot.py`, `scripts/compute_chatbot_metrics.py`, `scripts/build_chatbot_qindex.py`, `scripts/chatbot_infer.py`, etc.

How to restore a specific file from the branch history:

1. Identify the commit in which the file existed (on branch `remove/chatbot-backend` the deletions are committed).
2. Use git checkout &lt;commit&gt; -- &lt;path/to/file&gt; to restore a single file into your working tree.

Example:

```powershell
# while on your working branch
git fetch origin
git checkout origin/remove/chatbot-backend -- agrisense_app/backend/chatbot_index.npz
```

If you want me to move the actual files into a physical `archive/chatbot-backend-2025-09-04/` folder in this branch
instead of deleting them, tell me and I will restore and `git mv` them into that folder and commit.
