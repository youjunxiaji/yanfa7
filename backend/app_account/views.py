"""账号接口：登录、续期、取当前登录的人，都转发给 TMB 服务器（tmb_web_v1）

令牌存在渲染层；取当前登录的人这类要登录的接口，经 Authorization 头带 access token 过来。
"""

from typing import Annotated

from fastapi import Header
from loguru import logger

from app_account.serializers import (
    AccountUser,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenPair,
)
from common import tmb_web


async def login(req: LoginRequest) -> LoginResponse:
    """用工号和密码登录 TMB 服务器，拿 JWT 和用户信息。

    TMB 服务器同一账号只留一处登录：这里登录成功，它会通知网页版上的这个账号下线。
    """
    data = await tmb_web.request("POST", "/users/login/", json=req.model_dump())
    user = AccountUser.from_tmb(data["userInfo"])
    logger.info(f"已登录 TMB 服务器：{user.username} {user.name}")
    return LoginResponse(access=data["token"]["access"], refresh=data["token"]["refresh"], user=user)


async def refresh(req: RefreshRequest) -> TokenPair:
    """用 refresh token 换一对新令牌；refresh token 过期了回 401，要重新登录。"""
    data = await tmb_web.request("POST", "/users/refresh/", json={"refresh": req.refresh})
    # tmb_web_v1 开了 ROTATE_REFRESH_TOKENS，会给新的 refresh；没给就接着用原来的
    return TokenPair(access=data["access"], refresh=data.get("refresh") or req.refresh)


async def me(authorization: Annotated[str | None, Header()] = None) -> AccountUser:
    """取当前登录的人；前端启动时用它确认登录还有效，顺带更新姓名和部门。"""
    token = tmb_web.bearer_token(authorization)
    data = await tmb_web.request("GET", "/users/user/", token=token)
    return AccountUser.from_tmb(data["user"])
