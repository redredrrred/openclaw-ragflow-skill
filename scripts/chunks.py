#!/usr/bin/env python3
"""
RAGFlow Chunk Management (Python version - no jq dependency)
Usage: python chunks.py [command] [options]
"""

import os
import sys
import json
import urllib.request
import urllib.parse

def load_env():
    """Load .env file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, '..', '.env')

    if not os.path.exists(env_file):
        openclaw_env = os.path.expanduser('~/.openclaw/workspace/skills/openclaw-ragflow-skill/.env')
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
                if '[' in value:
                    continue
                env_vars[key.strip()] = value.strip()

    return env_vars

def api_request(url, api_key, method='GET', body=None):
    """Make API request to RAGFlow"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    if method == 'GET':
        req = urllib.request.Request(url, headers=headers)
    elif method == 'POST':
        data = json.dumps(body).encode('utf-8') if body else None
        req = urllib.request.Request(url, data=data, headers=headers)
    elif method == 'DELETE':
        req = urllib.request.Request(url, headers=headers, method='DELETE')
    else:
        raise ValueError(f"Unsupported method: {method}")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'data': [], 'message': str(e)}
    except Exception as e:
        return {'code': -1, 'data': [], 'error': str(e)}

def list_chunks(env, doc_id, page=1, size=30, keywords=''):
    """List chunks in a document"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key:
        print("[Error] RAGFLOW_API_KEY not set!")
        sys.exit(1)

    print(f"[List] Listing chunks for document: {doc_id}\n")

    body = {
        'doc_id': doc_id,
        'page': page,
        'size': size
    }
    if keywords:
        body['keywords'] = keywords

    url = f"{api_url}/api/v1/chunk/list"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        return

    data = result.get('data', {})
    chunks = data.get('chunks', [])
    total = data.get('total', 0)

    if not chunks:
        print("[Info] No chunks found")
        return

    print(f"[OK] Total: {total} chunk(s), showing {len(chunks)}:\n")

    for chunk in chunks:
        print(f"[Chunk] {chunk.get('chunk_id', 'N/A')}")
        print(f"[Content] {chunk.get('content_with_weight', 'N/A')[:100]}...")
        print(f"[Document] {chunk.get('docnm_kwd', 'N/A')}")
        print(f"[Available] {'Yes' if chunk.get('available_int', 1) else 'No'}")
        print()

def get_chunk(env, chunk_id):
    """Get chunk details"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Get] Getting chunk: {chunk_id}\n")

    url = f"{api_url}/api/v1/chunk/get?chunk_id={chunk_id}"
    result = api_request(url, api_key)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        return

    print("[OK] Chunk details:")
    print(json.dumps(result.get('data', {}), indent=2, ensure_ascii=False))

def create_chunk(env, doc_id, content, important_keywords=None, question_keywords=None):
    """Create a new chunk"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Create] Creating chunk in document: {doc_id}")

    body = {
        'doc_id': doc_id,
        'content_with_weight': content,
        'important_kwd': important_keywords or [],
        'question_kwd': question_keywords or []
    }

    url = f"{api_url}/api/v1/chunk/create"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') == 0:
        chunk_id = result.get('data', {}).get('chunk_id', 'unknown')
        print(f"[OK] Chunk created! ID: {chunk_id}")
    else:
        print("[Error] Failed to create chunk")
        print(f"   Code: {result.get('code')}")

def update_chunk(env, doc_id, chunk_id, content, important_keywords=None, available=1):
    """Update a chunk"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Update] Updating chunk: {chunk_id}")

    body = {
        'doc_id': doc_id,
        'chunk_id': chunk_id,
        'content_with_weight': content,
        'important_kwd': important_keywords or [],
        'available_int': available
    }

    url = f"{api_url}/api/v1/chunk/set"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') == 0:
        print("[OK] Chunk updated successfully!")
    else:
        print("[Error] Failed to update chunk")

