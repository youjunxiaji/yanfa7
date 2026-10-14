"""几个 app 共用的 pytest fixture

TMB 服务器（tmb_web_v1）换成进程内的假服务器（httpx 的 MockTransport），不碰真实网络；账号和载荷简化的历史记录都用它。
"""

from typing import Any

import httpx
import pytest

from common import tmb_web


class FakeTmbServer:
    """按「方法 + 路径」回固定响应的假 TMB 服务器，记下收到的每个请求。"""

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], tuple[int, Any] | Exception] = {}
        self.requests: list[httpx.Request] = []

    def reply(self, method: str, path: str, body: Any, status: int = 200) -> None:
        """让 `path`（接在 `/v1/api` 后面）回 `status` 和 JSON `body`。"""
        self.routes[(method, f"/v1/api{path}")] = (status, body)

    def fail(self, method: str, path: str, error: Exception) -> None:
        """让 `path` 的请求在传输层出错，模拟连不上、超时。"""
        self.routes[(method, f"/v1/api{path}")] = error

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        route = self.routes.get((request.method, request.url.path))
        if route is None:
            return httpx.Response(404, json={"detail": "未找到。"})
        if isinstance(route, Exception):
            raise route
        status, body = route
        return httpx.Response(status, json=body)


@pytest.fixture
def tmb_server(monkeypatch) -> FakeTmbServer:
    """把 `common.tmb_web` 的客户端接到假服务器上。"""
    server = FakeTmbServer()

    def new_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=tmb_web.BASE_URL,
            transport=httpx.MockTransport(server.handle),
            trust_env=False,
        )

    monkeypatch.setattr(tmb_web, "new_client", new_client)
    return server
