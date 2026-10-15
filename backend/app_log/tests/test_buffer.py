"""app_log/module/buffer.py —— 内存里的日志，和标准库 logging 的转接

标准库 logging 的记录照 uvicorn 打的样子造：访问记录的参数依次是客户端、方法、路径、HTTP 版本、状态码。
"""

import logging
from collections import deque

from loguru import logger

from app_log.module.buffer import LogBuffer, StdlibInterceptHandler
from common.constants import LogLevel, LogSource


def entries():
    return LogBuffer.since(0)


def stdlib_record(name: str, msg: str, args: tuple | None = None) -> logging.LogRecord:
    return logging.LogRecord(name, logging.INFO, __file__, 1, msg, args, None)


def access_record(path: str, status: int) -> logging.LogRecord:
    """uvicorn 的一条访问记录。"""
    return stdlib_record(
        "uvicorn.access", '%s - "%s %s HTTP/%s" %d', ("127.0.0.1:50000", "POST", path, "1.1", status)
    )


class TestBuffer:
    def test_后端写的日志进内存(self):
        logger.info("加载完成")

        [entry] = entries()

        assert (entry.level, entry.source, entry.message, entry.detail) == (
            LogLevel.INFO,
            LogSource.BACKEND,
            "加载完成",
            "",
        )

    def test_DEBUG_不进内存(self):
        logger.debug("细节")

        assert entries() == []

    def test_多行的第一行当内容_其余进详情(self):
        logger.warning("第一行\n第二行\n第三行")

        [entry] = entries()

        assert (entry.level, entry.message, entry.detail) == (LogLevel.WARNING, "第一行", "第二行\n第三行")

    def test_报错带堆栈(self):
        try:
            1 / 0
        except ZeroDivisionError:
            logger.exception("算错了")

        [entry] = entries()

        assert (entry.level, entry.message) == (LogLevel.ERROR, "算错了")
        assert "Traceback" in entry.detail and "ZeroDivisionError" in entry.detail

    def test_CRITICAL_算错误_SUCCESS_算信息(self):
        logger.critical("崩了")
        logger.success("好了")

        assert [entry.level for entry in entries()] == [LogLevel.ERROR, LogLevel.INFO]

    def test_只取_seq_之后的(self):
        logger.info("一")
        seq = entries()[-1].seq
        logger.info("二")

        assert [entry.message for entry in LogBuffer.since(seq)] == ["二"]

    def test_只留最近的(self, monkeypatch):
        monkeypatch.setattr(LogBuffer, "_records", deque(maxlen=3))

        for index in range(5):
            logger.info(f"第 {index} 条")

        assert [entry.message for entry in entries()] == ["第 2 条", "第 3 条", "第 4 条"]

    def test_重复安装只记一次(self):
        LogBuffer.install()

        logger.info("一次")

        assert len(entries()) == 1


class TestStdlibIntercept:
    def test_标准库_logging_转进来(self):
        logging.getLogger("httpx").info('HTTP Request: GET http://10.0.3.198/v1/api/users/user/ "HTTP/1.1 200 OK"')

        [entry] = entries()

        assert (entry.level, entry.source) == (LogLevel.INFO, LogSource.BACKEND)
        assert entry.message.startswith("HTTP Request: GET")

    def test_访问记录改写成方法路径状态码_按状态码分级(self):
        handler = StdlibInterceptHandler()

        for status in (200, 422, 500):
            handler.handle(access_record("/api/simple-load/histories", status))

        assert [(entry.level, entry.source, entry.message) for entry in entries()] == [
            (LogLevel.INFO, LogSource.REQUEST, "POST /api/simple-load/histories 200"),
            (LogLevel.WARNING, LogSource.REQUEST, "POST /api/simple-load/histories 422"),
            (LogLevel.ERROR, LogSource.REQUEST, "POST /api/simple-load/histories 500"),
        ]

    def test_日志页自己轮询的不记(self):
        StdlibInterceptHandler().handle(access_record("/api/logs?session=abc&after=3", 200))

        assert entries() == []

    def test_WebSocket_握手改写_连上断开的不记(self):
        handler = StdlibInterceptHandler()

        handler.handle(
            stdlib_record("uvicorn.error", '%s - "WebSocket %s" [accepted]', ("127.0.0.1:50000", "/ws/simple-load/load"))
        )
        handler.handle(stdlib_record("uvicorn.error", "connection open"))
        handler.handle(stdlib_record("uvicorn.error", "connection closed"))

        assert [(entry.source, entry.message) for entry in entries()] == [
            (LogSource.REQUEST, "WebSocket /ws/simple-load/load 已连接")
        ]

    def test_WebSocket_被拒记警告(self):
        StdlibInterceptHandler().handle(
            stdlib_record("uvicorn.error", '%s - "WebSocket %s" 403', ("127.0.0.1:50000", "/ws/nowhere"))
        )

        [entry] = entries()

        assert (entry.level, entry.message) == (LogLevel.WARNING, "WebSocket /ws/nowhere 403")

    def test_uvicorn_的报错带堆栈(self):
        try:
            raise RuntimeError("坏了")
        except RuntimeError:
            logging.getLogger("uvicorn.error").exception("Exception in ASGI application")

        [entry] = entries()

        assert (entry.level, entry.source, entry.message) == (
            LogLevel.ERROR,
            LogSource.BACKEND,
            "Exception in ASGI application",
        )
        assert "RuntimeError: 坏了" in entry.detail
