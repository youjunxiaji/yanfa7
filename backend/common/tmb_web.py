"""TMB 服务器（tmb_web_v1）的 HTTP 客户端

账号登录、续期经它转发给 TMB 服务器。渲染层不直连：webview 的源不在 tmb_web_v1 的 CORS 白名单里，
业务数据也按项目规则只走本地后端。JWT 存在渲染层，要登录的接口经 Authorization 头带过来，这里只转发、不留存。
"""

from typing import Any

import httpx
from fastapi import HTTPException
from loguru import logger

# 开发和打包都连生产服务器，历史记录在生产库里
BASE_URL = "http://10.0.3.198/v1/api"

# 报错时给使用者看的服务器地址
SERVER = httpx.URL(BASE_URL).netloc.decode()

# 连接 5 秒连不上就报错，不让登录框一直转圈
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def new_client() -> httpx.AsyncClient:
    """开一个连 TMB 服务器的客户端。

    `trust_env=False`：不用系统和环境变量里的代理。内网服务器直连就行；开发机上 `all_proxy` 是 socks
    代理的话，httpx 建客户端时就会因为缺 socksio 报错。

    Returns:
        用完要关闭的异步客户端。
    """
    return httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT, trust_env=False)


def bearer_token(authorization: str | None) -> str:
    """从 Authorization 头取出 access token。

    Args:
        authorization: 请求头原文，形如 `Bearer <token>`。

    Returns:
        access token。

    Raises:
        HTTPException: 没带令牌，按未登录处理（401）。
    """
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="还没有登录")
    return token.strip()


def first_message(value: Any) -> str | None:
    """取 DRF 报错里给人看的第一句话：优先 `detail`，其次第一个字段错误。

    Args:
        value: 响应体 JSON，或其中的一部分。

    Returns:
        找到的第一条非空文字，没有时为 None。
    """
    if isinstance(value, str):
        return value or None
    if isinstance(value, list):
        return next((text for item in value if (text := first_message(item))), None)
    if isinstance(value, dict):
        return first_message(value.get("detail")) or next(
            (text for item in value.values() if (text := first_message(item))), None
        )
    return None


async def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: Any = None,
    params: dict[str, str] | None = None,
) -> Any:
    """调 TMB 服务器的接口，返回解析好的 JSON。

    Args:
        method: HTTP 方法。
        path: 接口路径，接在 `BASE_URL` 后面，如 `/users/login/`。
        token: access token，要登录的接口才给。
        json: 请求体。
        params: 查询参数。

    Returns:
        响应体 JSON。

    Raises:
        HTTPException: 401 是令牌过期或无效，前端续期后重试，续期也不行就要重新登录；连不上、超时、
            服务器出错是 502；其余是 400，`detail` 取服务器给的原因（如「账号或密码不正确」）。
    """
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        async with new_client() as client:
            response = await client.request(method, path, headers=headers, json=json, params=params)
    except httpx.TimeoutException as e:
        logger.warning(f"TMB 服务器超时：{method} {path}")
        raise HTTPException(status_code=502, detail="TMB 服务器响应超时，请稍后再试") from e
    except httpx.HTTPError as e:
        logger.warning(f"连不上 TMB 服务器：{method} {path}：{e!r}")
        raise HTTPException(
            status_code=502, detail=f"连不上 TMB 服务器（{SERVER}），请检查网络"
        ) from e

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    if response.status_code >= 500:
        logger.warning(f"TMB 服务器出错：{method} {path} → HTTP {response.status_code}")
        raise HTTPException(
            status_code=502, detail=f"TMB 服务器出错（HTTP {response.status_code}），请稍后再试"
        )
    try:
        body = response.json()
    except ValueError as e:
        raise HTTPException(
            status_code=502, detail=f"TMB 服务器返回的不是 JSON（HTTP {response.status_code}）"
        ) from e
    if response.is_error:
        raise HTTPException(
            status_code=400,
            detail=first_message(body) or f"TMB 服务器拒绝了请求（HTTP {response.status_code}）",
        )
    return body
