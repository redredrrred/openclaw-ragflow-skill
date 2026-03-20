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
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:9380"
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
DEFAULT_ORDERBY = "create_time"
HTTP_TIMEOUT = 30


class ScriptError(Exception):
    pass


class ConfigError(ScriptError):
    pass


class ApiError(ScriptError):
    pass


class DataError(ScriptError):
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

        # Only load RAGFLOW_ prefixed variables to avoid accidentally loading
        # unrelated credentials (e.g., AWS keys, GitHub tokens) from the .env file
        if not key.startswith('RAGFLOW_'):
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List documents in a dataset through the RAGFlow HTTP API.")
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("--page", type=int, default=DEFAULT_PAGE, help=f"Page number (default: {DEFAULT_PAGE})")
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Page size (default: {DEFAULT_PAGE_SIZE})",
    )
    parser.add_argument("--orderby", default=DEFAULT_ORDERBY, help=f"Sort field (default: {DEFAULT_ORDERBY})")
    parser.add_argument("--asc", action="store_true", help="Sort ascending. Descending is the default.")
    parser.add_argument("--keywords", help="Filter by keywords")
    parser.add_argument("--id", dest="document_id", help="Filter by document ID")
    parser.add_argument("--name", help="Filter by document name")
    parser.add_argument("--suffix", help="Filter by file suffix, for example pdf")
    parser.add_argument("--run", help="Filter by parse run status, for example DONE")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON response")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server "
        "(priority: --base-url > RAGFLOW_API_URL > default)",
    )
    return parser.parse_args(argv)


def _validate_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ConfigError(f"{name} must be greater than 0.")


def _resolve_base_url(cli_base_url: str | None) -> str:
    base_url = (
        cli_base_url
        or DEFAULT_BASE_URL
    ).strip()

    parsed = urllib.parse.urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ConfigError("Invalid base URL. Use an absolute URL such as http://127.0.0.1:9380.")
    return base_url.rstrip("/")


def _require_api_key() -> str:
    api_key = (os.getenv("RAGFLOW_API_KEY") or "").strip()
    if not api_key:
        raise ConfigError(
            "RAGFLOW_API_KEY is not configured. Set it in the environment or in the repository .env file."
        )
    return api_key


def _build_documents_url(base_url: str, args: argparse.Namespace) -> str:
    dataset_id = args.dataset_id.strip()
    if not dataset_id:
        raise ConfigError("dataset_id must not be empty.")

    query: dict[str, Any] = {
        "page": args.page,
        "page_size": args.page_size,
        "orderby": args.orderby,
        "desc": str(not args.asc).lower(),
    }
    if args.keywords:
        query["keywords"] = args.keywords
    if args.document_id:
        query["id"] = args.document_id
    if args.name:
        query["name"] = args.name
    if args.suffix:
        query["suffix"] = args.suffix
    if args.run:
        query["run"] = args.run

    encoded_dataset_id = urllib.parse.quote(dataset_id, safe="")
    encoded_query = urllib.parse.urlencode(query)
    return f"{base_url}/api/v1/datasets/{encoded_dataset_id}/documents?{encoded_query}"


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
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
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


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
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

    return {
        "code": code,
        "message": payload.get("message", ""),
        "data": data,
    }


def _format_document_line(document: dict[str, Any]) -> str:
    document_id = str(document.get("id", "")).strip() or "<missing-id>"
    name = str(document.get("name", "")).strip() or "<missing-name>"
    lines = [f"{name} ({document_id})"]

    details = []
    for key, label in (
        ("run", "run"),
        ("type", "type"),
        ("chunk_count", "chunks"),
        ("token_count", "tokens"),
        ("size", "size"),
    ):
        value = document.get(key)
        if value not in (None, ""):
            details.append(f"{label}={value}")
    if details:
        lines.append("  " + ", ".join(details))

    return "\n".join(lines)


def _format_text(payload: dict[str, Any], dataset_id: str) -> str:
    data = payload["data"]
    docs = data["docs"]
    total = data["total"]

    lines = [f"Dataset: {dataset_id}", f"Documents: {len(docs)} / total={total}"]
    if not docs:
        return "\n".join(lines)

    for document in docs:
        lines.append("")
        lines.append(_format_document_line(document))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    repo_root = Path(__file__).resolve().parents[1]
    _load_env_file(repo_root / ".env")

    args = _parse_args(argv)

    try:
        _validate_positive("--page", args.page)
        _validate_positive("--page-size", args.page_size)
        api_key = _require_api_key()
        base_url = _resolve_base_url(args.base_url)
        payload = _request_json(_build_documents_url(base_url, args), api_key)
        normalized = _normalize_payload(payload)

        if args.json_output:
            print(json.dumps(normalized, ensure_ascii=False, indent=2))
        else:
            print(_format_text(normalized, args.dataset_id.strip()))
        return 0
    except ScriptError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
