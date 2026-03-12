#!/bin/bash
# RAGFlow Datasets Manager
# Usage: ./datasets.sh [list|info] [dataset_id]

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env file if exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    # Source only simple variables, skip JSON arrays
    eval "$(grep -E '^[A-Z_]+=' "$SCRIPT_DIR/.env" | grep -v '\[' | sed 's/^/export /')"
fi

# Configuration with defaults
RAGFLOW_API_URL="${RAGFLOW_API_URL:-http://127.0.0.1}"
RAGFLOW_API_KEY="${RAGFLOW_API_KEY:-}"

# Check if API key is set
if [ -z "$RAGFLOW_API_KEY" ] || [ "$RAGFLOW_API_KEY" = "ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "❌ Error: RAGFLOW_API_KEY not set!"
    echo ""
    echo "Please set your RAGFlow API key:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Fill in your RAGFLOW_API_KEY"
    echo "  3. Run this script again"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Command: list
list_datasets() {
    echo -e "${BLUE}📚 Fetching RAGFlow datasets...${NC}"
    echo ""

    RESPONSE=$(curl -s -X GET "${RAGFLOW_API_URL}/api/v1/datasets" \
        -H "Authorization: Bearer ${RAGFLOW_API_KEY}" 2>&1)

    # Check for curl errors
    if [[ $RESPONSE == *"curl"* ]] || [[ $RESPONSE == *"Failed to connect"* ]]; then
        echo -e "${YELLOW}⚠️  Connection Error${NC}"
        echo "Could not connect to RAGFlow at: ${RAGFLOW_API_URL}"
        exit 1
    fi

    # Parse response
    DATASET_COUNT=$(echo "$RESPONSE" | jq -r 'if .code == 0 then .data | length else 0 end')

    if [ "$DATASET_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No datasets found${NC}"
        echo ""
        echo "Possible reasons:"
        echo "  1. No datasets created in RAGFlow"
        echo "  2. Invalid API key"
        echo "  3. API permissions issue"
        exit 0
    fi

    echo -e "${GREEN}✓ Found ${DATASET_COUNT} dataset(s):${NC}"
    echo ""

    # Display datasets
    echo "$RESPONSE" | jq -r '.data[] |
        "📁 \(.name)\n" +
        "   ID: \(.id)\n" +
        "   Description: \(.description // "No description")\n" +
        "   Chunk Count: \(.chunk_num // 0) chunks\n" +
        "   Created: \(.created_at // "Unknown")\n" +
        "   ───────────────────────────────────────"'
}

# Command: info
dataset_info() {
    local DATASET_ID="$1"

    if [ -z "$DATASET_ID" ]; then
        echo "❌ Error: Dataset ID is required"
        echo ""
        echo "Usage: $0 info <dataset_id>"
        echo ""
        echo "Example: $0 info 8b29e240dc8611f0b88e02bd655462b6"
        exit 1
    fi

    echo -e "${BLUE}🔍 Fetching dataset info...${NC}"
    echo -e "${CYAN}Dataset ID: ${YELLOW}${DATASET_ID}${NC}"
    echo ""

    # Get all datasets first
    RESPONSE=$(curl -s -X GET "${RAGFLOW_API_URL}/api/v1/datasets" \
        -H "Authorization: Bearer ${RAGFLOW_API_KEY}" 2>&1)

    # Find the specific dataset
    DATASET_INFO=$(echo "$RESPONSE" | jq -r --arg DID "$DATASET_ID" '.data[] | select(.id == $DID)')

    if [ -z "$DATASET_INFO" ] || [ "$DATASET_INFO" = "null" ]; then
        echo -e "${YELLOW}⚠️  Dataset not found: ${DATASET_ID}${NC}"
        echo ""
        echo "To list all available datasets, run:"
        echo "  $0 list"
        exit 1
    fi

    # Display dataset info
    echo -e "${GREEN}✓ Dataset Details:${NC}"
    echo ""
    echo "$DATASET_INFO" | jq -r '
        "📁 Name: \(.name)\n" +
        "🆔 ID: \(.id)\n" +
        "📝 Description: \(.description // "No description")\n" +
        "📊 Chunk Count: \(.chunk_num // 0) chunks\n" +
        "📅 Created: \(.created_at // "Unknown")\n" +
        "🔑 Permission: \(.permission // "Unknown")\n"
    '

    # Display chunk count in color
    CHUNK_NUM=$(echo "$DATASET_INFO" | jq -r '.chunk_num // 0')
    if [ "$CHUNK_NUM" -gt 0 ]; then
        echo -e "${GREEN}  ✓ Dataset has ${CHUNK_NUM} document chunks${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Dataset is empty (no chunks)${NC}"
    fi
}

# Main
case "${1:-list}" in
    list)
        list_datasets
        ;;
    info)
        dataset_info "$2"
        ;;
    help|--help|-h)
        echo "RAGFlow Datasets Manager"
        echo ""
        echo "Usage: $0 [command] [arguments]"
        echo ""
        echo "Commands:"
        echo "  list              List all datasets (default)"
        echo "  info <dataset_id>  Show detailed information about a dataset"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 info 8b29e240dc8611f0b88e02bd655462b6"
        echo ""
        ;;
    *)
        echo -e "${YELLOW}⚠️  Unknown command: $1${NC}"
        echo ""
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
