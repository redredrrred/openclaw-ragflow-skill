---
name: ragflow_knowledge
description: Search RAGFlow knowledge bases for intelligent document retrieval
version: 1.0.0
author: redredrrred
tags: [rag, knowledge, search, retrieval, documents]
license: MIT
---

# RAGFlow Knowledge Search Skill

Enable AI agents to search and retrieve information from RAGFlow knowledge bases.

## 🎯 Purpose

This skill allows the AI agent to:
- Search RAGFlow knowledge bases for relevant documents
- Retrieve factual information from company documents, manuals, policies
- Provide evidence-based answers with source citations

## ⚙️ Configuration

The skill uses RAGFlow API credentials. Configure them first:

### Quick Setup (Environment Variables)

```bash
export RAGFLOW_API_URL="http://127.0.0.1"
export RAGFLOW_API_KEY="your-api-key-here"
export RAGFLOW_DATASET_IDS='["dataset-id-1", "dataset-id-2"]'
```

### Alternative: Direct Configuration

Replace the placeholder values in this skill with your actual:
- `RAGFLOW_API_URL`: Your RAGFlow server URL (default: `http://127.0.0.1`)
- `RAGFLOW_API_KEY`: Your RAGFlow API key
- `RAGFLOW_DATASET_IDS`: Array of dataset IDs to search (optional, searches all if empty)

## 🔍 When to Use This Skill

Use this skill when the user asks about:
- Company policies, procedures, or documentation
- Product specifications or manuals
- Technical knowledge base content
- Any factual information stored in documents
- **What datasets are available**
- **Details about a specific dataset**

## 📚 Managing Datasets

This skill supports listing datasets and getting detailed information.

### List All Datasets

When the user asks "what datasets do you have?" or "show available datasets":

```bash
# Using curl
curl -s -X GET "${RAGFLOW_API_URL}/api/v1/datasets" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}" | jq '.data[] | {
    name: .name,
    id: .id,
    description: .description,
    chunks: .chunk_num
  }'

# Or use the helper script
./datasets.sh list
```

### Get Dataset Details

When the user asks for details about a specific dataset:

```bash
# Using curl (replace DATASET_ID)
curl -s -X GET "${RAGFLOW_API_URL}/api/v1/datasets" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}" | \
  jq '.data[] | select(.id == "DATASET_ID")'

# Or use the helper script
./datasets.sh info DATASET_ID
```

### Dataset Information Includes

- **name**: Dataset name
- **id**: Unique dataset identifier
- **description**: What the dataset contains
- **chunk_num**: Number of document chunks
- **created_at**: When it was created
- **permission**: Access permissions

## 📖 How to Search

### Method 1: Using curl (Recommended)

```bash
curl -s -X POST "${RAGFLOW_API_URL}/api/v1/retrieval" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "USER_QUERY_HERE",
    "dataset_ids": ['${RAGFLOW_DATASET_IDS}'],
    "top_k": 5
  }'
```

### Method 2: Using jq for Pretty Output

```bash
curl -s -X POST "${RAGFLOW_API_URL}/api/v1/retrieval" \
  -H "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "USER_QUERY_HERE",
    "dataset_ids": ['${RAGFLOW_DATASET_IDS}'],
    "top_k": 5
  }' | jq -r '.data.chunks[] | "📄 [\(.document_keyword)] (相似度: \(.similarity * 100 | floor)%)\n\(.content)\n"'
```

## 📊 Understanding the Response

The API returns JSON with:
- `code`: Status code (0 = success)
- `data.chunks`: Array of relevant document chunks
  - `chunk_id`: Unique identifier
  - `content`: Actual text content
  - `similarity`: Relevance score (0-1, higher = better)
  - `document_keyword`: Document name/identifier
  - `dataset_id`: Which dataset the chunk came from

## 💡 Best Practices

1. **Always search before answering** factual questions
2. **Use the most relevant chunks** to construct answers
3. **Cite sources** by mentioning document names
4. **Handle no results gracefully** - suggest rephrasing or broader terms
5. **For Chinese content**, use original Chinese text in queries

## 📝 Example Workflow

**User Query**: "What is the remote work policy?"

**Step 1**: Search the knowledge base
```bash
# Execute curl command with the user's query
```

**Step 2**: Parse the JSON response
```bash
# Use jq or parse JSON to extract chunks
```

**Step 3**: Format results for the user
```
Found 3 relevant documents:

1. [Employee Handbook] (Similarity: 92%)
   Employees may work remotely up to 3 days per week...

2. [Remote Work Policy] (Similarity: 87%)
   Remote work requires manager approval...

3. [HR Guidelines 2024] (Similarity: 76%)
   Remote work eligibility criteria...
```

**Step 4**: Construct the answer using retrieved content

## 🚨 Troubleshooting

### Connection Failed
- **Symptom**: `curl: (7) Failed to connect` or `fetch failed`
- **Solution**:
  1. Check RAGFlow is running: `curl ${RAGFLOW_API_URL}`
  2. Verify the URL is correct
  3. Check firewall settings

### No Results Found
- **Symptom**: Empty chunks array
- **Solution**:
  1. Try different keywords
  2. Increase `top_k` parameter
  3. Check if datasets contain documents
  4. Verify documents are parsed in RAGFlow

### API Key Invalid
- **Symptom**: `401 Unauthorized` or `403 Forbidden`
- **Solution**:
  1. Regenerate API key in RAGFlow console
  2. Update environment variable
  3. Restart OpenClaw gateway

## 🔗 Related Resources

- RAGFlow Documentation: https://ragflow.io/docs
- RAGFlow API Reference: https://ragflow.io/docs/dev/http_api_reference
- OpenClaw Skills Guide: https://docs.openclaw.ai/tools/creating-skills

## 📄 License

MIT License - Feel free to use and modify!
