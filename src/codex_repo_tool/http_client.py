from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping


class HttpError(RuntimeError):
    """Raised when an HTTP response indicates failure."""

    def __init__(self, status_code: int, message: str | None = None) -> None:
        detail = message or ""
        super().__init__(f"HTTP {status_code}: {detail}".strip())
        self.status_code = status_code
        self.message = detail


@dataclass
class SimpleResponse:
    """Lightweight wrapper mimicking the subset of the requests.Response API we use."""

    status_code: int
    headers: Mapping[str, str]
    text: str
    _json_data: Any | None = None
    _error: Exception | None = None

    def json(self) -> Any:
        if self._json_data is not None:
            return self._json_data
        if not self.text:
            return None
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:  # pragma: no cover - mirrors requests behaviour
            raise ValueError("Response body is not valid JSON") from exc

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise HttpError(self.status_code, self.text) from self._error


class HttpClient:
    """Best-effort HTTP client that prefers requests but gracefully falls back to urllib."""

    def __init__(self) -> None:
        try:
            import requests  # type: ignore
        except ImportError:  # pragma: no cover - exercised when requests missing
            self._requests = None
        else:  # pragma: no cover - behaviour exercised via mocks
            self._requests = requests

    def _request_via_requests(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json_data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        timeout: float | int = 30,
    ):
        assert self._requests is not None
        return self._requests.request(  # type: ignore[attr-defined]
            method,
            url,
            headers=dict(headers or {}),
            json=json_data,
            params=dict(params or {}),
            timeout=timeout,
        )

    def _request_via_urllib(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json_data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        timeout: float | int = 30,
    ) -> SimpleResponse:
        query = urllib.parse.urlencode(params or {})
        if query:
            separator = "&" if urllib.parse.urlsplit(url).query else "?"
            url = f"{url}{separator}{query}"

        body: bytes | None = None
        req_headers: MutableMapping[str, str] = dict(headers or {})
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")

        request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                raw = resp.read()
                text = raw.decode("utf-8", errors="replace")
                return SimpleResponse(
                    status_code=resp.getcode() or 0,
                    headers=dict(resp.headers.items()),
                    text=text,
                    _json_data=None,
                )
        except urllib.error.HTTPError as exc:
            raw = exc.read() if exc.fp else b""
            text = raw.decode("utf-8", errors="replace") if raw else ""
            return SimpleResponse(
                status_code=exc.code,
                headers=dict(exc.headers.items()) if exc.headers else {},
                text=text,
                _json_data=None,
                _error=exc,
            )
        except urllib.error.URLError as exc:  # pragma: no cover - network failure path
            raise HttpError(-1, str(exc)) from exc

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
        timeout: float | int = 30,
    ):
        if self._requests is not None:
            return self._request_via_requests(
                method,
                url,
                headers=headers,
                json_data=json,
                params=params,
                timeout=timeout,
            )
        return self._request_via_urllib(
            method,
            url,
            headers=headers,
            json_data=json,
            params=params,
            timeout=timeout,
        )

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


client = HttpClient()

__all__ = ["HttpClient", "HttpError", "SimpleResponse", "client"]
