---
name: ragflow-dataset-parse
description: Use when the task is to start parsing already-uploaded RAGFlow documents and return the immediate parser status from that start request. Trigger on requests like "parse these document IDs", "start indexing this dataset", or "kick off parsing after upload". Do not use when the main task is only checking status later without starting a new parse run.
---

# RAGFlow Dataset Parse

Use only the bundled scripts in the repository `scripts/` directory.

## Workflow

1. Confirm the target dataset ID and document IDs.
2. Start parsing with `parse.py`.

```bash
python scripts/parse.py DATASET_ID DOC_ID1 [DOC_ID2 ...]
python scripts/parse.py DATASET_ID DOC_ID1 --json
```

3. Choose a mode:
- default: start parsing and return one status snapshot
- `--watch`: keep printing periodic updates until terminal states
- `--background`: start a detached watcher and return `pid`, `output_path`, and `error_path`

```bash
python scripts/parse.py DATASET_ID DOC_ID1 --watch --json
python scripts/parse.py DATASET_ID DOC_ID1 --background --output /tmp/parse-status.json --json
```

If the user only wants a later status check without starting parsing, switch to `ragflow-parser-status`.

## Scope

Support only:
- start parsing uploaded documents in a dataset
- return the immediate parser status snapshot
- optionally keep watching until completion
- optionally launch a detached background watcher

Do not use this skill for dataset creation, file upload, or standalone parser-status checks.

## Environment

Configure `.env` with:

```bash
RAGFLOW_API_URL=base-url-here
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Commands

```bash
python scripts/parse.py DATASET_ID DOC_ID1 [DOC_ID2 ...]
python scripts/parse.py DATASET_ID DOC_ID1 --json
python scripts/parse.py DATASET_ID DOC_ID1 --watch --json
python scripts/parse.py DATASET_ID DOC_ID1 --background --output /tmp/parse-status.json --json
```

## Notes

- `parse.py` always starts parsing before reporting status.
- Status is derived from the dataset documents API; it does not invent progress percentages.
- Use document IDs from a fresh upload when you want to limit monitoring to the new files.
