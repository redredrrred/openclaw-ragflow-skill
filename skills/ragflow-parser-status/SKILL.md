---
name: ragflow-parser-status
description: Use when the task is to inspect, poll, or background-monitor RAGFlow parser status for an existing dataset or specific document IDs without starting a new parse request. Trigger on requests like "check if parsing finished", "watch this document until done", or "monitor parser status in the background".
---

# RAGFlow Parser Status

Use only the bundled scripts in the repository `scripts/` directory.

## Workflow

1. Confirm the dataset ID. If the user cares about specific documents, pass `--doc-ids`.
2. Choose one of the status modes in `parse_status.py`.

```bash
python scripts/parse_status.py DATASET_ID
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --watch
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --background --output /tmp/parse-status.json
```

3. Return the current state, periodic updates, or the background watcher metadata.

If the user wants to start parsing first, switch to `ragflow-dataset-parse` or the top-level ingest skill.

## Scope

Support only:
- get one parser-status snapshot
- poll until the target documents reach terminal states
- launch a detached background watcher
- narrow status checks to selected document IDs

Do not use this skill for dataset creation, upload, or initiating a new parse request.

## Environment

Configure `.env` with:

```bash
RAGFLOW_API_URL=base-url-here
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Commands

```bash
python scripts/parse_status.py DATASET_ID --json
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --json
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --watch --interval 10 --timeout 1800
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --background --output /tmp/parse-status.json --json
```

## Notes

- This skill does not send a parse-start request.
- Prefer `--doc-ids` after a fresh upload or parse when the dataset contains older documents.
- `--background` writes the final payload to `output_path`.
