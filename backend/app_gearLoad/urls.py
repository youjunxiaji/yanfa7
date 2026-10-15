"""齿轮载荷 URL 路由配置"""

from fastapi import APIRouter

from app_gearLoad.views import calculate, export_excel, histories, history, save_history

router = APIRouter()

router.post("/api/gear-load/calculate")(calculate)
router.post("/api/gear-load/export")(export_excel)
router.get("/api/gear-load/histories")(histories)
router.post("/api/gear-load/histories")(save_history)
router.get("/api/gear-load/histories/{record_id}")(history)
