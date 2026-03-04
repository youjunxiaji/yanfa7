"""
边缘应力分析 FastAPI 后端

启动方式: uv run main.py
"""

from app_edgeStress.urls import router as edge_stress_router
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


if __name__ == "__main__":
    import sys

    if getattr(sys, "frozen", False):
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
