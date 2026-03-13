---
name: ragflow-dataset-upload
description: Use when the task is limited to choosing a RAGFlow dataset and listing, uploading, or deleting documents in it. Trigger on requests like "show documents in dataset X", "upload this PDF to dataset X", "put these files into RAGFlow", "delete these document IDs", or "list datasets so I can upload". Do not use when the task is primarily about dataset creation/deletion, starting parsing, or monitoring parser status.
---

# RAGFlow Dataset Upload

Use only the bundled scripts in the repository `scripts/` directory.

## Workflow

1. If the target dataset is unknown, inspect it first.

```bash
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
```

2. List, upload, or delete documents as needed.

```bash
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID /path/to/file1 [/path/to/file2 ...]
python scripts/upload.py DATASET_ID ./example.pdf --json
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2 --json
```

3. Return the uploaded `document_ids`. If the user also wants parsing, switch to `ragflow-dataset-parse` or the top-level ingest skill.

## Scope

Support only:
- list datasets to choose an upload target
- inspect one dataset before upload
- list documents in an existing dataset
- upload files into an existing dataset
- delete documents from an existing dataset
- return uploaded document IDs and basic metadata

Do not use this skill for dataset creation/deletion, starting parsing, or parser-status polling.

## Environment

Configure `.env` with:

```bash
RAGFLOW_API_URL=base-url-here
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Commands

```bash
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID /path/to/file1 /path/to/file2
python scripts/upload.py DATASET_ID ./example.pdf --json
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2 --json
```

## Notes

- Upload does not start parsing by itself.
- Prefer `list` before delete when the user only knows document names, not IDs.
- Document deletion is destructive. Require explicit document IDs.
- Validate file paths before uploading.
- Prefer JSON output when another step will consume the uploaded `document_ids`.
