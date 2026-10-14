"""账号 URL 路由配置"""

from fastapi import APIRouter

from app_account.views import login, me, refresh

router = APIRouter()

router.post("/api/account/login")(login)
router.post("/api/account/refresh")(refresh)
router.get("/api/account/me")(me)
