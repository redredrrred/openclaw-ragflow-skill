#!/bin/bash
# OpenClaw RAGFlow Skill Installation Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   OpenClaw RAGFlow Skill Installer    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if OpenClaw is installed
if ! command -v openclaw &> /dev/null; then
    echo -e "${YELLOW}⚠️  OpenClaw not found!${NC}"
    echo ""
    echo "Please install OpenClaw first:"
    echo "  npm install -g openclaw"
    exit 1
fi

echo -e "${GREEN}✓ OpenClaw found${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Target directory
TARGET_DIR="$HOME/.openclaw/workspace/skills/ragflow-knowledge"

echo ""
echo "Installing to: $TARGET_DIR"
echo ""

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy files
echo "Copying files..."
cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/"
cp "$SCRIPT_DIR/search.sh" "$TARGET_DIR/"
cp "$SCRIPT_DIR/datasets.sh" "$TARGET_DIR/"
chmod +x "$TARGET_DIR/search.sh"
chmod +x "$TARGET_DIR/datasets.sh"

# Create .env if it doesn't exist
if [ ! -f "$TARGET_DIR/.env" ]; then
    echo "Creating .env configuration file..."
    cp "$SCRIPT_DIR/.env.example" "$TARGET_DIR/.env"
    echo -e "${YELLOW}⚠️  Please edit .env with your RAGFlow API credentials:${NC}"
    echo "   $TARGET_DIR/.env"
else
    echo -e "${GREEN}✓ .env already exists, skipping...${NC}"
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure your RAGFlow API credentials:"
echo -e "     ${YELLOW}nano $TARGET_DIR/.env${NC}"
echo ""
echo "  2. Restart OpenClaw:"
echo -e "     ${YELLOW}openclaw restart${NC}"
echo ""
echo "  3. Or ask AI to: ${YELLOW}\"refresh skills\"${NC}"
echo ""
echo "Testing:"
echo "  Test search:"
echo -e "     ${YELLOW}cd $TARGET_DIR && ./search.sh \"your query\"${NC}"
echo "  List datasets:"
echo -e "     ${YELLOW}cd $TARGET_DIR && ./datasets.sh list${NC}"
echo ""
echo -e "${GREEN}Happy searching! 🎉${NC}"
