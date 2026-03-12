#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow Memory Management (Python version - no jq dependency)
Usage: python memory.py [command] [options]
"""

import os
import sys
import json
import urllib.request
from urllib.parse import urlencode
import io

# Fix Windows UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

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

def api_request(url, api_key, method='GET', body=None):
    """Make API request to RAGFlow"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        elif method == 'POST':
            data = json.dumps(body).encode('utf-8') if body else None
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        elif method == 'PUT':
            data = json.dumps(body).encode('utf-8') if body else None
            req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        elif method == 'DELETE':
            req = urllib.request.Request(url, headers=headers, method='DELETE')
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'data': [], 'message': str(e)}
    except Exception as e:
        return {'code': -1, 'data': [], 'error': str(e)}

def list_memories(env, keywords='', memory_type='', page=1, page_size=50):
    """List all memories"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key:
        print("[Error] RAGFLOW_API_KEY not set!")
        sys.exit(1)

    print(f"[List] Fetching memories from {api_url}...\n")

    params = {'page': page, 'page_size': page_size}
    if keywords:
        params['keywords'] = keywords
    if memory_type:
        params['memory_type'] = memory_type

    query_string = urlencode(params)
    url = f"{api_url}/api/v1/memories?{query_string}"

    result = api_request(url, api_key)

    if result.get('code') != 0:
        print(f"[Error] API Error: {result.get('code', 'unknown')}")
        if 'error' in result:
            print(f"   {result['error']}")
        return

    data = result.get('data', {})
    memories = data.get('memory_list', [])
    total = data.get('total_count', 0)

    if not memories:
        print("[Warning] No memories found")
        return

    print(f"[OK] Found {total} memory(s):\n")

    for mem in memories:
        print(f"[ID] {mem.get('id', 'N/A')}")
        print(f"[Name] {mem.get('name', 'Unknown')}")
        print(f"[Type] {', '.join(mem.get('memory_type', []))}")
        print(f"[Size] {mem.get('memory_size', 0)} bytes")
        print(f"[Owner] {mem.get('owner_name', 'Unknown')}")
        desc = mem.get('description')
        if desc:
            print(f"[Desc] {desc}")
        print("   ───────────────────────────────────────")

def create_memory(env, name, memory_type, embd_id, llm_id):
    """Create a new memory"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Create] Creating memory: {name}")

    body = {
        'name': name,
        'memory_type': [memory_type],
        'embd_id': embd_id,
        'llm_id': llm_id
    }

    url = f"{api_url}/api/v1/memories"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') == 0:
        print("[OK] Memory created successfully!")
        print(json.dumps(result.get('data', {}), indent=2, ensure_ascii=False))
    else:
        print("[Error] Failed to create memory")
        print(f"   Code: {result.get('code')}")
        print(f"   Message: {result.get('message', 'Unknown error')}")

def get_memory_config(env, memory_id):
    """Get memory configuration"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Config] Getting configuration for: {memory_id}")

    url = f"{api_url}/api/v1/memories/{memory_id}/config"
    result = api_request(url, api_key)

    if result.get('code') == 0:
        print("[OK] Memory configuration:")
        print(json.dumps(result.get('data', {}), indent=2, ensure_ascii=False))
    else:
        print("[Error] Failed to get configuration")
        print(f"   Code: {result.get('code')}")
        print(f"   Message: {result.get('message', 'Unknown error')}")

def get_messages(env, memory_id, agent_id='', keywords='', page=1, page_size=50):
    """Get messages from memory"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Messages] Getting messages from: {memory_id}")

    params = {'page': page, 'page_size': page_size}
    if agent_id:
        params['agent_id'] = agent_id
    if keywords:
        params['keywords'] = keywords

    query_string = urlencode(params)
    url = f"{api_url}/api/v1/memories/{memory_id}?{query_string}"

    result = api_request(url, api_key)

    if result.get('code') == 0:
        data = result.get('data', {})
        messages = data.get('messages', {})
        message_list = messages.get('message_list', [])
        total = messages.get('total_count', len(message_list))

        print(f"[OK] Found {total} message(s):\n")

        for msg in message_list:
            print(f"[Msg] ID: {msg.get('message_id')}")
            print(f"[Agent] {msg.get('agent_name', 'Unknown')}")
            print(f"[Session] {msg.get('session_id', 'N/A')}")
            print(f"[Status] {'Active' if msg.get('status') else 'Inactive'}")
            print(f"[Type] {msg.get('message_type', 'N/A')}")

            # Show task info if available
            task = msg.get('task', {})
            if task:
                progress = task.get('progress', 0)
                progress_msg = task.get('progress_msg', '')
                print(f"[Task] Progress: {progress*100:.0f}%")
                if progress_msg:
                    print(f"[Task] {progress_msg.strip()}")

            print("   ───────────────────────────────────────")
    else:
        print("[Error] Failed to get messages")
        print(f"   Code: {result.get('code')}")
        print(f"   Message: {result.get('message', 'Unknown error')}")

