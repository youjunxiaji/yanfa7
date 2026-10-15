"""载荷简化 URL 路由配置"""

from fastapi import APIRouter

from app_simpleLoad.views import clear, histories, preview, save_history, ws_load, ws_reduce

router = APIRouter()

router.post("/api/simple-load/preview")(preview)
router.post("/api/simple-load/clear", status_code=204)(clear)
router.get("/api/simple-load/histories")(histories)
router.post("/api/simple-load/histories")(save_history)
router.websocket("/ws/simple-load/load")(ws_load)
router.websocket("/ws/simple-load/reduce")(ws_reduce)
