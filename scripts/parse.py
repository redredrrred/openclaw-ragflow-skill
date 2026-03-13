#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start parsing uploaded RAGFlow documents in a dataset.
Usage: python scripts/parse.py <dataset_id> <doc_id1> [doc_id2 ...]
"""

import json
import os
import sys
from urllib import request, error
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_env():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, '..', '.env')
    if not os.path.exists(env_file):
        return {}

    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line or line.startswith('export'):
                continue
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    return env_vars


def start_parse(dataset_id, document_ids):
    env = load_env()
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1').rstrip('/')
    api_key = env.get('RAGFLOW_API_KEY', '')

    if not api_key:
        print('[Error] RAGFLOW_API_KEY not set in .env')
        return 1

    url = f'{api_url}/api/v1/datasets/{dataset_id}/chunks'
    body = json.dumps({'document_ids': document_ids}).encode('utf-8')
    req = request.Request(url, data=body, method='POST')
    req.add_header('Authorization', f'Bearer {api_key}')
    req.add_header('Content-Type', 'application/json')

    try:
        with request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode('utf-8'))
    except error.HTTPError as e:
        print(f'[Error] HTTP {e.code}: {e.reason}')
        try:
            print(e.read().decode('utf-8'))
        except Exception:
            pass
        return 1
    except Exception as e:
        print(f'[Error] Parse start failed: {e}')
        return 1

    if result.get('code') != 0:
        print(f"[Error] Parse start failed: {result.get('message', 'unknown error')}")
        return 1

    print(f'[OK] Parse started for dataset {dataset_id}')
    print(json.dumps({'dataset_id': dataset_id, 'document_ids': document_ids}, ensure_ascii=False))
    print('Parsing is asynchronous; check document status later.')
    print(f"Next: python scripts/parse_status.py {dataset_id} --doc-ids {','.join(document_ids)} --watch")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python scripts/parse.py <dataset_id> <doc_id1> [doc_id2 ...]')
        sys.exit(1)
    sys.exit(start_parse(sys.argv[1], sys.argv[2:]))
