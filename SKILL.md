---
name: ragflow-dataset-ingest
description: "Use for RAGFlow dataset and retrieval tasks: create, list, inspect, update, or delete datasets; list, upload, update, or delete documents in a dataset; start or stop parsing uploaded documents; check parser status through `parse_status.py`; and retrieve relevant chunks from RAGFlow datasets with `search.py`."
---

# RAGFlow Dataset And Retrieval

Use only the bundled scripts in `scripts/`.
Prefer `--json` for script execution so the returned fields can be relayed exactly.

## Workflow

```bash
python scripts/datasets.py create "My Dataset" --description "Optional description"
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
python scripts/update_dataset.py DATASET_ID --name "Renamed Dataset"
```

1. Create a dataset or confirm the target dataset.
2. Upload files.

When asking the user to provide files, prefer explicit local file paths. If the user's client supports drag-and-drop, they may also drop files into the conversation, but local paths work best and large drag-and-drop uploads may fail.

```bash
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID /path/to/file1 [/path/to/file2 ...]
python scripts/update_document.py DATASET_ID DOC_ID --name "Renamed Document"
```

Upload output returns `document_ids`. Pass those IDs into the next step.

Use delete commands when the task is cleanup instead of ingest:

```bash
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2
```

For document deletion, execute only against explicit document IDs. If the user gives filenames or a fuzzy description, list documents first, resolve exact IDs, and only then run the delete command. Do not perform fuzzy batch delete operations.

3. Start parsing, or stop parsing when explicitly requested.

```bash
python scripts/parse.py DATASET_ID DOC_ID1 [DOC_ID2 ...]
python scripts/stop_parse_documents.py DATASET_ID DOC_ID1 [DOC_ID2 ...]
```

`parse.py` only sends the parse request and returns immediately.

`stop_parse_documents.py` sends a stop request for explicit document IDs, then returns one current status snapshot for those documents.

Use `parse_status.py` when the user asks to check progress or current parser status.

For later requests like "Check the progress" or "Which files are currently being parsed", resolve scope by specificity:
- no dataset specified: inspect all datasets and all documents
- dataset specified: inspect all documents in that dataset
- document IDs specified: inspect only those documents

4. Retrieve chunks from one or more datasets when the user asks knowledge questions against RAGFlow.

```bash
python scripts/search.py "What does the warranty policy say?"
python scripts/search.py "What does the warranty policy say?" DATASET_ID
python scripts/search.py --dataset-ids DATASET_ID1,DATASET_ID2 --doc-ids DOC_ID1,DOC_ID2 "What does the warranty policy say?"
python scripts/search.py --threshold 0.7 --top-k 10 "query"
python scripts/search.py --retrieval-test --kb-id DATASET_ID "query"
```

## Scope

Support only:
- create datasets
- list datasets
- inspect datasets
- update datasets
- delete datasets
- upload documents to a dataset
- list documents in a dataset
- update documents in a dataset
- delete documents from a dataset
- start parsing documents in a dataset
- stop parsing documents in a dataset
- list all currently parsing documents in a dataset for broad progress requests
- aggregate parse progress across all datasets for broad progress requests
- retrieve relevant chunks from one or more datasets
- limit retrieval to specific dataset IDs or document IDs
- use `retrieval_test` for single-dataset debugging when needed

Do not use this skill for chunk editing, memory APIs, or other RAGFlow capabilities outside dataset operations and retrieval.

## Environment

Configure `.env` with:

```bash
RAGFLOW_BASE_URL=http://127.0.0.1:9380
RAGFLOW_API_KEY=ragflow-your-api-key-here
RAGFLOW_DATASET_IDS=["dataset-id-1", "dataset-id-2"]
```

## Endpoints

