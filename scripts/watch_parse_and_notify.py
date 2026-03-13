#!/usr/bin/env python3
#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_INTERVAL = 10.0
DEFAULT_TIMEOUT = 1800.0
STATUS_KEYS = ("UNSTART", "RUNNING", "DONE", "FAIL", "CANCEL")


class ScriptError(Exception):
    pass


def _configure_stdio_utf8() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            continue


def _current_timestamp() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Watch parse completion for specific documents and emit one final summary JSON."
    )
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("--doc-ids", required=True, help="Comma-separated document IDs to monitor")
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
    parser.add_argument("--base-url", help="Optional base URL passed through to parse_status.py")
    return parser.parse_args(argv)


def _parse_doc_ids(raw_value: str) -> list[str]:
    doc_ids: list[str] = []
    seen: set[str] = set()
    for item in raw_value.split(","):
        doc_id = item.strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        doc_ids.append(doc_id)
    if not doc_ids:
        raise ScriptError("--doc-ids must include at least one document ID.")
    return doc_ids


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def _build_parse_status_command(args: argparse.Namespace) -> list[str]:
    parse_status_path = Path(__file__).resolve().with_name("parse_status.py")
    command = [
        sys.executable,
        str(parse_status_path),
        args.dataset_id,
        "--doc-ids",
        args.doc_ids,
        "--watch",
        "--json",
        "--interval",
        _format_number(args.interval),
        "--timeout",
        _format_number(args.timeout),
    ]
    if args.base_url:
        command.extend(["--base-url", args.base_url])
    return command


def _run_parse_status(args: argparse.Namespace) -> dict[str, Any]:
    completed = subprocess.run(
        _build_parse_status_command(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    stdout_text = completed.stdout.decode("utf-8", errors="replace").strip()
    stderr_text = completed.stderr.decode("utf-8", errors="replace").strip()

    if not stdout_text:
        message = stderr_text or "parse_status.py produced no output."
        raise ScriptError(message)

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        raise ScriptError(f"parse_status.py returned invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ScriptError("parse_status.py returned a non-object JSON payload.")

    if completed.returncode != 0 and "error" not in payload:
        payload["error"] = stderr_text or f"parse_status.py exited with code {completed.returncode}."

    return payload


def _default_summary(total: int) -> dict[str, int]:
    summary = {"total": total}
    for key in STATUS_KEYS:
        summary[key] = 0
    return summary


def _build_message(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    dataset_id = payload["dataset_id"]
    documents = payload.get("documents", [])
    done = summary.get("DONE", 0)
    fail = summary.get("FAIL", 0)
    cancel = summary.get("CANCEL", 0)
    running = summary.get("RUNNING", 0)

    if payload.get("timed_out"):
        return (
            "Parse monitoring timed out.\n"
            f"dataset: {dataset_id}\n"
            f"Current status: DONE: {done}, RUNNING: {running}, FAIL: {fail}\n"
            "Start another watcher if you still need monitoring."
        )

    if fail > 0:
        return (
            "Parse finished, but some documents failed.\n"
            f"dataset: {dataset_id}\n"
            f"DONE: {done}, FAIL: {fail}, CANCEL: {cancel}\n"
            "Please inspect the failed documents."
        )

    if cancel > 0 and done == 0:
        return (
            "Parse finished, but the documents were canceled.\n"
            f"dataset: {dataset_id}\n"
            f"DONE: {done}, FAIL: {fail}, CANCEL: {cancel}\n"
            "Please inspect the canceled documents."
        )

    details = ", ".join(f"{doc.get('name', doc.get('id', 'unknown'))} ({doc.get('run', 'UNKNOWN')})" for doc in documents)
    if not details:
        details = "none"
    return (
        "Parse finished.\n"
        f"dataset: {dataset_id}\n"
        f"DONE: {done}, FAIL: {fail}, CANCEL: {cancel}\n"
        f"Document details: {details}"
    )


def _classify_result(payload: dict[str, Any]) -> str:
    if payload.get("error") and not payload.get("timed_out"):
        return "error"
    if payload.get("timed_out"):
        return "timeout"
    summary = payload["summary"]
    if summary.get("FAIL", 0) > 0 or summary.get("CANCEL", 0) > 0:
        return "partial_or_all_failed"
    return "all_done"


def _finalize_payload(raw_payload: dict[str, Any], dataset_id: str, doc_ids: list[str]) -> dict[str, Any]:
    summary = raw_payload.get("summary")
    if not isinstance(summary, dict):
        summary = _default_summary(len(doc_ids))

    documents = raw_payload.get("documents")
    if not isinstance(documents, list):
        documents = []

    payload = {
        "dataset_id": raw_payload.get("dataset_id", dataset_id),
        "document_ids": doc_ids,
        "timed_out": bool(raw_payload.get("timed_out", False)),
        "all_terminal": bool(raw_payload.get("all_terminal", False)),
        "summary": summary,
        "documents": documents,
        "checked_at": raw_payload.get("checked_at", _current_timestamp()),
    }
    if "error" in raw_payload:
        payload["error"] = raw_payload["error"]
    payload["result"] = _classify_result(payload)
    payload["message"] = _build_message(payload) if "error" not in payload else str(payload["error"])
    return payload


def _emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    args = _parse_args(argv)

    try:
        if args.interval <= 0:
            raise ScriptError("--interval must be greater than 0.")
        if args.timeout <= 0:
            raise ScriptError("--timeout must be greater than 0.")

        doc_ids = _parse_doc_ids(args.doc_ids)
        payload = _finalize_payload(_run_parse_status(args), args.dataset_id, doc_ids)
        _emit_json(payload)
        return 0 if payload["result"] in {"all_done", "partial_or_all_failed", "timeout"} else 1
    except ScriptError as exc:
        _emit_json(
            {
                "dataset_id": args.dataset_id,
                "document_ids": [],
                "timed_out": False,
                "all_terminal": False,
                "summary": _default_summary(0),
                "documents": [],
                "checked_at": _current_timestamp(),
                "result": "error",
                "message": str(exc),
                "error": str(exc),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
