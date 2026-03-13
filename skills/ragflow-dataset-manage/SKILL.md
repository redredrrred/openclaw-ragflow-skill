---
name: ragflow-dataset-manage
description: Use when the task is to create, list, inspect, update, or delete RAGFlow datasets before any upload or parse step. Trigger on requests like "create a dataset", "show my datasets", "find the dataset id", "inspect dataset settings", "rename this dataset", or "delete these datasets". Do not use when the main task is uploading files, deleting documents, starting parsing, or monitoring parser status.
---

# RAGFlow Dataset Manage

Use only the bundled scripts in the repository `scripts/` directory.

## Workflow

Choose the narrowest command that matches the task:

```bash
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
python scripts/datasets.py create "Dataset Name" --description "Optional description"
python scripts/update_dataset.py DATASET_ID --name "Renamed Dataset"
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2
```

Dataset creation also supports optional settings:

```bash
python scripts/datasets.py create "Dataset Name" \
  --embedding-model bge-m3 \
  --chunk-method naive \
  --permission me \
  --language English
```

If the next step is upload or parse, switch to `ragflow-dataset-upload`, `ragflow-dataset-parse`, or the top-level ingest skill.

## Scope

Support only:
- list datasets
- inspect one dataset
- create a dataset
- update a dataset
- delete datasets
- return dataset IDs and basic dataset metadata

Do not use this skill for file upload, parse start, or parser-status monitoring.

## Environment

Configure `.env` with:

```bash
RAGFLOW_BASE_URL=http://127.0.0.1:9380
RAGFLOW_API_KEY=ragflow-your-api-key-here
```

## Commands

```bash
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID --json
python scripts/datasets.py create "Example Dataset" --description "Quarterly reports"
python scripts/update_dataset.py DATASET_ID --name "Example Dataset v2" --description "Updated description"
python scripts/datasets.py create "Example Dataset" --embedding-model bge-m3 --chunk-method naive --permission me --json
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2 --json
```

## Notes

- Use JSON output when another step needs to consume dataset IDs.
- Dataset creation maps directly to `POST /api/v1/datasets`.
- Dataset update maps directly to `PUT /api/v1/datasets/<dataset_id>`.
- Dataset deletion maps directly to `DELETE /api/v1/datasets`.
- The top-level `ragflow-dataset-ingest` skill remains the default choice for multi-step ingest flows.
