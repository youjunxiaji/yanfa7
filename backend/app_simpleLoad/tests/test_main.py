"""main.py —— 应用装配

simple_load 的 main.py 没有搬过来，载荷简化在 yanfa7 的 main.py 里装配。
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute, APIWebSocketRoute

import main


class TestAppWiring:
    def test_接口挂在模块前缀下(self):
        paths = {route.path for route in main.app.routes if isinstance(route, APIRoute)}

        assert {"/api/simple-load/preview", "/api/simple-load/clear"} <= paths

    def test_加载和缩减各一条_WebSocket(self):
        paths = {route.path for route in main.app.routes if isinstance(route, APIWebSocketRoute)}

        assert {"/ws/simple-load/load", "/ws/simple-load/reduce"} <= paths

    def test_开启了_CORS(self):
        assert any(m.cls is CORSMiddleware for m in main.app.user_middleware)

    def test_请求体不合法时照常返回_422(self, api_client):
        response = api_client.post("/api/simple-load/preview", json={})

        assert response.status_code == 422
