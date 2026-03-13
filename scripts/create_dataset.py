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

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a dataset through the RAGFlow HTTP API.")
    parser.add_argument("name", help="Dataset name")
    parser.add_argument("--avatar", help="Dataset avatar")
    parser.add_argument("--description", help="Dataset description")
    parser.add_argument("--embedding-model", dest="embedding_model", help="Embedding model ID")
    parser.add_argument("--permission", help="Permission value, for example me or team")
    parser.add_argument("--chunk-method", dest="chunk_method", help="Chunking method / parser ID")
    parser.add_argument("--language", help="Dataset language")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON response")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server "
        "(priority: --base-url > RAGFLOW_BASE_URL > HOST_ADDRESS > default)",
    )
    return parser.parse_args(argv)


def _resolve_base_url(cli_base_url: str | None) -> str:
    base_url = (
        cli_base_url
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
        raise ConfigError(
            "RAGFLOW_API_KEY is not configured. Set it in the environment or in the repository .env file."
        )
    return api_key


def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    name = args.name.strip()
    if not name:
        raise ConfigError("Dataset name must not be empty.")

    payload: dict[str, Any] = {"name": name}
    if args.avatar:
        payload["avatar"] = args.avatar
    if args.description:
        payload["description"] = args.description
    if args.embedding_model:
        payload["embedding_model"] = args.embedding_model
    if args.permission:
        payload["permission"] = args.permission
    if args.chunk_method:
        payload["chunk_method"] = args.chunk_method
    if args.language:
        payload["language"] = args.language
    return payload


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


def _request_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
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

    return {
        "code": code,
        "message": payload.get("message", ""),
        "data": data,
    }


def _format_text(payload: dict[str, Any]) -> str:
    data = payload["data"]
    lines = ["Dataset created"]

    dataset_id = data.get("id")
    name = data.get("name")
    if name:
        lines.append(f"name: {name}")
    if dataset_id:
        lines.append(f"id: {dataset_id}")

    for key in ("embedding_model", "permission", "chunk_method", "language", "avatar", "description"):
        value = data.get(key)
        if value not in (None, ""):
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    repo_root = Path(__file__).resolve().parents[1]
    _load_env_file(repo_root / ".env")

    args = _parse_args(argv)

    try:
        api_key = _require_api_key()
        base_url = _resolve_base_url(args.base_url)
        payload = _request_json(f"{base_url}/api/v1/datasets", api_key, _build_payload(args))
        normalized = _normalize_payload(payload)

        if args.json_output:
            print(json.dumps(normalized, ensure_ascii=False, indent=2))
        else:
            print(_format_text(normalized))
        return 0
    except ScriptError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