def search_messages(env, memory_id, query, threshold=0.2, keyword_weight=0.7, top_n=5, agent_id='', session_id=''):
    """Search messages in memory"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Search] Searching in {memory_id}")
    print(f"[Search] Query: {query}\n")

    params = {
        'memory_id': memory_id,
        'query': query,
        'similarity_threshold': threshold,
        'keywords_similarity_weight': keyword_weight,
        'top_n': top_n
    }
    if agent_id:
        params['agent_id'] = agent_id
    if session_id:
        params['session_id'] = session_id

    query_string = urlencode(params)
    url = f"{api_url}/api/v1/messages/search?{query_string}"

    result = api_request(url, api_key)

    if result.get('code') == 0:
        data = result.get('data', {})
        print("[OK] Search results:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("[Error] Search failed")
        print(f"   Code: {result.get('code')}")
        print(f"   Message: {result.get('message', 'Unknown error')}")

def delete_memory(env, memory_id):
    """Delete a memory"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"[Delete] Deleting memory: {memory_id}")

    url = f"{api_url}/api/v1/memories/{memory_id}"
    result = api_request(url, api_key, method='DELETE')

    if result.get('code') == 0:
        print("[OK] Memory deleted successfully!")
    else:
        print("[Error] Failed to delete memory")
        print(f"   Code: {result.get('code')}")
        print(f"   Message: {result.get('message', 'Unknown error')}")

def main():
    env = load_env()

    if len(sys.argv) < 2:
        print("RAGFlow Memory Management (Python version)")
        print("\nUsage: python memory.py [command] [options]")
        print("\nCommands:")
        print("  list [options]              List all memories")
        print("  create <name> <type> <embd_id> <llm_id>  Create memory")
        print("  config <memory_id>          Get memory configuration")
        print("  messages <memory_id> [options]  Get messages")
        print("  search <memory_id> <query>  Search messages")
        print("  delete <memory_id>          Delete memory")
        print("\nMemory types: longtime, user, agent, session")
        print("\nExamples:")
        print("  python memory.py list")
        print("  python memory.py config 3dc4b79cf5e411f0890ecbabf5d804da")
        print("  python memory.py messages 3dc4b79cf5e411f0890ecbabf5d804da")
        print("  python memory.py search 3dc4b79cf5e411f0890ecbabf5d804da 'test query'")
        return

    command = sys.argv[1].lower()

    if command == 'list':
        keywords = ''
        memory_type = ''
        page = 1

        for i in range(2, len(sys.argv)):
            if sys.argv[i] == '--keywords' and i + 1 < len(sys.argv):
                keywords = sys.argv[i + 1]
            elif sys.argv[i] == '--type' and i + 1 < len(sys.argv):
                memory_type = sys.argv[i + 1]

        list_memories(env, keywords, memory_type, page)

    elif command == 'create':
        if len(sys.argv) < 6:
            print("[Error] Usage: python memory.py create <name> <type> <embd_id> <llm_id>")
            sys.exit(1)
        create_memory(env, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    elif command == 'config':
        if len(sys.argv) < 3:
            print("[Error] Usage: python memory.py config <memory_id>")
            sys.exit(1)
        get_memory_config(env, sys.argv[2])

    elif command == 'messages':
        if len(sys.argv) < 3:
            print("[Error] Usage: python memory.py messages <memory_id>")
            sys.exit(1)
        get_messages(env, sys.argv[2])

    elif command == 'search':
        if len(sys.argv) < 4:
            print("[Error] Usage: python memory.py search <memory_id> <query>")
            sys.exit(1)
        search_messages(env, sys.argv[2], sys.argv[3])

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("[Error] Usage: python memory.py delete <memory_id>")
            sys.exit(1)
        delete_memory(env, sys.argv[2])

    else:
        print(f"[Error] Unknown command: {command}")

if __name__ == '__main__':
    main()