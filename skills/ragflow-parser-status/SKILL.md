---
name: ragflow-parser-status
description: Use when the task is to inspect, poll, or background-monitor RAGFlow parser status for an existing dataset or specific document IDs without starting a new parse request. Trigger on requests like "check if parsing finished", "show parsing progress", "which files are still parsing", "watch this document until done", or "monitor parser status in the background".
---

# RAGFlow Parser Status

Use only the bundled scripts in the repository `scripts/` directory.

## Workflow

1. Resolve scope by specificity:
   - if the user specifies document IDs, inspect only those documents
   - else if the user specifies one dataset, inspect all documents in that dataset
   - else inspect all datasets and all documents
2. For all-dataset progress requests, first list datasets with `python scripts/datasets.py list --json`, then run `python scripts/parse_status.py DATASET_ID --json` for each dataset.
3. For dataset-level status or progress requests, query the whole dataset without `--doc-ids` so the result includes all currently parsing files.
4. Use `--doc-ids` only when the user explicitly wants a narrowed subset.
5. Choose one of the status modes in `parse_status.py`.

```bash
python scripts/parse_status.py DATASET_ID
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --watch
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --background --output /tmp/parse-status.json
```

3. Return the current state, periodic updates, or the background watcher metadata.
When responding to a generic progress request, summarize `summary.RUNNING` first and list the RUNNING documents before mentioning terminal documents. If no dataset was specified, aggregate across all datasets and present dataset-grouped results.

If the user wants to start parsing first, switch to `ragflow-dataset-parse` or the top-level ingest skill.

## Scope

Support only:
- get one parser-status snapshot
- poll until the target documents reach terminal states
- launch a detached background watcher
- narrow status checks to selected document IDs
- list all currently parsing documents in a dataset when the request is broad
- aggregate parser progress across all datasets when no dataset is specified

Do not use this skill for dataset creation, upload, or initiating a new parse request.

## Environment

Configure `.env` with:

```bash
RAGFLOW_BASE_URL=http://127.0.0.1:9380
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Commands

```bash
python scripts/datasets.py list --json
python scripts/parse_status.py DATASET_ID --json
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --json
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --watch --interval 10 --timeout 1800
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --background --output /tmp/parse-status.json --json
```

## Notes

- This skill does not send a parse-start request.
- For requests like "看下进度" or "还有哪些文件在解析" with no dataset specified, inspect all datasets first.
- For the same requests with a dataset specified, prefer `python scripts/parse_status.py DATASET_ID` without `--doc-ids`.
- Prefer `--doc-ids` after a fresh upload or parse when the dataset contains older documents.
- In natural-language responses, prioritize files with `RUNNING` status and include dataset-level counts.
- `--background` writes the final payload to `output_path`.
