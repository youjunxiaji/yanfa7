"""
研发七部工具包 FastAPI 后端

开发：`uv run main.py`，起在 8006，热重载。
打包：`uv run python build_backend.py`，Nuitka 编译成 Tauri 外壳的 sidecar，打包后固定 8000。
"""

import os
import sys
import threading

from app_account.urls import router as account_router
from app_edgeStress.urls import router as edge_stress_router
from app_log.module.buffer import LogBuffer
from app_log.urls import router as log_router
from app_log.views import log_http_error, log_validation_error
from app_pmax.urls import router as pmax_router
from app_simpleLoad.urls import router as simple_load_router
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import matplotlib
matplotlib.use("Agg")

# 先接上日志：后面 uvicorn 的输出、各模块写的日志都要进「日志」页
LogBuffer.install()

app = FastAPI(title="Edge Stress API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求出错时把原因记进日志，响应照 FastAPI 默认的
app.exception_handler(RequestValidationError)(log_validation_error)
app.exception_handler(StarletteHTTPException)(log_http_error)

app.include_router(account_router)
app.include_router(edge_stress_router)
app.include_router(log_router)
app.include_router(pmax_router)
app.include_router(simple_load_router)


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
    # log_config=None：uvicorn 不装自己的 handler，输出全走 loguru（见 app_log/module/buffer.py）。
    if "__compiled__" in globals():
        # 打包后由 Tauri 外壳带 --sidecar 拉起，见 frontend/src-tauri/src/backend.rs。
        # 只听本机：不弹 Windows 防火墙提示，局域网里也连不进来。
        if "--sidecar" in sys.argv[1:]:
            exit_with_parent()
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True, log_config=None)
