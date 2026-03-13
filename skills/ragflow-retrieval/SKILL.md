---
name: ragflow-retrieval
description: Search RAGFlow knowledge base to retrieve relevant documents and chunks. Use when user asks to search RAGFlow knowledge base, query documents, retrieve information from datasets, or perform knowledge base lookups.
license: MIT
---

# RAGFlow Retrieval

Search RAGFlow knowledge base to retrieve relevant documents and chunks.

## How to Use

### List available datasets

```bash
python scripts/datasets.py list
python scripts/datasets.py list --json
```

### Search knowledge base

```bash
# Search all datasets from .env
python scripts/search.py "your query"

# Search specific dataset
python scripts/search.py "query text" "dataset_id"

# High precision (higher threshold)
python scripts/search.py --threshold 0.7 "query"

# With knowledge graph
python scripts/search.py --use-kg "query"

# Limit to specific documents
python scripts/search.py --doc-ids "doc1,doc2" "query"

# Use retrieval_test API
python scripts/search.py --retrieval-test --kb-id <dataset_id> "query"
```

## Configuration

Environment variables in `.env` file:

```bash
RAGFLOW_API_URL=http://127.0.0.1
RAGFLOW_API_KEY=ragflow-your-api-key-here
RAGFLOW_DATASET_IDS=["dataset-id-1", "dataset-id-2"]
```

Get your API key from RAGFlow Console → Profile → API.

## API Endpoints

**Dataset Management:**
- `GET /api/v1/datasets` - List datasets
- `GET /api/v1/datasets/<dataset_id>` - Get dataset details

**Knowledge Retrieval:**
- `POST /api/v1/retrieval` - Basic retrieval (uses dataset_ids)
- `POST /api/v1/chunk/retrieval_test` - Advanced retrieval (uses kb_id)
