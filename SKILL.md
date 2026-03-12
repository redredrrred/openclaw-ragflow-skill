---
name: ragflow_knowledge
description: When user asks to search RAGFlow knowledge base, query documents in RAGFlow, look up information from ragflow, or search datasets. Keywords: "ragflow search", "ragflow 搜索", "查一下ragflow", "ragflow里有什么", "用ragflow找"
license: MIT
---

# RAGFlow Knowledge

RAGFlow-powered knowledge retrieval and document management.

## How to Use

When user asks to search RAGFlow, use these scripts (DO NOT write custom API code):

```bash
# Search knowledge base
python scripts/search.py "query"

# List datasets
python scripts/datasets.py list

# Manage chunks
python scripts/chunks.py list <doc_id>

# Memory operations
python scripts/memory.py list
```

The scripts handle Windows UTF-8 encoding, environment loading, and error handling.

## Configuration

Environment variables in `.env` file:

```bash
RAGFLOW_API_URL=http://127.0.0.1
RAGFLOW_API_KEY=ragflow-your-api-key-here
RAGFLOW_DATASET_IDS=["dataset-id-1", "dataset-id-2"]
```

## Search Options

```bash
# Basic search
python scripts/search.py "your query"

# High precision (higher threshold)
python scripts/search.py --threshold 0.7 "query"

# With knowledge graph
python scripts/search.py --use-kg "query"

# Limit to specific documents
python scripts/search.py --doc-ids "doc1,doc2" "query"

# Use retrieval_test API (lower threshold by default)
python scripts/search.py --retrieval-test --kb-id <dataset_id> "query"
```

## Dataset Management

```bash
# List all datasets
python scripts/datasets.py list

# Get dataset details
python scripts/datasets.py info DATASET_ID
```

## Memory Management

```bash
# List all memories
python scripts/memory.py list

# Get memory configuration
python scripts/memory.py config MEMORY_ID

# Get messages from memory
python scripts/memory.py messages MEMORY_ID

# Search messages
python scripts/memory.py search MEMORY_ID "search query"
```

## Chunk Management

```bash
# List chunks in document
python scripts/chunks.py list DOC_ID

# Get chunk details
python scripts/chunks.py get CHUNK_ID

# Create new chunk
python scripts/chunks.py create DOC_ID "chunk content"

# Update chunk
python scripts/chunks.py update DOC_ID CHUNK_ID "updated content"

# Delete chunks
python scripts/chunks.py delete DOC_ID CHUNK_ID1,CHUNK_ID2
```

## API Endpoints

**Retrieval:**
- `POST /api/v1/retrieval` - Basic retrieval (no auth, uses dataset_ids)
- `POST /api/v1/chunk/retrieval_test` - Advanced retrieval (login required, uses kb_id)

**Datasets:**
- `GET /api/v1/datasets` - List datasets

**Chunks:**
- `GET /api/v1/chunk/get` - Get chunk details
- `POST /api/v1/chunk/create` - Create chunk
- `POST /api/v1/chunk/set` - Update chunk
- `POST /api/v1/chunk/switch` - Toggle availability
- `POST /api/v1/chunk/rm` - Delete chunks
- `POST /api/v1/chunk/list` - List chunks in document

**Memory:**
- `POST /api/v1/memories` - Create memory
- `PUT /api/v1/memories/<id>` - Update memory
- `DELETE /api/v1/memories/<id>` - Delete memory
- `GET /api/v1/memories` - List memories
- `GET /api/v1/memories/<id>/config` - Get configuration
- `GET /api/v1/memories/<id>` - Get messages
- `POST /api/v1/messages` - Add message
- `DELETE /api/v1/messages/<mid>:<msgid>` - Forget message
- `PUT /api/v1/messages/<mid>:<msgid>` - Update status
- `GET /api/v1/messages/search` - Search messages
