"""载荷简化 URL 路由配置"""

from fastapi import APIRouter

from app_simpleLoad.views import load_file, simple_load, simple_pre_processing, websocket_endpoint

router = APIRouter()

router.post("/api/load_file")(load_file)
router.post("/api/divide_interval")(simple_pre_processing)
router.post("/api/reduce_load")(simple_load)
router.websocket("/ws/{client_id}")(websocket_endpoint)
