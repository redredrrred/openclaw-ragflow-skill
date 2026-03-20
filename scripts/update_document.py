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

        # Only load RAGFLOW_ prefixed variables to avoid accidentally loading
        # unrelated credentials (e.g., AWS keys, GitHub tokens) from the .env file
        if not key.startswith('RAGFLOW_'):
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update a document through the RAGFlow HTTP API.")
    parser.add_argument("dataset_id", help="Dataset ID")
    parser.add_argument("document_id", help="Document ID")
    parser.add_argument("--name", help="Updated document name")
    parser.add_argument("--chunk-method", help="Updated chunk method")
    parser.add_argument(
        "--parser-config",
        help="Parser config JSON object or @path/to/file.json",
    )
    parser.add_argument(
        "--meta-fields",
        help="Document metadata JSON object or @path/to/file.json",
    )
    parser.add_argument(
        "--enabled",
        choices=("0", "1"),
        help="Set availability flag: 1 enabled, 0 disabled",
    )
    parser.add_argument(
        "--data",
        help="Raw JSON object payload or @path/to/file.json. Explicit flags override the same keys.",
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON response")
    parser.add_argument(
        "--base-url",
        help="Base URL for the RAGFlow server "
        "(priority: --base-url > RAGFLOW_API_URL > default)",
    )
    return parser.parse_args(argv)


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


def _load_json_object(raw_value: str, option_name: str) -> dict[str, Any]:
    value = raw_value
    if raw_value.startswith("@"):
        path = Path(raw_value[1:]).expanduser()
        try:
            value = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigError(f"Failed to read {option_name} file {path}: {exc}") from exc

    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{option_name} must be valid JSON: {exc.msg}.") from exc

    if not isinstance(payload, dict):
        raise ConfigError(f"{option_name} must be a JSON object.")
    return payload


def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.data:
        payload.update(_load_json_object(args.data, "--data"))

    field_values = {
        "name": args.name,
        "chunk_method": args.chunk_method,
    }
    for key, value in field_values.items():
        if value is not None:
            payload[key] = value

    if args.parser_config is not None:
        payload["parser_config"] = _load_json_object(args.parser_config, "--parser-config")
    if args.meta_fields is not None:
        payload["meta_fields"] = _load_json_object(args.meta_fields, "--meta-fields")
    if args.enabled is not None:
        payload["enabled"] = int(args.enabled)

    if not payload:
        raise ConfigError("No update fields provided. Use --data or at least one explicit update flag.")
    return payload


def _build_url(base_url: str, dataset_id: str, document_id: str) -> str:
    encoded_dataset_id = urllib.parse.quote(dataset_id, safe="")
    encoded_document_id = urllib.parse.quote(document_id, safe="")
    return f"{base_url}/api/v1/datasets/{encoded_dataset_id}/documents/{encoded_document_id}"


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
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="PUT",
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
    return payload


def _print_summary(payload: dict[str, Any]) -> None:
    data = payload["data"]
    document_id = str(data.get("id", "")).strip() or "<missing-id>"
    name = str(data.get("name", "")).strip() or "<missing-name>"
    dataset_id = str(data.get("dataset_id", "")).strip() or "<missing-dataset-id>"
    print(f"Updated document: {name} ({document_id})")

    details = [f"dataset_id={dataset_id}"]
    if data.get("chunk_method"):
        details.append(f"chunk_method={data['chunk_method']}")
    if data.get("run"):
        details.append(f"run={data['run']}")
    if data.get("chunk_count") is not None:
        details.append(f"chunks={data['chunk_count']}")
    if data.get("token_count") is not None:
        details.append(f"tokens={data['token_count']}")
    print("  " + ", ".join(details))


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    _load_env_file(Path(__file__).resolve().parent.parent / ".env")

    try:
        args = _parse_args(argv)
        base_url = _resolve_base_url(args.base_url)
        api_key = _require_api_key()
        payload = _build_payload(args)
        response = _request_json(_build_url(base_url, args.dataset_id, args.document_id), api_key, payload)
        normalized = _normalize_payload(response)
    except ScriptError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
    else:
        _print_summary(normalized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
