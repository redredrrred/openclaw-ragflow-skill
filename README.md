# OpenClaw RAGFlow Knowledge Skill

🔍 **Connect OpenClaw AI to RAGFlow knowledge bases** for intelligent document retrieval and Q&A.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-orange.svg)

## ✨ Features

- 🔍 **Smart Search**: Search across multiple RAGFlow datasets
- 📚 **Dataset Management**: List and inspect available datasets
- 🎯 **High Accuracy**: Vector similarity + keyword matching
- 🌏 **Multi-Language**: Supports Chinese and English content
- ⚡ **Fast**: Direct API calls without overhead
- 🛠️ **Easy Setup**: Just configure environment variables
- 📊 **Detailed Info**: Get dataset statistics and metadata

## 📋 Prerequisites

1. **OpenClaw** installed and running
2. **RAGFlow** server running (local or remote)
3. **RAGFlow API Key** from your RAGFlow console

## 🚀 Quick Start

### 1. Install This Skill

```bash
# Clone or download this repository
git clone https://github.com/redredrrred/openclaw-ragflow-skill.git
cd openclaw-ragflow-skill

# Copy to OpenClaw skills directory
cp -r SKILL.md ~/.openclaw/workspace/skills/ragflow-knowledge/
```

### 2. Configure RAGFlow Access

Create/Edit `~/.openclaw/workspace/skills/ragflow-knowledge/.env`:

```bash
RAGFLOW_API_URL=http://127.0.0.1
RAGFLOW_API_KEY=ragflow-your-api-key-here
RAGFLOW_DATASET_IDS=["dataset-id-1", "dataset-id-2"]
```

Or set as environment variables:

```bash
export RAGFLOW_API_URL="http://127.0.0.1"
export RAGFLOW_API_KEY="ragflow-your-api-key-here"
```

### 3. Refresh OpenClaw

```bash
# Restart OpenClaw gateway
openclaw restart

# Or ask AI to "refresh skills" in chat
```

### 4. Start Using!

Just chat with OpenClaw:

```
You: What's our company's remote work policy?
AI: [Searches RAGFlow knowledge base and answers with sources]
```

## 📖 Usage Examples

### Example 1: Policy Questions

```
User: What is the vacation policy?
AI: According to the Employee Handbook, full-time employees are entitled to...
     Source: Employee Handbook 2024 (Similarity: 94%)
```

### Example 2: Technical Documentation

```
User: How do I configure the API gateway?
AI: Based on the Technical Documentation, here are the steps...
     Source: API Setup Guide (Similarity: 89%)
```

### Example 3: Product Information

```
User: What are the specifications of Product X?
AI: According to the Product Catalog, Product X has...
     Source: Product Specs (Similarity: 91%)
```

### Example 4: Listing Datasets

```
User: What datasets do you have?
AI: [Lists all available RAGFlow datasets]
     Found 6 datasets:
     - 醉清风 (1,234 chunks)
     - 杜克采购文档 (567 chunks)
     - ...
```

### Example 5: Dataset Details

```
User: Tell me about the "醉清风" dataset
AI: [Shows detailed information]
     Dataset: 醉清风
     ID: 8b29e240dc8611f0b88e02bd655462b6
     Chunks: 1,234
     Created: 2026-03-10
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAGFLOW_API_URL` | ✅ Yes | - | RAGFlow server URL (e.g., `http://127.0.0.1`) |
| `RAGFLOW_API_KEY` | ✅ Yes | - | Your RAGFlow API key |
| `RAGFLOW_DATASET_IDS` | ❌ No | `[]` (all) | Comma-separated dataset IDs to search |
| `RAGFLOW_TOP_K` | ❌ No | `5` | Maximum results to return |

### Getting Your RAGFlow API Key

1. Open RAGFlow web console (usually `http://localhost`)
2. Go to **Profile → API**
3. Copy your API key
4. Use it in the configuration above

### Finding Dataset IDs

```bash
curl http://127.0.0.1/api/v1/datasets \
  -H "Authorization: Bearer YOUR_API_KEY" | jq '.data[].id'
```

## 🔧 Manual Testing

Test the skill directly without OpenClaw:

```bash
# Search knowledge base
cd ~/.openclaw/workspace/skills/ragflow-knowledge
./search.sh "your search query"

# List all datasets (bash version - requires jq)
./datasets.sh list

# List all datasets (Python version - cross-platform)
python datasets.py list

# Get dataset details (bash version - requires jq)
./datasets.sh info 8b29e240dc8611f0b88e02bd655462b6

# Get dataset details (Python version - cross-platform)
python datasets.py info 8b29e240dc8611f0b88e02bd655462b6

# Or using curl directly
curl -X POST "http://127.0.0.1/api/v1/retrieval" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "your search query",
    "top_k": 5
  }' | jq
```

## 📁 File Structure

```
~/.openclaw/workspace/skills/ragflow-knowledge/
├── SKILL.md          # Main skill definition (AI reads this)
├── search.sh         # Helper script for manual testing
├── .env              # Your local configuration (don't commit!)
└── README.md         # This file
```

## 🆚 Skill vs Plugin

### Use This Skill If You Want:
- ✅ Quick setup without compilation
- ✅ Easy to modify and customize
- ✅ Manual control over when to search
- ✅ Lightweight solution

### Use the Plugin If You Want:
- ✅ Automatic context injection before every message
- ✅ CLI commands (`openclaw ragflow search`)
- ✅ Advanced error handling and retry logic
- ✅ Health monitoring

**Pro Tip**: You can use both! The plugin for production, the skill for testing.

## 🐛 Troubleshooting

### Skill Not Found

```bash
# Check if skill directory exists
ls -la ~/.openclaw/workspace/skills/ragflow-knowledge/

# Restart OpenClaw
openclaw restart
```

### RAGFlow Connection Failed

```bash
# Check if RAGFlow is running
curl http://127.0.0.1

# Check API key
curl http://127.0.0.1/api/v1/datasets \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### No Results Returned

- Lower the similarity threshold
- Increase `top_k` parameter
- Check if documents are uploaded to RAGFlow
- Verify documents are parsed successfully

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **RAGFlow**: https://ragflow.io
- **RAGFlow Docs**: https://ragflow.io/docs
- **OpenClaw**: https://openclaw.ai
- **Plugin Version**: https://github.com/redredrrred/openclaw-ragflow

## ⭐ Star This Repository!

If you find this skill useful, please give it a star!

---

Made with ❤️ by [redredrrred](https://github.com/redredrrred)
