"""app_account/views.py —— 登录、续期、取当前登录的人，经 common/tmb_web.py 转发给 TMB 服务器

假服务器的响应照 tmb_web_v1 的 user_manager 接口写：登录回 `token` + `userInfo`，
续期回 `access` + `refresh`（开了轮换），令牌无效回 401。
"""

import json

import httpx

from common import tmb_web

# tmb_web_v1 的 UserSerializer 给的用户信息
TMB_USER = {
    "username": "603043",
    "chinese_name": "张三",
    "department": "研发七部",
    "position": "仿真",
    "permissions": ["add_simpleloadcalculationhistorymodel"],
    "roles": ["上海-研发七部-效率工具-载荷简化"],
    "is_superuser": False,
    "last_login": None,
}

LOGIN_OK = {
    "token": {"access": "access-1", "refresh": "refresh-1"},
    "userInfo": TMB_USER,
    "session_key": "0123456789abcdef",
}

TOKEN_INVALID = {"detail": "令牌无效或已过期", "code": "token_not_valid"}


class TestLogin:
    def test_转发工号和密码_返回令牌和登录的人(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/login/", LOGIN_OK)

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "secret"}
        )

        assert response.status_code == 200
        assert response.json() == {
            "access": "access-1",
            "refresh": "refresh-1",
            "user": {"username": "603043", "name": "张三", "department": "研发七部"},
        }
        assert json.loads(tmb_server.requests[0].content) == {
            "username": "603043",
            "password": "secret",
        }

    def test_没填中文名时用工号(self, api_client, tmb_server):
        user = {**TMB_USER, "chinese_name": None, "department": None}
        tmb_server.reply("POST", "/users/login/", {**LOGIN_OK, "userInfo": user})

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "secret"}
        )

        assert response.json()["user"] == {"username": "603043", "name": "603043", "department": None}

    def test_账号或密码不对_给出服务器的原话(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/login/", {"detail": "账号或密码不正确"}, status=400)

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "wrong"}
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "账号或密码不正确"

    def test_字段校验错误_取第一条(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/login/", {"password": ["该字段是必填项。"]}, status=400)

        response = api_client.post("/api/account/login", json={"username": "603043", "password": "x"})

        assert response.json()["detail"] == "该字段是必填项。"

    def test_连不上服务器_502_写明地址(self, api_client, tmb_server):
        tmb_server.fail("POST", "/users/login/", httpx.ConnectError("refused"))

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "secret"}
        )

        assert response.status_code == 502
        assert response.json()["detail"] == f"连不上 TMB 服务器（{tmb_web.SERVER}），请检查网络"

    def test_超时_502(self, api_client, tmb_server):
        tmb_server.fail("POST", "/users/login/", httpx.ReadTimeout("slow"))

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "secret"}
        )

        assert response.status_code == 502
        assert "超时" in response.json()["detail"]

    def test_服务器出错_502(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/login/", {"detail": "boom"}, status=500)

        response = api_client.post(
            "/api/account/login", json={"username": "603043", "password": "secret"}
        )

        assert response.status_code == 502
        assert "HTTP 500" in response.json()["detail"]

    def test_没填密码_不找服务器(self, api_client, tmb_server):
        response = api_client.post("/api/account/login", json={"username": "603043", "password": ""})

        assert response.status_code == 422
        assert tmb_server.requests == []


class TestRefresh:
    def test_换回一对新令牌(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/refresh/", {"access": "access-2", "refresh": "refresh-2"})

        response = api_client.post("/api/account/refresh", json={"refresh": "refresh-1"})

        assert response.json() == {"access": "access-2", "refresh": "refresh-2"}
        assert json.loads(tmb_server.requests[0].content) == {"refresh": "refresh-1"}

    def test_服务器没给新的_refresh_就接着用原来的(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/refresh/", {"access": "access-2"})

        response = api_client.post("/api/account/refresh", json={"refresh": "refresh-1"})

        assert response.json() == {"access": "access-2", "refresh": "refresh-1"}

    def test_refresh_过期_401(self, api_client, tmb_server):
        tmb_server.reply("POST", "/users/refresh/", TOKEN_INVALID, status=401)

        response = api_client.post("/api/account/refresh", json={"refresh": "refresh-1"})

        assert response.status_code == 401
        assert response.json()["detail"] == "登录已过期，请重新登录"


class TestMe:
    def test_带着_access_token_去取(self, api_client, tmb_server):
        tmb_server.reply("GET", "/users/user/", {"user": TMB_USER})

        response = api_client.get("/api/account/me", headers={"Authorization": "Bearer access-1"})

        assert response.json() == {"username": "603043", "name": "张三", "department": "研发七部"}
        assert tmb_server.requests[0].headers["Authorization"] == "Bearer access-1"

    def test_没带令牌_401_不找服务器(self, api_client, tmb_server):
        response = api_client.get("/api/account/me")

        assert response.status_code == 401
        assert tmb_server.requests == []

    def test_access_过期_401(self, api_client, tmb_server):
        tmb_server.reply("GET", "/users/user/", TOKEN_INVALID, status=401)

        response = api_client.get("/api/account/me", headers={"Authorization": "Bearer stale"})

        assert response.status_code == 401


class TestClient:
    async def test_不用环境变量里的代理(self, monkeypatch):
        # 开发机上 all_proxy 常是 socks 代理，读了它的话建客户端就报缺 socksio
        monkeypatch.setenv("ALL_PROXY", "socks5://127.0.0.1:7890")

        async with tmb_web.new_client() as client:
            assert client.trust_env is False
