#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow Knowledge Search (Python version - no jq dependency)
Usage: python search.py [OPTIONS] "<search query>"
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from urllib.parse import urlencode
import io

# Fix Windows UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_env():
    """Load .env file from parent directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Look in parent directory
    env_file = os.path.join(script_dir, '..', '.env')

    # Fallback to openclaw workspace
    if not os.path.exists(env_file):
        openclaw_env = os.path.expanduser('~/.openclaw/workspace/skills/ragflow-knowledge/.env')
        if os.path.exists(openclaw_env):
            env_file = openclaw_env

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
                # Parse JSON arrays properly
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    try:
                        env_vars[key.strip()] = json.loads(value)
                    except:
                        env_vars[key.strip()] = value
                else:
                    env_vars[key.strip()] = value

    return env_vars

def api_request(url, api_key, body=None):
    """Make POST API request to RAGFlow"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'data': [], 'message': str(e)}
    except Exception as e:
        return {'code': -1, 'data': [], 'error': str(e)}

def search(env, query, dataset_ids=None, top_k=5, similarity_threshold=0.2,
          vector_similarity_weight=None, page=1, size=30, doc_ids=None,
          keyword=False, use_kg=False, rerank_id=None, search_id=None,
          use_retrieval_test=False, kb_id=None):
    """Search RAGFlow knowledge base"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key:
        print("[Error] RAGFLOW_API_KEY not set!")
        sys.exit(1)

    # Determine which API to use
    if use_retrieval_test:
        api_endpoint = f"{api_url}/api/v1/chunk/retrieval_test"
        if not kb_id:
            # Try to use first dataset_id
            if dataset_ids and len(dataset_ids) > 0:
                kb_id = dataset_ids[0]
            else:
                print("[Error] --kb-id is required for retrieval_test")
                sys.exit(1)
        body = {
            'kb_id': kb_id,
            'question': query,
            'page': page,
            'size': size
        }
        similarity_threshold = similarity_threshold or 0.0
    else:
        api_endpoint = f"{api_url}/api/v1/retrieval"
        if not dataset_ids:
            default_ids = env.get('RAGFLOW_DATASET_IDS', '[]')
            dataset_ids = json.loads(default_ids) if default_ids else []

        body = {
            'question': query
        }
        if dataset_ids:
            body['dataset_ids'] = dataset_ids

    # Add optional parameters
    body['top_k'] = top_k
    body['similarity_threshold'] = similarity_threshold
    body['page'] = page
    body['size'] = size

    if vector_similarity_weight is not None:
        body['vector_similarity_weight'] = vector_similarity_weight
    if doc_ids:
        body['doc_ids'] = doc_ids
    if keyword:
        body['keyword'] = True
    if use_kg:
        body['use_kg'] = True
    if rerank_id:
        body['rerank_id'] = rerank_id
    if search_id:
        body['search_id'] = search_id

    print(f"[Search] Query: {query}")
    if use_retrieval_test:
        print(f"[Search] Using: retrieval_test API (requires login)")
        print(f"[Search] KB ID: {kb_id}")

    result = api_request(api_endpoint, api_key, body)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        if 'error' in result:
            print(f"   {result['error']}")
        if 'message' in result:
            print(f"   {result['message']}")
        return

    chunks = result.get('data', {}).get('chunks', [])

    if not chunks:
        print("[Result] No results found")
        return

    print(f"\n[Result] Found {len(chunks)} result(s):\n")

    for i, chunk in enumerate(chunks, 1):
        similarity = chunk.get('similarity', 0) * 100
        doc = chunk.get('document_keyword', chunk.get('docnm_kwd', 'Unknown'))
        content = chunk.get('content', '')[:200]

        print(f"[{i}] {doc}")
        print(f"    Similarity: {similarity:.0f}%")
        print(f"    Content: {content}...")
        print()

def main():
    env = load_env()

    if len(sys.argv) < 2:
        print("RAGFlow Knowledge Search (Python version)")
        print("\nUsage: python search.py [OPTIONS] \"<search query>\"")
        print("\nOptions:")
        print("  --top-k N               Maximum results (default: 5)")
        print("  --threshold N           Similarity 0-1 (default: 0.2)")
        print("  --vector-weight N       Vector weight 0-1 (default: 0.3)")
        print("  --dataset-ids \"id1,id2\"  Specific datasets")
        print("  --kb-id ID              Dataset for retrieval_test")
        print("  --doc-ids \"id1,id2\"      Limit to documents")
        print("  --keyword               Enable keyword extraction")
        print("  --use-kg                Use knowledge graph")
        print("  --retrieval-test         Use retrieval_test API")
        print("\nExamples:")
        print("  python search.py \"your query\"")
        print("  python search.py --top-k 10 --threshold 0.3 \"your query\"")
        print("  python search.py --retrieval-test --kb-id DATASET_ID \"query\"")
        return

    query = sys.argv[-1]
    dataset_ids = None
    top_k = 5
    similarity_threshold = 0.2
    vector_weight = None
    page = 1
    size = 30
    doc_ids = None
    keyword = False
    use_kg = False
    rerank_id = None
    search_id = None
    use_retrieval_test = False
    kb_id = None

    i = 1
    while i < len(sys.argv) - 1:
        arg = sys.argv[i]
        if arg == '--top-k' and i + 1 < len(sys.argv):
            top_k = int(sys.argv[i + 1])
            i += 2
        elif arg == '--threshold' and i + 1 < len(sys.argv):
            similarity_threshold = float(sys.argv[i + 1])
            i += 2
        elif arg == '--vector-weight' and i + 1 < len(sys.argv):
            vector_weight = float(sys.argv[i + 1])
            i += 2
        elif arg == '--dataset-ids' and i + 1 < len(sys.argv):
            ids = sys.argv[i + 1].split(',')
            dataset_ids = ids
            i += 2
        elif arg == '--kb-id' and i + 1 < len(sys.argv):
            kb_id = sys.argv[i + 1]
            i += 2
        elif arg == '--doc-ids' and i + 1 < len(sys.argv):
            doc_ids = sys.argv[i + 1].split(',')
            i += 2
        elif arg == '--keyword':
            keyword = True
            i += 1
        elif arg == '--use-kg':
            use_kg = True
            i += 1
        elif arg == '--rerank' and i + 1 < len(sys.argv):
            rerank_id = sys.argv[i + 1]
            i += 2
        elif arg == '--search-id' and i + 1 < len(sys.argv):
            search_id = sys.argv[i + 1]
            i += 2
        elif arg == '--retrieval-test':
            use_retrieval_test = True
            i += 1
        else:
            i += 1

    search(env, query, dataset_ids, top_k, similarity_threshold, vector_weight,
          page, size, doc_ids, keyword, use_kg, rerank_id, search_id,
          use_retrieval_test, kb_id)

if __name__ == '__main__':
    main()
