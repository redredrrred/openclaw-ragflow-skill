---
name: ragflow-dataset-ingest
description: Use for RAGFlow dataset ingestion tasks: list datasets, upload documents into a dataset, start parsing uploaded documents, and explicitly check or watch parsing status until those documents finish processing.
---

# RAGFlow Dataset Ingest

Use only the bundled scripts.

## Supported operations

```bash
# List datasets
python scripts/datasets.py list

# Upload one or more files to a dataset
python scripts/upload.py DATASET_ID /path/to/file1 [/path/to/file2 ...]

# Start parsing uploaded documents
python scripts/parse.py DATASET_ID DOC_ID1 [DOC_ID2 ...]

# Check current parsing status once
python scripts/parse_status.py DATASET_ID

# Watch parsing status for specific documents until terminal state
python scripts/parse_status.py DATASET_ID --doc-ids DOC1,DOC2 --watch
```

## Scope

This package supports only:
- list datasets
- upload documents to a dataset
- start parsing documents in a dataset
- check or watch parsing status for documents in a dataset

Do not use it for retrieval, chunk editing, memory APIs, or other RAGFlow capabilities.

## Environment

Configure `.env` with:

```bash
RAGFLOW_API_URL=http://127.0.0.1
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## API endpoints used

- `GET /api/v1/datasets`
- `POST /api/v1/datasets/<dataset_id>/documents`
- `POST /api/v1/datasets/<dataset_id>/chunks`
- `GET /api/v1/datasets/<dataset_id>/documents`

## Recommended workflow

1. List datasets and confirm the target dataset.
2. Upload one or more documents to that dataset.
3. Copy the returned document IDs from upload output.
4. Start parsing with those document IDs.
5. Use `parse_status.py` to check once or watch until those document IDs reach terminal state.

## Candidate commands

```bash
python scripts/datasets.py list
python scripts/upload.py DATASET_ID ./example.pdf
python scripts/parse.py DATASET_ID DOC_ID1
python scripts/parse_status.py DATASET_ID --doc-ids DOC_ID1 --watch
python scripts/parse_status.py DATASET_ID --doc-ids DOC_ID1,DOC_ID2 --watch --interval 10 --timeout 1800
python scripts/parse_status.py DATASET_ID --json
```

## Notes

- Upload does not make a document retrievable by itself; parsing must be started separately.
- Parsing is asynchronous.
- `parse_status.py` reports document state from the dataset document list API; it does not fabricate percentage progress.
- Prefer `--doc-ids` after a fresh upload/parse so you monitor only the target documents instead of the entire dataset.
