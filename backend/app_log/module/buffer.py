"""这次运行的日志：loguru 照常打到 stderr，另在内存里留最近一段给「日志」页

- stderr：开发时在跑 `uv run main.py` 的终端里；打包后外壳写进这次运行的日志文件（frontend/src-tauri/src/backend.rs）。
- 内存：只留 INFO 及以上的最近 `LogBuffer.MAX_RECORDS` 条，进程重启就没了。
- 标准库 logging（uvicorn、httpx 这些）经 `StdlibInterceptHandler` 转进 loguru，和后端自己写的一起记。
"""

import inspect
import logging
import re
import threading
import traceback
from collections import deque
from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from loguru import logger

from app_log.serializers import LogEntry
from common.constants import LogLevel, LogSource

if TYPE_CHECKING:
    from loguru import Message


class LogBuffer:
    """内存里这次运行的最近几条日志，给「日志」页增量取

    每条带这次运行里递增的 seq，前端带着上次取到的 seq 来只取新的。session 每次启动换一个，
    前端发现它变了（开发时热重载、打包后重开应用）就从头取。
    """

    MAX_RECORDS: ClassVar[int] = 2000
    session: ClassVar[str] = uuid4().hex

    _records: ClassVar[deque[LogEntry]] = deque(maxlen=MAX_RECORDS)
    _seq: ClassVar[int] = 0
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _installed: ClassVar[bool] = False

    @classmethod
    def install(cls) -> None:
        """接上 loguru 和标准库 logging，main.py 导入时调。

        开发时热重载的子进程会把 main.py 执行两遍（multiprocessing 的 `__mp_main__` 一遍、uvicorn 导入
        `main` 一遍），sink 和根 logger 的 handler 只装一次，不然每条日志进内存两次。uvicorn 的 logger
        每次都摘掉自己的 handler、交给根 logger：uvicorn 配日志时会装回去，两遍之间就配过一次。
        打包后 main.py 只执行一遍、之后才起 uvicorn，所以还要用 `log_config=None` 起，不让它配。
        """
        if not cls._installed:
            cls._installed = True
            logger.add(cls.sink, level="INFO", format="{message}")
            logging.root.addHandler(StdlibInterceptHandler())
            logging.root.setLevel(logging.INFO)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            named = logging.getLogger(name)
            named.handlers.clear()
            named.propagate = True

    @classmethod
    def sink(cls, message: "Message") -> None:
        """loguru 的 sink：一条日志换成「日志」页的一行。第一行当内容，其余几行和报错堆栈进详情。"""
        record = message.record
        first, _, rest = record["message"].partition("\n")
        details = [rest] if rest else []
        if record["exception"] is not None:
            exc_type, exc_value, exc_traceback = record["exception"]
            details.append("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        with cls._lock:
            cls._seq += 1
            cls._records.append(
                LogEntry(
                    seq=cls._seq,
                    time=record["time"].isoformat(timespec="milliseconds"),
                    level=cls.level_of(record["level"].no),
                    source=record["extra"].get("source", LogSource.BACKEND),
                    message=first,
                    detail="\n".join(details).rstrip(),
                )
            )

    @staticmethod
    def level_of(no: int) -> LogLevel:
        """loguru 的级别号换成「日志」页的三级：SUCCESS 算信息，CRITICAL 算错误。"""
        if no >= logging.ERROR:
            return LogLevel.ERROR
        if no >= logging.WARNING:
            return LogLevel.WARNING
        return LogLevel.INFO

    @classmethod
    def since(cls, after: int) -> list[LogEntry]:
        """seq 大于 `after` 的几条，按先后排。"""
        with cls._lock:
            return [entry for entry in cls._records if entry.seq > after]

    @classmethod
    def clear(cls) -> None:
        """清掉内存里的日志，seq 接着往后编；测试用。"""
        with cls._lock:
            cls._records.clear()


class StdlibInterceptHandler(logging.Handler):
    """标准库 logging 的记录转给 loguru，级别和调用位置照原样

    uvicorn 的访问记录改写成「方法 路径 状态码」，按状态码分级；WebSocket 握手同样改写，websockets 库
    每次连上、断开打的 connection open / closed 不记。「日志」页自己轮询的请求也不记，不然每秒一条。
    """

    QUIET_PATH: ClassVar[str] = "/api/logs"
    WEBSOCKET_LINE: ClassVar[re.Pattern[str]] = re.compile(r'^\S+ - "(WebSocket \S+)" (.+)$')
    WEBSOCKET_NOISE: ClassVar[frozenset[str]] = frozenset({"connection open", "connection closed"})

    def emit(self, record: logging.LogRecord) -> None:
        """访问记录和 uvicorn 自己的输出要改写，其余照原样转。"""
        try:
            if record.name == "uvicorn.access":
                self.emit_access(record)
            elif record.name == "uvicorn.error":
                self.emit_server(record)
            else:
                self.forward(record)
        except Exception:
            self.handleError(record)

    def emit_access(self, record: logging.LogRecord) -> None:
        """HTTP 访问记录：uvicorn 给的参数依次是客户端、方法、路径、HTTP 版本、状态码。"""
        args = record.args
        if not (isinstance(args, tuple) and len(args) == 5 and isinstance(args[4], int)):
            self.forward(record, source=LogSource.REQUEST)
            return
        _, method, path, _, status = args
        if str(path).startswith(self.QUIET_PATH):
            return
        self.forward(
            record,
            level=self.level_of_status(status),
            message=f"{method} {path} {status}",
            source=LogSource.REQUEST,
        )

    def emit_server(self, record: logging.LogRecord) -> None:
        """uvicorn 自己的输出：WebSocket 握手改写成「WebSocket 路径 结果」，连上、断开的不记。"""
        if isinstance(record.msg, str) and record.msg in self.WEBSOCKET_NOISE:
            return
        line = self.WEBSOCKET_LINE.match(record.getMessage())
        if line is None:
            self.forward(record)
            return
        target, result = line.groups()
        if result == "[accepted]":
            self.forward(record, message=f"{target} 已连接", source=LogSource.REQUEST)
            return
        status = int(result) if result.isdigit() else 0
        self.forward(
            record,
            level=self.level_of_status(status),
            message=f"{target} {result}",
            source=LogSource.REQUEST,
        )

    @staticmethod
    def level_of_status(status: int) -> LogLevel:
        """4xx 记警告，5xx 记错误，其余是信息。"""
        if status >= 500:
            return LogLevel.ERROR
        if status >= 400:
            return LogLevel.WARNING
        return LogLevel.INFO

    def forward(
        self,
        record: logging.LogRecord,
        *,
        level: LogLevel | None = None,
        message: str | None = None,
        source: LogSource | None = None,
    ) -> None:
        """转给 loguru。调用位置取标准库 logging 外面那一层，stderr 里看得出是谁打的。

        Args:
            record: 标准库 logging 的记录。
            level: 改写后的级别，不给就照原样。
            message: 改写后的内容，不给就照原样。
            source: 「日志」页显示的来源，不给是后端。
        """
        name: str | int
        if level is not None:
            name = level.value
        else:
            try:
                name = logger.level(record.levelname).name
            except ValueError:
                name = record.levelno
        frame, depth = inspect.currentframe(), 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename in (logging.__file__, __file__)):
            frame = frame.f_back
            depth += 1
        bound = logger.bind(source=source) if source is not None else logger
        bound.opt(depth=depth, exception=record.exc_info).log(
            name, message if message is not None else record.getMessage()
        )
