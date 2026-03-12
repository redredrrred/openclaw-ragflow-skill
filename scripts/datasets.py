#!/usr/bin/env python3
"""
RAGFlow Datasets Manager
Usage: python datasets.py [list|info] [dataset_id]
"""

import os
import sys
import json
import urllib.request

def load_env():
    """Load .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_file):
        return {}

    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line and not line.startswith('export'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

def api_request(url, api_key):
    """Make API request to RAGFlow"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'data': []}
    except Exception as e:
        return {'code': -1, 'data': [], 'error': str(e)}

def list_datasets():
    """List all datasets"""
    env = load_env()
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key or api_key == 'ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx':
        print("[Error] Error: RAGFLOW_API_KEY not set!")
        print("\nPlease set your RAGFlow API key in .env file")
        sys.exit(1)

    print(f"[List] Fetching RAGFlow datasets from {api_url}...\n")

    url = f"{api_url}/api/v1/datasets"
    result = api_request(url, api_key)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        if 'error' in result:
            print(f"   {result['error']}")
        sys.exit(1)

    datasets = result.get('data', [])

    if not datasets:
        print("[Warning]️  No datasets found\n")
        print("Possible reasons:")
        print("  1. No datasets created in RAGFlow")
        print("  2. Invalid API key")
        print("  3. API permissions issue")
        sys.exit(0)

    print(f"[OK] Found {len(datasets)} dataset(s):\n")

    for ds in datasets:
        print(f"[Dir] {ds.get('name', 'Unknown')}")
        print(f"   ID: {ds.get('id', 'N/A')}")
        print(f"   Description: {ds.get('description', 'No description')}")
        print(f"   Chunk Count: {ds.get('chunk_count', 0)} chunks")
        print(f"   Created: {ds.get('created_at', 'Unknown')}")
        print("   ───────────────────────────────────────")

def dataset_info(dataset_id):
    """Get dataset details"""
    env = load_env()
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key or api_key == 'ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx':
        print("[Error] Error: RAGFLOW_API_KEY not set!")
        sys.exit(1)

    print(f"[Search] Fetching dataset info...")
    print(f"Dataset ID: {dataset_id}\n")

    url = f"{api_url}/api/v1/datasets"
    result = api_request(url, api_key)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        sys.exit(1)

    datasets = result.get('data', [])
    dataset = None

    for ds in datasets:
        if ds.get('id') == dataset_id:
            dataset = ds
            break

    if not dataset:
        print(f"[Warning]️  Dataset not found: {dataset_id}\n")
        print("To list all available datasets, run:")
        print("  python datasets.py list")
        sys.exit(1)

    print("[OK] Dataset Details:\n")
    print(f"[Dir] Name: {dataset.get('name', 'Unknown')}")
    print(f"[ID] ID: {dataset.get('id', 'N/A')}")
    print(f"[Desc] Description: {dataset.get('description', 'No description')}")
    print(f"[Count] Chunk Count: {dataset.get('chunk_count', 0)} chunks")
    print(f"[Date] Created: {dataset.get('created_at', 'Unknown')}")
    print(f"[Key] Permission: {dataset.get('permission', 'Unknown')}")

    chunk_count = dataset.get('chunk_count', 0)
    if chunk_count > 0:
        print(f"\n[OK] Dataset has {chunk_count} document chunks")
    else:
        print("\n[Warning]️  Dataset is empty (no chunks)")

def main():
    if len(sys.argv) < 2:
        list_datasets()
        return

    command = sys.argv[1].lower()

    if command == 'list':
        list_datasets()
    elif command == 'info':
        if len(sys.argv) < 3:
            print("[Error] Error: Dataset ID is required")
            print("\nUsage: python datasets.py info <dataset_id>")
            print("\nExample: python datasets.py info 8b29e240dc8611f0b88e02bd655462b6")
            sys.exit(1)
        dataset_info(sys.argv[2])
    elif command in ['help', '--help', '-h']:
        print("RAGFlow Datasets Manager")
        print("\nUsage: python datasets.py [command] [arguments]")
        print("\nCommands:")
        print("  list              List all datasets (default)")
        print("  info <dataset_id>  Show detailed information about a dataset")
        print("  help              Show this help message")
        print("\nExamples:")
        print("  python datasets.py list")
        print("  python datasets.py info 8b29e240dc8611f0b88e02bd655462b6")
    else:
        print(f"[Warning]️  Unknown command: {command}")
        print("\nRun 'python datasets.py help' for usage information")
        sys.exit(1)

if __name__ == '__main__':
    main()
