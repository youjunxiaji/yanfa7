"""日志 URL 路由配置"""

from fastapi import APIRouter

from app_log.views import logs, report

router = APIRouter()

router.get("/api/logs")(logs)
router.post("/api/logs", status_code=204)(report)
