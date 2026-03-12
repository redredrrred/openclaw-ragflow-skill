#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow Search Diagnosis Tool
Diagnose why certain content is not appearing in search results
"""

import os
import sys
import json
import urllib.request
import io

# Fix Windows UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import load_env, api_request

def diagnose_search(env, query):
    """Diagnose search issues"""
    api_url = env.get('RAGFLOW_API_URL', 'http://127.0.0.1')
    api_key = env.get('RAGFLOW_API_KEY', '')

    print(f"\n{'='*60}")
    print(f"RAGFlow 搜索诊断工具")
    print(f"{'='*60}\n")

    # 1. Check connection
    print("[1/5] 检查 API 连接...")
    url = f"{api_url}/api/v1/datasets"
    result = api_request(url, api_key)
    if result.get('code') == 0:
        print(f"    ✅ 连接成功: {api_url}")
    else:
        print(f"    ❌ 连接失败: {result.get('message', 'Unknown error')}")
        return

    # 2. List datasets
    print("\n[2/5] 列出所有数据集...")
    datasets = result.get('data', [])
    if not datasets:
        print("    ⚠️  没有找到数据集")
        return

    print(f"    找到 {len(datasets)} 个数据集:")
    for ds in datasets:
        ds_id = ds.get('id', 'N/A')
        ds_name = ds.get('name', 'N/A')
        chunk_count = ds.get('chunk_num', ds.get('chunk_count', 0))
        print(f"      - {ds_name} ({ds_id})")
        print(f"        Chunks: {chunk_count}")

    # 3. Search with different thresholds
    print(f"\n[3/5] 使用不同阈值搜索: '{query}'")

    dataset_ids = env.get('RAGFLOW_DATASET_IDS', '[]')
    if dataset_ids and dataset_ids != '[]':
        dataset_ids = json.loads(dataset_ids)
    else:
        dataset_ids = [ds.get('id') for ds in datasets]

    for threshold in [0.0, 0.1, 0.2, 0.3]:
        body = {
            'question': query,
            'dataset_ids': dataset_ids,
            'similarity_threshold': threshold,
            'top_k': 30
        }
        url = f"{api_url}/api/v1/retrieval"
        result = api_request(url, api_key, method='POST', body=body)
        chunks = result.get('data', {}).get('chunks', [])
        print(f"    Threshold={threshold}: 找到 {len(chunks)} 个结果")

    # 4. Detailed search with threshold 0.0
    print(f"\n[4/5] 详细分析搜索结果 (threshold=0.0)...")
    body = {
        'question': query,
        'dataset_ids': dataset_ids,
        'similarity_threshold': 0.0,
        'top_k': 30
    }
    url = f"{api_url}/api/v1/retrieval"
    result = api_request(url, api_key, method='POST', body=body)

    if result.get('code') != 0:
        print(f"    ❌ API 错误: {result.get('message', 'Unknown')}")
        return

    chunks = result.get('data', {}).get('chunks', [])

    if not chunks:
        print("    ⚠️  没有找到任何结果")
        print("\n    可能的原因:")
        print("      1. 该内容没有被索引到任何数据集")
        print("      2. 文档正在处理中（chunking）")
        print("      3. 文档上传失败")
    else:
        print(f"    找到 {len(chunks)} 个结果:\n")

        # Group by document
        by_doc = {}
        for chunk in chunks:
            doc_id = chunk.get('doc_id', 'unknown')
            if doc_id not in by_doc:
                by_doc[doc_id] = []
            by_doc[doc_id].append(chunk)

        for doc_id, doc_chunks in by_doc.items():
            print(f"    📄 文档: {doc_id}")
            for i, chunk in enumerate(doc_chunks[:3], 1):  # Show first 3
                similarity = chunk.get('similarity', 0) * 100
                content = chunk.get('content', '')[:100]
                available = chunk.get('available_int', 1)
                status = "✅" if available else "❌ 禁用"
                print(f"      [{i}] 相似度: {similarity:.1f}% {status}")
                print(f"          内容: {content}...")
            if len(doc_chunks) > 3:
                print(f"      ... 还有 {len(doc_chunks) - 3} 个 chunks")
            print()

    # 5. Check document aggregation
    print("[5/5] 文档聚合统计...")
    doc_aggs = result.get('data', {}).get('doc_aggs', [])
    if doc_aggs:
        print(f"    结果分布在 {len(doc_aggs)} 个文档中:")
        for agg in doc_aggs:
            print(f"      - {agg.get('doc_name', 'Unknown')}: {agg.get('count', 0)} 个 chunks")

    print(f"\n{'='*60}")
    print("诊断完成")
    print(f"{'='*60}\n")

    # Recommendations
    if not chunks:
        print("💡 建议:")
        print("  1. 检查 RAGFlow 控制台，确认文档已成功上传")
        print("  2. 查看文档的 parsing 状态是否完成")
        print("  3. 尝试重新上传相关文档")
        print("  4. 使用不同的关键词搜索")
    else:
        low_similarity = [c for c in chunks if c.get('similarity', 0) < 0.2]
        if low_similarity:
            print(f"💡 注意: {len(low_similarity)} 个结果相似度 < 20%")
            print("   建议: 使用 --threshold 0.1 或 0.0 获取更多结果")

def main():
    env = load_env()

    if not env.get('RAGFLOW_API_KEY'):
        print("Error: RAGFLOW_API_KEY not set!")
        print("\n请配置 .env 文件:")
        print("  RAGFLOW_API_URL=http://127.0.0.1")
        print("  RAGFLOW_API_KEY=ragflow-xxxxx")
        sys.exit(1)

    query = sys.argv[1] if len(sys.argv) > 1 else "memory"
    diagnose_search(env, query)

if __name__ == '__main__':
    main()
