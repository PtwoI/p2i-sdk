"""Small, provider-neutral HTTP client for the local P2I server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from p2i import ModelIR


class P2IAPIError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


class Client:
    """Access the same JSON API used by the P2I browser UI.

    No model or activation values are sent anywhere other than the explicitly
    configured server. The default is the local, loopback P2I instance.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000", *, timeout: float = 10):
        parsed = urlsplit(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path not in ("", "/"):
            raise ValueError("base_url must be an HTTP(S) origin without a path")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, body: Mapping[str, Any] | bytes | None = None, *, raw: bool = False) -> Any:
        binary = isinstance(body, bytes)
        payload = body if binary else None if body is None else json.dumps(body, allow_nan=False).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=payload,
            headers={"Accept": "application/octet-stream" if raw else "application/json", **({"Content-Type": "application/octet-stream" if binary else "application/json"} if payload is not None else {})},
            method="POST" if payload is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read() if raw else json.load(response)
        except HTTPError as exc:
            raw = exc.read()
            try:
                detail = json.loads(raw)
            except (ValueError, TypeError):
                detail = raw.decode("utf-8", errors="replace")
            raise P2IAPIError(f"P2I returned HTTP {exc.code}", status=exc.code, detail=detail) from exc
        except URLError as exc:
            raise P2IAPIError(f"Cannot reach P2I at {self.base_url}: {exc.reason}") from exc

    def model(self) -> dict[str, Any]:
        return self._request("/api/model")

    def model_ir(self) -> ModelIR:
        from p2i import ModelIR

        return ModelIR.model_validate(self.model())

    def modules(self) -> list[dict[str, Any]]:
        return self._request("/api/modules")

    def item(self, kind: str, item_id: str) -> dict[str, Any]:
        if kind not in ("modules", "operations", "tensors"):
            raise ValueError("kind must be modules, operations or tensors")
        return self._request(f"/api/{kind}/{quote(item_id, safe='')}")

    def inspection(self) -> dict[str, Any]:
        return self._request("/api/inspection")

    def harness(self) -> dict[str, Any]:
        return self._request("/api/harness")

    def skills(self, *, query: str = "") -> dict[str, Any]:
        suffix = "?query=" + quote(query, safe="") if query else ""
        return self._request("/api/skills" + suffix)

    def command(self, name: str, body: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if name not in ("preview", "apply", "validate", "undo", "redo", "retrace"):
            raise ValueError("Unknown harness command")
        return self._request(f"/api/harness/{name}", body or {})

    def tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not name:
            raise ValueError("tool name is required")
        return self._request("/api/tools", {"tool": name, "arguments": dict(arguments or {})})

    def save_checkpoint(self, path: str | Path, *, include_inputs: bool = True,
                        expected_revision: int | None = None) -> Path:
        """Download structure, weights and optional examples from the live session."""
        data = self._request("/api/checkpoint/export", {
            "include_inputs": include_inputs, "expected_revision": expected_revision,
        }, raw=True)
        destination = Path(path)
        destination.write_bytes(data)
        return destination

    def open_checkpoint(self, path: str | Path) -> dict[str, Any]:
        """Replace the live session only after the server can restore and trace it."""
        return self._request("/api/checkpoint/import", Path(path).read_bytes())
