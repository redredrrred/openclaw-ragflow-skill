---
name: openclaw-ragflow-skill
description: Search RAGFlow knowledge base, retrieve documents, manage datasets and chunks via HTTP API. Use when user asks about RAGFlow, knowledge base search, document retrieval, or dataset management. Always use scripts in scripts/ directory (search.py, datasets.py, chunks.py, memory.py) instead of writing custom API calls.
license: MIT
---

# RAGFlow Knowledge

RAGFlow-powered knowledge retrieval and document management.

## ⚠️ For AI: Use These Scripts

**DO NOT write custom API code.** Always use these scripts:

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

## 🚀 Quick Start

### Configuration

Set environment variables in `.env` file:

```bash
RAGFLOW_API_URL=http://127.0.0.1
RAGFLOW_API_KEY=ragflow-your-api-key-here
RAGFLOW_DATASET_IDS=["dataset-id-1", "dataset-id-2"]
```

### Basic Usage

```bash
# Search knowledge base
python scripts/search.py "your search query"

# List datasets
python scripts/datasets.py list

# Manage memory
python scripts/memory.py list
```

## 🔍 Search Knowledge Base

### Basic Search

```bash
curl -s -X POST "${RAGFLOW_API_URL}/api/v1/retrieval" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"question": "Your search query"}'
```

### Advanced Search with Python Script

```bash
# High-precision search
python scripts/search.py --threshold 0.7 --vector-weight 0.7 "query"

# With knowledge graph
python scripts/search.py --use-kg "conceptual query"

# Limit to specific documents
python scripts/search.py --doc-ids "doc1,doc2" "query"
```

## 📚 Dataset Management

### List Datasets

```bash
python scripts/datasets.py list
```

### Get Dataset Details

```bash
python scripts/datasets.py info DATASET_ID
```

### Dataset API Fields

When listing datasets, each dataset contains:
- `name` - Dataset name
- `id` - Unique identifier
- `description` - Description text
- `chunk_count` - Number of document chunks
- `document_count` - Number of documents
- `created_at` - Creation timestamp
- `permission` - Access permissions

## 🧠 Memory Management

### Memory Operations

```bash
# List all memories
python scripts/memory.py list

# Get memory configuration
python scripts/memory.py config MEMORY_ID

# Get messages from memory
python scripts/memory.py messages MEMORY_ID

# Search messages
python scripts/memory.py search MEMORY_ID "search query"

# Delete memory
python scripts/memory.py delete MEMORY_ID
```

### Memory Types

- `longtime` - Long-term memory storage
- `user` - User-specific memories
- `agent` - Agent memories
- `session` - Session-based memories

## 📝 Chunk Management

### Chunk CRUD Operations

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

## 🔧 Advanced Retrieval

### Retrieval Parameters

**Core Parameters:**
- `question` (required) - Search query
- `dataset_ids` / `kb_id` - Dataset identifier
- `top_k` - Maximum results (default: 1024)
- `similarity_threshold` - Minimum similarity (0-1)

**Similarity Control:**
- `vector_similarity_weight` - Vector vs keyword balance (default: 0.3)
- Lower (0.1) favors keywords, higher (0.7) favors semantics

**Content Filtering:**
- `doc_ids` - Limit to specific documents
- `meta_data_filter` - Filter by metadata

**Advanced Features:**
- `keyword` - Extract keywords for matching
- `rerank_id` - Use reranking model
- `use_kg` - Include knowledge graph
- `cross_languages` - Multilingual search

### Basic vs Retrieval Test API

**Basic Retrieval** (`/api/v1/retrieval`):
- No login required
- Uses `dataset_ids` parameter
- Default threshold: 0.2

**Retrieval Test** (`/api/v1/chunk/retrieval_test`):
- Login required
- Uses `kb_id` parameter (required)
- Default threshold: 0.0
- Returns additional `labels` field
- Supports advanced metadata filtering

## 📖 API Endpoints Reference

### Knowledge Base & Retrieval
- `POST /api/v1/retrieval` - Basic retrieval
- `POST /api/v1/chunk/retrieval_test` - Advanced retrieval (login)
- `GET /api/v1/datasets` - List datasets
- `GET /api/v1/chunk/get` - Get chunk details
- `POST /api/v1/chunk/create` - Create chunk
- `POST /api/v1/chunk/set` - Update chunk
- `POST /api/v1/chunk/switch` - Toggle availability
- `POST /api/v1/chunk/rm` - Delete chunks
- `POST /api/v1/chunk/list` - List chunks in document
- `GET /api/v1/chunk/knowledge_graph` - Get knowledge graph

### Memory Management
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
- `GET /api/v1/messages` - Get recent messages
- `GET /api/v1/messages/<mid>:<msgid>/content` - Get content

## 📊 Response Format

```json
{
  "code": 0,
  "data": {
    "chunks": [
      {
        "chunk_id": "unique-id",
        "content": "Document content...",
        "similarity": 0.8923,
        "document_keyword": "document.pdf",
        "doc_id": "doc-id",
        "dataset_id": "dataset-id"
      }
    ],
    "doc_aggs": [
      {
        "doc_id": "doc-id",
        "count": 5,
        "doc_name": "document.pdf"
      }
    ]
  }
}
```

## 🛠️ Troubleshooting

### Connection Issues

```bash
curl "${RAGFLOW_API_URL}/api/v1/datasets" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}"
```

### No Results Found

- Lower `similarity_threshold` to 0.1
- Increase `top_k` to 20+
- Enable `keyword` extraction
- Verify datasets contain documents

## 📚 Resources

- RAGFlow Documentation: https://ragflow.io/docs
- HTTP API Reference: https://ragflow.io/docs/dev/http_api_reference