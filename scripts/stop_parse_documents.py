#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from typing import Any

from common import (
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
from parse_status import collect_status_payload, format_status_text


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stop parsing RAGFlow documents and return a current parser status snapshot.",
    )
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("document_ids", nargs="+", help="One or more document IDs to stop parsing")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print JSON output")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server (priority: --base-url > RAGFLOW_API_URL > RAGFLOW_BASE_URL > HOST_ADDRESS > default)",
    )
    return parser.parse_args(argv)


def stop_parse(dataset_id: str, document_ids: list[str], *, base_url: str, api_key: str) -> dict[str, Any]:
    url = f"{base_url}/api/v1/datasets/{dataset_id}/chunks"
    response = ensure_success(
        request_json(
            url,
            api_key,
            method="DELETE",
            body=json.dumps({"document_ids": document_ids}).encode("utf-8"),
            content_type="application/json",
        )
    )

    payload: dict[str, Any] = {
        "dataset_id": dataset_id,
        "document_ids": document_ids,
        "stop_requested_at": current_timestamp(),
    }
    message = response.get("message")
    if isinstance(message, str) and message.strip():
        payload["message"] = message.strip()
    data = response.get("data")
    if data is not None:
        payload["data"] = data
    return payload


def _format_payload(payload: dict[str, Any]) -> str:
    lines = [
        f"Dataset: {payload['dataset_id']}",
        f"Stop requested at: {payload['stop_requested_at']}",
    ]
    message = payload.get("message")
    if isinstance(message, str) and message:
        lines.append(f"Message: {message}")
    lines.extend(
        [
            "",
            format_status_text(payload["status"]),
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    configure_stdio_utf8()
    load_repo_env(repo_root_from_path(__file__))
    args = _parse_args(argv)

    try:
        base_url = resolve_base_url(args.base_url)
        api_key = require_api_key()
        stop_request = stop_parse(args.dataset_id, args.document_ids, base_url=base_url, api_key=api_key)
        status_payload = collect_status_payload(
            args.dataset_id,
            args.document_ids,
            base_url=base_url,
            api_key=api_key,
        )
        payload = {**stop_request, "status": status_payload}
        print(format_json(payload) if args.json_output else _format_payload(payload))
        return 0
    except ScriptError as exc:
        if args.json_output:
            print(
                format_json(
                    {
                        "dataset_id": args.dataset_id,
                        "document_ids": args.document_ids,
                        "stop_requested_at": current_timestamp(),
                        "error": str(exc),
                    }
                )
            )
        else:
            print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
