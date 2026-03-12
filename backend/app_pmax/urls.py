"""Pmax 时间占比 URL 路由配置"""

from fastapi import APIRouter

from app_pmax.views import analyze

router = APIRouter()

router.post("/api/pmax/analyze")(analyze)
