"""日志 Pydantic 序列化模型：「日志」页取的日志，和界面报上来的报错

字段名用 camelCase，和前端 `api/logs.ts` 一致。
"""

from pydantic import BaseModel, Field

from common.constants import LogLevel, LogSource


class LogEntry(BaseModel):
    """「日志」页的一行"""

    seq: int  # 这次运行里的序号，从 1 起递增
    time: str  # 本机时间，ISO 8601，到毫秒
    level: LogLevel
    source: LogSource
    message: str  # 第一行
    detail: str = ""  # 其余几行和报错堆栈


class LogsResponse(BaseModel):
    """GET /api/logs"""

    session: str  # 后端这次运行的标识，变了说明后端重启过
    records: list[LogEntry]


class LogReportRequest(BaseModel):
    """POST /api/logs：界面上的报错，记进后端的日志"""

    level: LogLevel
    message: str = Field(min_length=1)
    detail: str = ""  # 堆栈
