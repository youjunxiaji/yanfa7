"""日志接口：「日志」页取这次运行的日志，界面上的报错报进来；请求出错时把原因记进日志的两个异常处理器"""

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app_log.module.buffer import LogBuffer
from app_log.serializers import LogReportRequest, LogsResponse
from common.constants import LogSource


async def logs(session: str = "", after: int = 0) -> LogsResponse:
    """这次运行的日志，只给 seq 大于 `after` 的；`session` 对不上（后端重启过）就从头给。"""
    if session != LogBuffer.session:
        after = 0
    return LogsResponse(session=LogBuffer.session, records=LogBuffer.since(after))


async def report(req: LogReportRequest) -> None:
    """界面上的报错记进后端的日志，「日志」页和日志文件里都有。"""
    text = f"{req.message}\n{req.detail}" if req.detail else req.message
    logger.bind(source=LogSource.UI).log(req.level.value, text)


async def log_validation_error(request: Request, exc: RequestValidationError) -> Response:
    """请求和模型对不上，多半是前端发错了：记一条错误写明哪个字段，再照 FastAPI 默认的回 422。

    只记字段和原因，不记填的值：登录请求里有密码。
    """
    problems = [f"{'.'.join(str(part) for part in error['loc'])}：{error['msg']}" for error in exc.errors()]
    summary = problems[0] if problems else "报文不对"
    if len(problems) > 1:
        summary += f" 等 {len(problems)} 处"
    lines = [f"{request.method} {request.url.path} 参数不对：{summary}"]
    if len(problems) > 1:
        lines.extend(problems)
    logger.bind(source=LogSource.REQUEST).error("\n".join(lines))
    return await request_validation_exception_handler(request, exc)


async def log_http_error(request: Request, exc: StarletteHTTPException) -> Response:
    """业务错误（400）：把给使用者看的原因记一条警告，再照 FastAPI 默认的回。

    其余状态码看访问记录就够了：401 是要重新登录，连不上 TMB 服务器的 502 在 common/tmb_web.py 里已经记过。
    """
    if exc.status_code == 400:
        logger.bind(source=LogSource.REQUEST).warning(f"{request.method} {request.url.path}：{exc.detail}")
    return await http_exception_handler(request, exc)
