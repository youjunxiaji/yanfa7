"""边缘应力 URL 路由配置"""

from fastapi import APIRouter

from app_edgeStress.views import ws_parse, get_chart_data, update_stress_point, regenerate_polar

router = APIRouter()

router.websocket("/ws/parse")(ws_parse)
router.get("/api/chart-data")(get_chart_data)
router.post("/api/update-stress-point")(update_stress_point)
router.post("/api/regenerate-polar")(regenerate_polar)
