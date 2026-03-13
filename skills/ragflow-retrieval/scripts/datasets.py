#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from typing import Any

from common import (
    DataError,
    ScriptError,
    configure_stdio_utf8,
    current_timestamp,
    ensure_success,
    format_json,
    load_repo_env,
    repo_root_from_path,
    request_json,
    require_api_key,
    resolve_base_url,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List or inspect RAGFlow datasets.")
    parser.add_argument("command", nargs="?", default="list", choices=("list", "info"), help="Command to run")
    parser.add_argument("dataset_id", nargs="?", help="Dataset ID for the info command")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print JSON output")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server (priority: --base-url > RAGFLOW_API_URL > RAGFLOW_BASE_URL > HOST_ADDRESS > default)",
    )
    return parser.parse_args(argv)


def _normalize_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "description": dataset.get("description"),
        "chunk_count": dataset.get("chunk_count"),
        "created_at": dataset.get("created_at"),
        "permission": dataset.get("permission"),
    }


def list_datasets(*, base_url: str, api_key: str) -> dict[str, Any]:
    payload = ensure_success(request_json(f"{base_url}/api/v1/datasets", api_key))
    datasets = payload.get("data")
    if not isinstance(datasets, list):
        raise DataError("Dataset list response missing data array.")
    normalized = [_normalize_dataset(dataset) for dataset in datasets]
    return {
        "checked_at": current_timestamp(),
        "count": len(normalized),
        "datasets": normalized,
    }


def dataset_info(dataset_id: str, *, base_url: str, api_key: str) -> dict[str, Any]:
    payload = list_datasets(base_url=base_url, api_key=api_key)
    for dataset in payload["datasets"]:
        if dataset.get("id") == dataset_id:
            return {
                "checked_at": current_timestamp(),
                "dataset": dataset,
            }
    raise DataError(f"Dataset not found: {dataset_id}")


def _format_list(payload: dict[str, Any]) -> str:
    lines = [
        f"Checked at: {payload['checked_at']}",
        f"Datasets: {payload['count']}",
    ]
    for dataset in payload["datasets"]:
        lines.extend(
            [
                "",
                f"- {dataset.get('name') or 'unknown'}",
                f"  id: {dataset.get('id') or 'unknown'}",
                f"  chunks: {dataset.get('chunk_count') if dataset.get('chunk_count') is not None else 'unknown'}",
                f"  created_at: {dataset.get('created_at') or 'unknown'}",
            ]
        )
    return "\n".join(lines)


def _format_info(payload: dict[str, Any]) -> str:
    dataset = payload["dataset"]
    return "\n".join(
        [
            f"Checked at: {payload['checked_at']}",
            f"Name: {dataset.get('name') or 'unknown'}",
            f"ID: {dataset.get('id') or 'unknown'}",
            f"Description: {dataset.get('description') or 'unknown'}",
            f"Chunk count: {dataset.get('chunk_count') if dataset.get('chunk_count') is not None else 'unknown'}",
            f"Created at: {dataset.get('created_at') or 'unknown'}",
            f"Permission: {dataset.get('permission') or 'unknown'}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    configure_stdio_utf8()
    load_repo_env(repo_root_from_path(__file__))
    args = _parse_args(argv)

    try:
        base_url = resolve_base_url(args.base_url)
        api_key = require_api_key()

        if args.command == "list":
            payload = list_datasets(base_url=base_url, api_key=api_key)
            print(format_json(payload) if args.json_output else _format_list(payload))
            return 0

        if not args.dataset_id:
            raise DataError("dataset_id is required for the info command.")

        payload = dataset_info(args.dataset_id, base_url=base_url, api_key=api_key)
        print(format_json(payload) if args.json_output else _format_info(payload))
        return 0
    except ScriptError as exc:
        if args.json_output:
            print(format_json({"checked_at": current_timestamp(), "error": str(exc)}))
        else:
            print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
