"""
研发七部工具包 FastAPI 后端

开发：`uv run main.py`，起在 8006，热重载。
打包：`uv run python build_backend.py`，Nuitka 编译成 Tauri 外壳的 sidecar，打包后固定 8000。
"""

import os
import sys
import threading
from contextlib import asynccontextmanager

from app_edgeStress.urls import router as edge_stress_router
from app_pmax.urls import router as pmax_router
from app_simpleLoad.module.socket_manager import ConnectionManager
from app_simpleLoad.urls import router as simple_load_router
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from loguru import logger
import uvicorn
import matplotlib
matplotlib.use("Agg")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 载荷简化的计算实例挂在这个连接管理器上，见 app_simpleLoad/module/socket_manager.py
    app.state.websocket_manager = ConnectionManager()
    yield


app = FastAPI(title="Edge Stress API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(edge_stress_router)
app.include_router(pmax_router)
# 载荷简化的接口还是 simple_load 原来的路径：/api/load_file 这类，不带模块前缀。
# 它的 /ws/{client_id} 能匹配任意一段的 /ws/xxx，必须排在边缘应力的 /ws/parse 之后注册，否则会把它截走。
app.include_router(simple_load_router)

SIMPLE_LOAD_PATHS = {route.path for route in simple_load_router.routes if isinstance(route, APIRoute)}


@app.exception_handler(RequestValidationError)
async def on_request_validation_error(request: Request, exc: RequestValidationError):
    """载荷简化的请求体不合法时，仍按业务错误的形状返回，它的前端只认 status 字段。

    这是 simple_load 原来挂在整个应用上的处理器，这里只对载荷简化的接口生效；
    别的工具照常走 FastAPI 默认的 422，它们的前端靠非 2xx 判断出错。
    """
    if request.url.path not in SIMPLE_LOAD_PATHS:
        return await request_validation_exception_handler(request, exc)
    details = "；".join(
        f"{'.'.join(str(part) for part in error['loc'][1:])}: {error['msg']}"
        for error in exc.errors()
    )
    logger.error(f"请求参数不合法: {details}")
    return JSONResponse(
        status_code=200,
        content={"message": f"请求参数不合法: {details}", "status": "error"},
    )


def exit_with_parent() -> None:
    """父进程关掉 stdin 时退出。

    Tauri 外壳拉起 sidecar 时 stdin 是管道。外壳正常退出会结束 sidecar；崩溃或被强杀时来不及，
    但管道会断。读到 EOF 就退出，不留一个占着 8000 端口的孤儿进程。
    """
    if sys.stdin is None:
        return

    def watch() -> None:
        while sys.stdin.buffer.read(4096):
            pass
        os._exit(0)

    threading.Thread(target=watch, daemon=True).start()


if __name__ == "__main__":
    # Nuitka 编译后的模块里有 __compiled__；它不设 sys.frozen，那是 PyInstaller 的。
    # 前端按同样的规则选端口，见 frontend/src/renderer/src/api/backend.ts。
    if "__compiled__" in globals():
        # 打包后由 Tauri 外壳带 --sidecar 拉起，见 frontend/src-tauri/src/backend.rs。
        # 只听本机：不弹 Windows 防火墙提示，局域网里也连不进来。
        if "--sidecar" in sys.argv[1:]:
            exit_with_parent()
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