- `GET /api/v1/datasets`
- `POST /api/v1/datasets`
- `PUT /api/v1/datasets/<dataset_id>`
- `DELETE /api/v1/datasets`
- `POST /api/v1/datasets/<dataset_id>/documents`
- `PUT /api/v1/datasets/<dataset_id>/documents/<document_id>`
- `DELETE /api/v1/datasets/<dataset_id>/documents`
- `POST /api/v1/datasets/<dataset_id>/chunks`
- `DELETE /api/v1/datasets/<dataset_id>/chunks`
- `GET /api/v1/datasets/<dataset_id>/documents`
- `POST /api/v1/retrieval`
- `POST /api/v1/chunk/retrieval_test`

## Commands

```bash
python scripts/datasets.py create "Example Dataset" --description "Quarterly reports"
python scripts/datasets.py create "Example Dataset" --embedding-model bge-m3 --chunk-method naive --permission me
python scripts/datasets.py list
python scripts/datasets.py info DATASET_ID
python scripts/update_dataset.py DATASET_ID --name "Updated Dataset" --description "Updated description"
python scripts/datasets.py delete --ids DATASET_ID1,DATASET_ID2 --json
python scripts/upload.py list DATASET_ID --json
python scripts/upload.py DATASET_ID ./example.pdf --json
python scripts/update_document.py DATASET_ID DOC_ID --name "Updated Document" --enabled 1 --json
python scripts/upload.py delete DATASET_ID --ids DOC_ID1,DOC_ID2 --json
python scripts/datasets.py list --json
python scripts/parse.py DATASET_ID DOC_ID1 --json
python scripts/stop_parse_documents.py DATASET_ID DOC_ID1 --json
python scripts/parse_status.py DATASET_ID --json
python scripts/search.py "query"
python scripts/search.py "query" DATASET_ID --json
python scripts/search.py --dataset-ids DATASET_ID1,DATASET_ID2 --doc-ids DOC_ID1,DOC_ID2 "query" --json
python scripts/search.py --retrieval-test --kb-id DATASET_ID "query" --json
```

## Notes

- Dataset creation supports `--avatar`, `--description`, `--embedding-model`, `--permission`, `--chunk-method`, and `--language`.
- Dataset update supports explicit flags or `--data` JSON payloads through `scripts/update_dataset.py`.
- Upload does not start parsing by itself.
- Prefer local file paths for uploads. Drag-and-drop is acceptable only when the client's UI supports it, and it may fail for large files.
- Document update supports explicit flags or `--data` JSON payloads through `scripts/update_document.py`.
- Dataset deletion is destructive. Require explicit dataset IDs.
- Document deletion is destructive. Require explicit dataset and document IDs. If the user only knows filenames, list documents first and resolve exact IDs before deleting. Do not perform fuzzy batch deletes.
- Parsing is asynchronous.
- `parse.py` returns immediately after the start request. Do not wait for parse status in this command.
- Do not infer likely causes when a script returns an error. Report the script JSON fields exactly as returned.
- When a script returns an error, proactively include the error message in the same reply. Do not wait for the user to ask for the error details.
- If JSON output contains `api_error`, return that API error object directly instead of replacing it with a guessed explanation.
- If JSON output contains `error`, `api_error.message`, `status_error.message`, or `error_detail.message`, surface that message to the user immediately.
- `stop_parse_documents.py` requires explicit dataset and document IDs. If the user only knows filenames, list documents first and resolve exact IDs before stopping parsing. Do not perform fuzzy batch stop operations.
- A stop request may not flip the document to `CANCEL` immediately. Use the returned snapshot or `scripts/parse_status.py` to confirm the terminal state.
- For broad status/progress requests with no dataset specified, list datasets first and aggregate `scripts/parse_status.py DATASET_ID` across all datasets.
- If a dataset is specified, prefer `scripts/parse_status.py DATASET_ID` without `--doc-ids`.
- If document IDs are specified, pass `--doc-ids`.
- Summarize RUNNING files first.
- Status reporting is derived from the dataset document list API. It does not fabricate percentage progress.
- Retrieval defaults to `POST /api/v1/retrieval`.
- `scripts/search.py` accepts `RAGFLOW_DATASET_IDS` from `.env` as the default dataset scope when the user does not specify dataset IDs explicitly.
- Use `--retrieval-test` only when the user wants single-dataset debugging or specifically asks for that endpoint.
