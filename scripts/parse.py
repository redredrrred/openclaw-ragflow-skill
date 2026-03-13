#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path

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
from parse_status import (
    DEFAULT_INTERVAL,
    DEFAULT_TIMEOUT,
    WatchTimeout,
    collect_status_payload,
    format_status_text,
    start_background_watch,
    watch_status_until_terminal,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start parsing uploaded RAGFlow documents and return parser status.")
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("document_ids", nargs="+", help="Document IDs to parse")
    parser.add_argument("--watch", action="store_true", help="Poll until all target documents reach a terminal state")
    parser.add_argument("--background", action="store_true", help="Start a detached watcher and return immediately")
    parser.add_argument("--output", help="Write background-watch JSON to this file")
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help=f"Polling interval in seconds (default: {int(DEFAULT_INTERVAL)})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Polling timeout in seconds (default: {int(DEFAULT_TIMEOUT)})",
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print JSON output")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server (priority: --base-url > RAGFLOW_API_URL > RAGFLOW_BASE_URL > HOST_ADDRESS > default)",
    )
    return parser.parse_args(argv)


def start_parse(dataset_id: str, document_ids: list[str], *, base_url: str, api_key: str) -> dict[str, object]:
    url = f"{base_url}/api/v1/datasets/{dataset_id}/chunks"
    body = json.dumps({"document_ids": document_ids}).encode("utf-8")
    ensure_success(
        request_json(
            url,
            api_key,
            method="POST",
            body=body,
            content_type="application/json",
        )
    )
    return {
        "dataset_id": dataset_id,
        "document_ids": document_ids,
        "parse_requested_at": current_timestamp(),
    }


def _format_once_or_watch(payload: dict[str, object]) -> str:
    status_payload = payload["status"]
    lines = [
        f"Dataset: {payload['dataset_id']}",
        f"Parse requested at: {payload['parse_requested_at']}",
        f"Mode: {payload['status_mode']}",
        "",
        format_status_text(status_payload),
    ]
    return "\n".join(lines)


def _format_background(payload: dict[str, object]) -> str:
    background_job = payload["background_job"]
    status_payload = payload["status"]
    lines = [
        f"Dataset: {payload['dataset_id']}",
        f"Parse requested at: {payload['parse_requested_at']}",
        f"Mode: {payload['status_mode']}",
        f"PID: {background_job['pid'] if background_job['pid'] is not None else 'not started'}",
        f"Output: {background_job['output_path']}",
        f"Log: {background_job['error_path']}",
        "",
        background_job["message"],
        "",
        "Initial status:",
        format_status_text(status_payload),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    configure_stdio_utf8()
    load_repo_env(repo_root_from_path(__file__))
    args = _parse_args(argv)

    try:
        if args.interval <= 0:
            raise ScriptError("--interval must be greater than 0.")
        if args.timeout <= 0:
            raise ScriptError("--timeout must be greater than 0.")

        base_url = resolve_base_url(args.base_url)
        api_key = require_api_key()
        parse_request = start_parse(args.dataset_id, args.document_ids, base_url=base_url, api_key=api_key)

        if args.background:
            background_job = start_background_watch(
                args.dataset_id,
                args.document_ids,
                interval=args.interval,
                timeout=args.timeout,
                base_url=base_url,
                api_key=api_key,
                output_path=Path(args.output) if args.output else None,
            )
            payload = {
                **parse_request,
                "status_mode": "background",
                "status": background_job["initial_status"],
                "background_job": background_job,
            }
            print(format_json(payload) if args.json_output else _format_background(payload))
            return 0

        if args.watch:
            status_payload = watch_status_until_terminal(
                args.dataset_id,
                args.document_ids,
                interval=args.interval,
                timeout=args.timeout,
                base_url=base_url,
                api_key=api_key,
                print_updates=not args.json_output,
            )
            payload = {**parse_request, "status_mode": "watch", "status": status_payload}
            if args.json_output:
                print(format_json(payload))
            return 0

        status_payload = collect_status_payload(
            args.dataset_id,
            args.document_ids,
            base_url=base_url,
            api_key=api_key,
        )
        payload = {**parse_request, "status_mode": "once", "status": status_payload}
        print(format_json(payload) if args.json_output else _format_once_or_watch(payload))
        return 0
    except WatchTimeout as exc:
        if args.json_output:
            print(
                format_json(
                    {
                        "dataset_id": args.dataset_id,
                        "document_ids": args.document_ids,
                        "parse_requested_at": current_timestamp(),
                        "timed_out": True,
                        "status": exc.payload,
                        "error": str(exc),
                    }
                )
            )
        else:
            print(f"Error: {exc}")
        return 1
    except ScriptError as exc:
        if args.json_output:
            print(
                format_json(
                    {
                        "dataset_id": args.dataset_id,
                        "document_ids": args.document_ids,
                        "parse_requested_at": current_timestamp(),
                        "error": str(exc),
                    }
                )
            )
        else:
            print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
