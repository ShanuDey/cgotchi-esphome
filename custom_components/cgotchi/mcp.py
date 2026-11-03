"""Stateless MCP (streamable HTTP, JSON replies). Tools are built from the OpenAPI spec; no Home Assistant imports."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import voluptuous as vol

from .schemas import DISPLAY_SCHEMA, SPEAKER_SCHEMA, VOICE_SCHEMA

_LOGGER = logging.getLogger(__name__)

PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
INSTRUCTIONS = (
    "Controls the cgotchi device: its screen (page, theme, face expression, message, colors), speaker and "
    "wake word. A set_* tool returns the state read right after the change, which can still show the old "
    "value; read it again to confirm."
)

PARSE_ERROR_CODE = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

_HTTP_METHODS = ("get", "post", "put", "patch", "delete")

Run = Callable[[Any, dict[str, Any]], Awaitable[Any]]


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


PARSE_ERROR = _error(None, PARSE_ERROR_CODE, "the body is not valid JSON")


class _RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _read(method: str) -> Run:
    async def run(device: Any, args: dict[str, Any]) -> Any:
        return getattr(device, method)()

    return run


def _write(schema: Callable[[Any], dict[str, Any]], apply: str, read: str) -> Run:
    async def run(device: Any, args: dict[str, Any]) -> Any:
        await getattr(device, apply)(schema(args))
        return getattr(device, read)()

    return run


# operationId in openapi.yaml -> what runs. The spec describes a tool, this table executes it.
HANDLERS: dict[str, Run] = {
    "get_state": _read("state"),
    "get_display": _read("display_state"),
    "set_display": _write(DISPLAY_SCHEMA, "apply_display", "display_state"),
    "get_speaker": _read("speaker_state"),
    "set_speaker": _write(SPEAKER_SCHEMA, "apply_speaker", "speaker_state"),
    "get_wake_word": _read("voice_state"),
    "set_wake_word": _write(VOICE_SCHEMA, "apply_voice", "voice_state"),
    "get_touch": _read("touch_state"),
}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    run: Run

    def listing(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "inputSchema": self.input_schema}


def _resolve(spec: dict[str, Any], node: Any) -> Any:
    """Inline the local `#/...` references (the spec has no others)."""
    if isinstance(node, list):
        return [_resolve(spec, item) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if ref is not None:
        target: Any = spec
        for part in ref.removeprefix("#/").split("/"):
            target = target[part]
        return _resolve(spec, target)
    return {key: _resolve(spec, value) for key, value in node.items()}


def _input_schema(spec: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    return _resolve(spec, body) if body else {"type": "object", "properties": {}}


def build_tools(spec: dict[str, Any]) -> dict[str, Tool]:
    tools: dict[str, Tool] = {}
    for item in spec["paths"].values():
        for method, operation in item.items():
            if method not in _HTTP_METHODS:
                continue
            name = operation["operationId"]
            if name not in HANDLERS:
                raise ValueError(f"operation {name!r} has no handler")
            if operation.get("parameters"):
                raise ValueError(f"operation {name!r}: path and query parameters are not supported")
            text = (operation.get("summary"), operation.get("description"))
            description = "\n\n".join(part.strip() for part in text if part)
            tools[name] = Tool(name, description, _input_schema(spec, operation), HANDLERS[name])
    unused = set(HANDLERS) - set(tools)
    if unused:
        raise ValueError(f"handlers without an operation: {sorted(unused)}")
    return tools


def _text(text: str, *, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


class McpServer:
    def __init__(self, spec: dict[str, Any]) -> None:
        self._tools = build_tools(spec)
        self._version = str(spec["info"]["version"])

    async def handle(
        self, device: Any, message: Any, tool_errors: tuple[type[Exception], ...] = ()
    ) -> dict[str, Any] | None:
        """One JSON-RPC message in, the reply out. None means there is nothing to send (HTTP 202)."""
        if not isinstance(message, dict):
            return _error(None, INVALID_REQUEST, "send one JSON-RPC message per request")
        request_id = message.get("id")
        method = message.get("method")
        if not isinstance(method, str):
            if "result" in message or "error" in message:
                return None
            return _error(request_id, INVALID_REQUEST, "missing method")
        if "id" not in message:
            return None
        try:
            params = message.get("params", {})
            if not isinstance(params, dict):
                raise _RpcError(INVALID_PARAMS, "params must be an object")
            return _result(request_id, await self._dispatch(device, method, params, tool_errors))
        except _RpcError as err:
            return _error(request_id, err.code, err.message)
        except Exception:
            _LOGGER.exception("MCP request %s failed", method)
            return _error(request_id, INTERNAL_ERROR, "internal error")

    async def _dispatch(
        self, device: Any, method: str, params: dict[str, Any], tool_errors: tuple[type[Exception], ...]
    ) -> Any:
        if method == "initialize":
            requested = params.get("protocolVersion")
            return {
                "protocolVersion": requested if requested in PROTOCOLS else PROTOCOLS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "cgotchi", "version": self._version},
                "instructions": INSTRUCTIONS,
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": [tool.listing() for tool in self._tools.values()]}
        if method == "tools/call":
            return await self._call(device, params, tool_errors)
        raise _RpcError(METHOD_NOT_FOUND, f"unknown method {method!r}")

    async def _call(
        self, device: Any, params: dict[str, Any], tool_errors: tuple[type[Exception], ...]
    ) -> dict[str, Any]:
        name = params.get("name")
        tool = self._tools.get(name) if isinstance(name, str) else None
        if tool is None:
            raise _RpcError(INVALID_PARAMS, f"unknown tool {name!r}")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise _RpcError(INVALID_PARAMS, "arguments must be an object")
        try:
            data = await tool.run(device, args)
        except vol.Invalid as err:
            return _text(f"invalid arguments: {err}", is_error=True)
        except tool_errors as err:
            return _text(str(err), is_error=True)
        return _text(json.dumps(data, default=str))
