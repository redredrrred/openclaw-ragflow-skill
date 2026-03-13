#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Show and poll document parse status for a dataset.
Usage:
  python scripts/parse_status.py <dataset_id>
  python scripts/parse_status.py <dataset_id> --doc-ids DOC1,DOC2 --watch
"""

import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import io

DEFAULT_BASE_URL = "http://127.0.0.1"
DEFAULT_INTERVAL = 10.0
DEFAULT_TIMEOUT = 1800.0
DEFAULT_PAGE_SIZE = 100
HTTP_TIMEOUT = 30
STATUS_ORDER = ("UNSTART", "RUNNING", "DONE", "FAIL", "CANCEL")
TERMINAL_STATES = {"DONE", "FAIL", "CANCEL"}
RUN_STATUS_MAP = {
    "0": "UNSTART",
    "1": "RUNNING",
    "2": "CANCEL",
    "3": "DONE",
    "4": "FAIL",
}


class ScriptError(Exception):
    pass


class ConfigError(ScriptError):
    pass


class ApiError(ScriptError):
    pass


class DataError(ScriptError):
    pass


class WatchTimeout(ScriptError):
    def __init__(self, timeout_seconds: float, payload: dict[str, Any]):
        super().__init__(f"Watch timeout after {_format_number(timeout_seconds)} seconds.")
        self.timeout_seconds = timeout_seconds
        self.payload = payload


@dataclass
class DocumentStatus:
    id: str
    name: str
    run: str
    chunk_count: int
    token_count: int


def _current_timestamp() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _configure_stdio_utf8() -> None:
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            continue


def _load_env_file(env_path: Path) -> None:
    if not env_path.is_file():
        return

    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"Failed to read {env_path}: {exc}") from exc

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show and poll document parse status for a dataset.")
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("--doc-ids", help="Comma-separated document IDs to monitor")
    parser.add_argument("--watch", action="store_true", help="Poll until all target documents reach a terminal state")
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


def _parse_doc_ids(raw_value: str | None) -> list[str] | None:
    if raw_value is None:
        return None

    doc_ids: list[str] = []
    seen: set[str] = set()
    for item in raw_value.split(","):
        doc_id = item.strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        doc_ids.append(doc_id)

    if not doc_ids:
        raise ConfigError("--doc-ids must include at least one document ID.")
    return doc_ids


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ConfigError(f"{name} must be greater than 0.")


def _resolve_base_url(cli_base_url: str | None) -> str:
    base_url = (
        cli_base_url
        or os.getenv("RAGFLOW_API_URL")
        or os.getenv("RAGFLOW_BASE_URL")
        or os.getenv("HOST_ADDRESS")
        or DEFAULT_BASE_URL
    ).strip()

    parsed = urllib.parse.urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ConfigError("Invalid base URL. Use an absolute URL such as http://127.0.0.1:9380.")
    return base_url.rstrip("/")


def _require_api_key() -> str:
    api_key = (os.getenv("RAGFLOW_API_KEY") or "").strip()
    if not api_key:
        raise ConfigError("RAGFLOW_API_KEY is not configured. Set it in the environment or in the repository .env file.")
    return api_key


def _build_documents_url(base_url: str, dataset_id: str, page: int, page_size: int) -> str:
    encoded_dataset_id = urllib.parse.quote(dataset_id, safe="")
    query = urllib.parse.urlencode({"page": page, "page_size": page_size})
    return f"{base_url}/api/v1/datasets/{encoded_dataset_id}/documents?{query}"


def _decode_json_response(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ApiError("Received a non-JSON response from the server.") from exc

    if not isinstance(payload, dict):
        raise DataError("Expected a JSON object from the server.")
    return payload


def _extract_error_message(body: bytes) -> str | None:
    if not body:
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


def _request_json(url: str, api_key: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            return _decode_json_response(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        message = _extract_error_message(body)
        if message:
            raise ApiError(message) from None
        raise ApiError(f"HTTP request failed with status {exc.code}.") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise ApiError(f"HTTP request failed: {reason}") from None


def _fetch_documents_page(base_url: str, api_key: str, dataset_id: str, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    url = _build_documents_url(base_url, dataset_id, page, page_size)
    payload = _request_json(url, api_key)

    code = payload.get("code")
    if code != 0:
        message = payload.get("message") or f"API returned code {code}."
        raise ApiError(str(message))

    data = payload.get("data")
    if not isinstance(data, dict):
        raise DataError("Response missing data object.")

    docs = data.get("docs")
    total = data.get("total")
    if not isinstance(docs, list):
        raise DataError("Response missing data.docs.")
    if not isinstance(total, int):
        raise DataError("Response missing data.total.")
    return docs, total


def _fetch_all_documents(base_url: str, api_key: str, dataset_id: str) -> list[dict[str, Any]]:
    all_docs: list[dict[str, Any]] = []
    page = 1
    total: int | None = None

    while True:
        docs, page_total = _fetch_documents_page(base_url, api_key, dataset_id, page, DEFAULT_PAGE_SIZE)
        if total is None:
            total = page_total
        all_docs.extend(docs)

        if len(all_docs) >= total or not docs:
            return all_docs[:total]
        page += 1


def _coerce_required_string(document_id: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"Document {document_id} is missing a valid {field_name}.")
    return value.strip()


def _coerce_required_int(document_id: str, field_name: str, value: Any) -> int:
    if isinstance(value, bool):
        raise DataError(f"Document {document_id} is missing a valid {field_name}.")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise DataError(f"Document {document_id} is missing a valid {field_name}.") from None
    if number < 0:
        raise DataError(f"Document {document_id} is missing a valid {field_name}.")
    return number


def _normalize_run(value: Any, document_id: str) -> str:
    if isinstance(value, int):
        mapped = RUN_STATUS_MAP.get(str(value))
        if mapped:
            return mapped
    elif isinstance(value, str):
        raw_value = value.strip()
        mapped = RUN_STATUS_MAP.get(raw_value)
        if mapped:
            return mapped
        normalized = raw_value.upper()
        if normalized in STATUS_ORDER:
            return normalized

    raise DataError(f"Document {document_id} has an unsupported run status: {value!r}.")


def _normalize_document(raw_doc: dict[str, Any]) -> DocumentStatus:
    if not isinstance(raw_doc, dict):
        raise DataError("Response contains a malformed document entry.")

    raw_id = raw_doc.get("id")
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise DataError("Response contains a document with a missing id.")
    document_id = raw_id.strip()

    return DocumentStatus(
        id=document_id,
        name=_coerce_required_string(document_id, "name", raw_doc.get("name")),
        run=_normalize_run(raw_doc.get("run"), document_id),
        chunk_count=_coerce_required_int(document_id, "chunk_count", raw_doc.get("chunk_count")),
        token_count=_coerce_required_int(document_id, "token_count", raw_doc.get("token_count")),
    )


def _normalize_documents(raw_docs: list[dict[str, Any]]) -> list[DocumentStatus]:
    return [_normalize_document(raw_doc) for raw_doc in raw_docs]


def _select_documents(documents: list[DocumentStatus], target_ids: list[str] | None) -> list[DocumentStatus]:
    if not target_ids:
        return documents

    documents_by_id = {document.id: document for document in documents}
    missing_ids = [doc_id for doc_id in target_ids if doc_id not in documents_by_id]
    if missing_ids:
        raise DataError("--doc-ids contains document IDs that were not found in the dataset: " + ", ".join(missing_ids))
    return [documents_by_id[doc_id] for doc_id in target_ids]


def _build_payload(dataset_id: str, documents: list[DocumentStatus]) -> dict[str, Any]:
    summary = {"total": len(documents)}
    for status in STATUS_ORDER:
        summary[status] = 0

    for document in documents:
        summary[document.run] += 1

    return {
        "dataset_id": dataset_id,
        "checked_at": _current_timestamp(),
        "summary": summary,
        "documents": [asdict(document) for document in documents],
        "all_terminal": all(document.run in TERMINAL_STATES for document in documents),
    }


def _collect_payload(base_url: str, api_key: str, dataset_id: str, target_ids: list[str] | None) -> dict[str, Any]:
    raw_documents = _fetch_all_documents(base_url, api_key, dataset_id)
    documents = _normalize_documents(raw_documents)
    selected_documents = _select_documents(documents, target_ids)
    return _build_payload(dataset_id, selected_documents)


def _format_text(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    documents = payload["documents"]

    lines = [
        f"Dataset: {payload['dataset_id']}",
        f"Checked at: {payload['checked_at']}",
        f"Watching: {summary['total']} document(s)",
        "",
    ]

    for status in STATUS_ORDER:
        lines.append(f"{status}: {summary[status]}")

    for document in documents:
        lines.extend([
            "",
            f"[{document['run']}] {document['name']}",
            f"id: {document['id']}",
            f"chunks: {document['chunk_count']}",
            f"tokens: {document['token_count']}",
        ])

    return "\n".join(lines)


def _format_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def _poll_until_complete(base_url: str, api_key: str, dataset_id: str, target_ids: list[str] | None, interval: float, timeout: float, print_updates: bool) -> dict[str, Any]:
    started_at = time.monotonic()
    last_signature = None

    while True:
        payload = _collect_payload(base_url, api_key, dataset_id, target_ids)
        if print_updates:
            signature = json.dumps(
                {
                    "summary": payload["summary"],
                    "documents": payload["documents"],
                    "all_terminal": payload["all_terminal"],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            rendered = _format_text(payload)
            if signature != last_signature:
                if last_signature is not None:
                    print()
                print(rendered, flush=True)
                last_signature = signature

        if payload["all_terminal"]:
            return payload

        if time.monotonic() - started_at >= timeout:
            raise WatchTimeout(timeout, payload)

        time.sleep(interval)


def _write_error(message: str, json_output: bool, dataset_id: str | None = None, payload: dict[str, Any] | None = None) -> None:
    if json_output:
        error_payload: dict[str, Any] = {}
        if payload:
            error_payload.update(payload)
        elif dataset_id:
            error_payload["dataset_id"] = dataset_id
        if "checked_at" not in error_payload:
            error_payload["checked_at"] = _current_timestamp()
        error_payload["error"] = message
        if "timed_out" not in error_payload:
            error_payload["timed_out"] = False
        print(_format_json(error_payload))
        return

    print(f"Error: {message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    repo_root = Path(__file__).resolve().parents[1]
    _load_env_file(repo_root / ".env")

    args = _parse_args(argv)

    try:
        target_ids = _parse_doc_ids(args.doc_ids)
        _validate_positive("--interval", args.interval)
        _validate_positive("--timeout", args.timeout)
        api_key = _require_api_key()
        base_url = _resolve_base_url(args.base_url)

        if args.watch:
            payload = _poll_until_complete(
                base_url=base_url,
                api_key=api_key,
                dataset_id=args.dataset_id,
                target_ids=target_ids,
                interval=args.interval,
                timeout=args.timeout,
                print_updates=not args.json_output,
            )
            if args.json_output:
                print(_format_json(payload))
            return 0

        payload = _collect_payload(base_url, api_key, args.dataset_id, target_ids)
        if args.json_output:
            print(_format_json(payload))
        else:
            print(_format_text(payload))
        return 0
    except WatchTimeout as exc:
        timeout_payload = dict(exc.payload)
        timeout_payload["timed_out"] = True
        _write_error(str(exc), args.json_output, dataset_id=args.dataset_id, payload=timeout_payload)
        return 1
    except ScriptError as exc:
        _write_error(str(exc), args.json_output, dataset_id=args.dataset_id)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
