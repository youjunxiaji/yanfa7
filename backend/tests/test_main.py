"""main.py —— 应用装配

simple_load 的 main.py 没有搬过来，载荷简化在 yanfa7 的 main.py 里装配；它的启动横幅随之不要了。
"""

from fastapi.middleware.cors import CORSMiddleware

import main
from my_websockets.socket_manager import ConnectionManager


class TestAppWiring:
    def test_业务接口挂在_api_前缀下(self):
        paths = {route.path for route in main.app.routes}

        assert {"/api/load_file", "/api/divide_interval", "/api/reduce_load"} <= paths

    def test_websocket_路由已注册(self):
        paths = {route.path for route in main.app.routes}

        assert "/ws/{client_id}" in paths

    def test_开启了_CORS(self):
        assert any(m.cls is CORSMiddleware for m in main.app.user_middleware)

    def test_lifespan_里初始化连接管理器(self, api_client):
        assert isinstance(api_client.app.state.websocket_manager, ConnectionManager)

    def test_websocket_路由排在边缘应力之后(self):
        paths = [route.path for route in main.app.routes]

        assert paths.index("/ws/parse") < paths.index("/ws/{client_id}")

    def test_校验失败折成_200_只对载荷简化生效(self, api_client):
        # 别的工具（这里拿 Pmax）照常 422，它们的前端靠非 2xx 判断出错
        response = api_client.post("/api/pmax/analyze", json={})

        assert response.status_code == 422
