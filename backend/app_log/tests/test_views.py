"""app_log/views.py —— 「日志」页取日志、界面的报错报进来，请求出错的原因记进日志

TestClient 不经过 uvicorn，没有访问记录；但它是 httpx 的客户端，每个请求 httpx 会记一条，所以按内容挑记录，不数总条数。
"""

import json

from loguru import logger

from app_log.module.buffer import LogBuffer


def fetch(api_client, session: str | None = None, after: int = 0) -> dict:
    params = {"session": LogBuffer.session if session is None else session, "after": after}
    return api_client.get("/api/logs", params=params).json()


def records_from(api_client, source: str) -> list[dict]:
    return [record for record in fetch(api_client)["records"] if record["source"] == source]


class TestLogs:
    def test_给这次运行的日志和_session(self, api_client):
        logger.info("加载完成")

        body = fetch(api_client)

        assert body["session"] == LogBuffer.session
        [record] = [record for record in body["records"] if record["message"] == "加载完成"]
        assert set(record) == {"seq", "time", "level", "source", "message", "detail"}
        assert (record["level"], record["source"], record["detail"]) == ("INFO", "后端", "")

    def test_只给_seq_之后的(self, api_client):
        logger.info("一")
        seq = max(record["seq"] for record in fetch(api_client)["records"])
        logger.info("二")

        messages = [record["message"] for record in fetch(api_client, after=seq)["records"]]

        assert "二" in messages and "一" not in messages

    def test_session_对不上就从头给(self, api_client):
        logger.info("一")

        messages = [record["message"] for record in fetch(api_client, session="上一次的", after=10**9)["records"]]

        assert "一" in messages


class TestReport:
    def test_界面的报错记成界面来源(self, api_client):
        response = api_client.post(
            "/api/logs",
            json={
                "level": "ERROR",
                "message": "界面出错：x is undefined",
                "detail": "TypeError: x is undefined\n    at setup (SimpleLoadView.vue:12)",
            },
        )

        assert response.status_code == 204
        [record] = records_from(api_client, "界面")
        assert (record["level"], record["message"]) == ("ERROR", "界面出错：x is undefined")
        assert record["detail"] == "TypeError: x is undefined\n    at setup (SimpleLoadView.vue:12)"

    def test_没有内容的不收(self, api_client):
        response = api_client.post("/api/logs", json={"level": "ERROR", "message": ""})

        assert response.status_code == 422


class TestRequestErrors:
    def test_请求参数不对_记下是哪个字段(self, api_client):
        response = api_client.post("/api/simple-load/histories")

        assert response.status_code == 422
        [record] = records_from(api_client, "请求")
        assert (record["level"], record["detail"]) == ("ERROR", "")
        assert record["message"] == "POST /api/simple-load/histories 参数不对：body：Field required"

    def test_好几处不对时详情里逐条列出_不记填的值(self, api_client):
        response = api_client.post("/api/account/login", json={"username": "", "password": 12345678})

        assert response.status_code == 422
        [record] = records_from(api_client, "请求")
        assert record["message"].startswith("POST /api/account/login 参数不对：body.username：")
        assert record["message"].endswith("等 2 处")
        assert [line.split("：")[0] for line in record["detail"].splitlines()] == ["body.username", "body.password"]
        assert "12345678" not in json.dumps(record, ensure_ascii=False)

    def test_业务错误_记下给使用者看的原因(self, api_client, tmp_path):
        missing = tmp_path / "没有这个文件夹"

        response = api_client.post("/api/simple-load/preview", json={"loadDir": str(missing)})

        assert response.status_code == 400
        [record] = records_from(api_client, "请求")
        assert record["level"] == "WARNING"
        assert record["message"] == f"POST /api/simple-load/preview：载荷文件夹不存在：{missing}"

    def test_没登录这类_401_不另记(self, api_client):
        response = api_client.get("/api/account/me")

        assert response.status_code == 401
        assert records_from(api_client, "请求") == []
