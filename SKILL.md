---
name: ragflow-dataset-ingest
description: "Use for RAGFlow dataset ingestion tasks: create, list, inspect, or delete datasets; list, upload, or delete documents in a dataset; start parsing uploaded documents; and track parser status through `parse.py` snapshot, watch, or background modes."
---

# RAGFlow Dataset Ingest

Use only the bundled scripts in `scripts/`.

## Workflow

```bash
python scripts/datasets.py create "My Dataset" --description "Optional description"
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
```

1. Create a dataset or confirm the target dataset.
2. Upload files.

```bash
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID /path/to/file1 [/path/to/file2 ...]
```

Upload output returns `document_ids`. Pass those IDs into the next step.

Use delete commands when the task is cleanup instead of ingest:

```bash
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2
```

3. Start parsing and return parser status.

```bash
python scripts/parse.py DATASET_ID DOC_ID1 [DOC_ID2 ...]
```

`parse.py` always starts parsing first, then returns status in one of three modes:
- default: return one current parser status snapshot
- `--watch`: print periodic status updates until the target documents reach terminal states
- `--background`: start a detached watcher and return `pid`, `output_path`, and `error_path`

## Scope

Support only:
- create datasets
- list datasets
- inspect datasets
- delete datasets
- upload documents to a dataset
- list documents in a dataset
- delete documents from a dataset
- start parsing documents in a dataset
- return one current parser status snapshot
- print periodic parse status updates
- start a background parse watcher

Do not use this skill for retrieval, chunk editing, memory APIs, or other RAGFlow capabilities.

## Environment

Configure `.env` with:

```bash
RAGFLOW_API_URL=base-url-here
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Endpoints

- `GET /api/v1/datasets`
- `POST /api/v1/datasets`
- `DELETE /api/v1/datasets`
- `POST /api/v1/datasets/<dataset_id>/documents`
- `DELETE /api/v1/datasets/<dataset_id>/documents`
- `POST /api/v1/datasets/<dataset_id>/chunks`
- `GET /api/v1/datasets/<dataset_id>/documents`

## Commands

```bash
python scripts/datasets.py create "Example Dataset" --description "Quarterly reports"
python scripts/datasets.py create "Example Dataset" --embedding-model bge-m3 --chunk-method naive --permission me
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2 --json
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID ./example.pdf --json
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2 --json
python scripts/parse.py DATASET_ID DOC_ID1 --json
python scripts/parse.py DATASET_ID DOC_ID1 --watch --json
python scripts/parse.py DATASET_ID DOC_ID1 --background --output /tmp/parse-status.json --json
```

## Notes

- Dataset creation supports `--avatar`, `--description`, `--embedding-model`, `--permission`, `--chunk-method`, and `--language`.
- Upload does not start parsing by itself.
- Dataset and document deletion are destructive. Require explicit target IDs.
- Parsing is asynchronous.
- `parse.py` returns parser status immediately after the start request; use `--watch` for periodic updates or `--background` for a detached watcher.
- Status reporting is derived from the dataset document list API. It does not fabricate percentage progress.
- `--background` writes the final JSON payload to `output_path`.
