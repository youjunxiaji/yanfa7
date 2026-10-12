"""
边缘应力分析 FastAPI 后端

启动方式: uv run main.py
"""

from app_edgeStress.urls import router as edge_stress_router
from app_pmax.urls import router as pmax_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import matplotlib
matplotlib.use("Agg")


app = FastAPI(title="Edge Stress API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(edge_stress_router)
app.include_router(pmax_router)


if __name__ == "__main__":
    import sys

    # 打包后的后端固定 8000；开发时 `uv run main.py` 起在 8006。
    # 前端按同样的规则选端口，见 frontend/src/renderer/src/api/backend.ts。
    if getattr(sys, "frozen", False):
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
