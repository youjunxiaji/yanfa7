"""账号 Pydantic 序列化模型：登录、续期的请求和响应

字段名用 camelCase，和前端 `api/account.ts` 一致。用户信息只挑界面要显示的几项，
TMB 服务器返回的权限、角色这些不往前端传。
"""

from typing import Any, Self

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """POST /api/account/login"""

    username: str = Field(min_length=1)  # 工号
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    """POST /api/account/refresh"""

    refresh: str = Field(min_length=1)


class TokenPair(BaseModel):
    """TMB 服务器签发的 JWT：access 15 分钟过期，refresh 7 天；续期时两个都换新的，refresh 重新计 7 天"""

    access: str
    refresh: str


class AccountUser(BaseModel):
    """当前登录的人"""

    username: str  # 工号
    name: str  # 中文名，没填时用工号
    department: str | None = None

    @classmethod
    def from_tmb(cls, user: dict[str, Any]) -> Self:
        """从 TMB 服务器的用户信息（tmb_web_v1 的 `UserSerializer`）里挑出界面要显示的几项。

        Args:
            user: 登录接口的 `userInfo`，或当前用户接口的 `user`。

        Returns:
            界面显示用的用户信息。
        """
        username = str(user["username"])
        return cls(
            username=username,
            name=user.get("chinese_name") or username,
            department=user.get("department"),
        )


class LoginResponse(TokenPair):
    """登录成功：一对令牌和登录的人"""

    user: AccountUser