def toggle_chunks(env, doc_id, chunk_ids, available=1):
    """Toggle chunk availability"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    action = "Enable" if available == 1 else "Disable"
    print(f"[{action}] {action}ing chunks in document: {doc_id}")

    if isinstance(chunk_ids, str):
        chunk_ids = chunk_ids.split(',')

    body = {
        'doc_id': doc_id,
        'chunk_ids': chunk_ids,
        'available_int': available
    }

    url = f"{api_url}/api/v1/chunk/switch"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') == 0:
        print(f"[OK] Chunks {action}ed successfully!")
    else:
        print(f"[Error] Failed to {action.lower()} chunks")

def delete_chunks(env, doc_id, chunk_ids):
    """Delete chunks"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Delete] Deleting chunks from document: {doc_id}")

    if isinstance(chunk_ids, str):
        chunk_ids = chunk_ids.split(',')

    body = {
        'doc_id': doc_id,
        'chunk_ids': chunk_ids
    }

    url = f"{api_url}/api/v1/chunk/rm"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') == 0:
        print("[OK] Chunks deleted successfully!")
    else:
        print("[Error] Failed to delete chunks")

def main():
    env = load_env()

    if len(sys.argv) < 2:
        print("RAGFlow Chunk Management (Python version)")
        print("\nUsage: python chunks.py [command] [options]")
        print("\nCommands:")
        print("  list <doc_id>              List chunks in document")
        print("  get <chunk_id>              Get chunk details")
        print("  create <doc_id> <content>   Create new chunk")
        print("  update <doc_id> <chunk_id> <content>  Update chunk")
        print("  enable <doc_id> <chunk_ids>   Enable chunks")
        print("  disable <doc_id> <chunk_ids>  Disable chunks")
        print("  delete <doc_id> <chunk_ids>   Delete chunks")
        print("\nExamples:")
        print("  python chunks.py list doc-id-123")
        print("  python chunks.py get chunk-id-456")
        print("  python chunks.py create doc-id-123 'content here'")
        print("  python chunks.py update doc-id-123 chunk-id-456 'new content'")
        print("  python chunks.py enable doc-id-123 chunk-id-1,chunk-id-2")
        print("  python chunks.py delete doc-id-123 chunk-id-1,chunk-id-2")
        return

    command = sys.argv[1].lower()

    if command == 'list':
        if len(sys.argv) < 3:
            print("[Error] doc_id is required")
            return
        list_chunks(env, sys.argv[2])

    elif command == 'get':
        if len(sys.argv) < 3:
            print("[Error] chunk_id is required")
            return
        get_chunk(env, sys.argv[2])

    elif command == 'create':
        if len(sys.argv) < 4:
            print("[Error] Usage: python chunks.py create <doc_id> <content>")
            return
        create_chunk(env, sys.argv[2], sys.argv[3])

    elif command == 'update':
        if len(sys.argv) < 5:
            print("[Error] Usage: python chunks.py update <doc_id> <chunk_id> <content>")
            return
        update_chunk(env, sys.argv[2], sys.argv[3], sys.argv[4])

    elif command == 'enable':
        if len(sys.argv) < 4:
            print("[Error] Usage: python chunks.py enable <doc_id> <chunk_ids>")
            return
        toggle_chunks(env, sys.argv[2], sys.argv[3], 1)

    elif command == 'disable':
        if len(sys.argv) < 4:
            print("[Error] Usage: python chunks.py disable <doc_id> <chunk_ids>")
            return
        toggle_chunks(env, sys.argv[2], sys.argv[3], 0)

    elif command == 'delete':
        if len(sys.argv) < 4:
            print("[Error] Usage: python chunks.py delete <doc_id> <chunk_ids>")
            return
        delete_chunks(env, sys.argv[2], sys.argv[3])

    else:
        print(f"[Error] Unknown command: {command}")

if __name__ == '__main__':
    main()
