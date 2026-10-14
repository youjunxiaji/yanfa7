"""进度推送器 — 把计算进度推给前端"""

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger


class ProgressReporter:
    """每次更新推一条 `{"type": "progress", "stage": 当前阶段, "percent": 0~100}`。

    不给 send 时只记下阶段和进度，不推；推送失败（连接断了）后不再推，计算照常做完。
    一条 WebSocket 里会跑几段计算，每段都按 0~100 报进度，`span` 把接下来那段映射到总进度的一截。
    """

    def __init__(self, send: Callable[[dict[str, Any]], Awaitable[None]] | None = None):
        self._send = send
        self._low = 0.0
        self._high = 100.0
        self.stage = ""
        self.percent = 0.0

    def span(self, low: float, high: float):
        """接下来报的 0~100 换算到总进度的 low~high。"""
        self._low = low
        self._high = high

    async def send_text(self, message: str):
        """更新当前阶段的说明。"""
        self.stage = message
        await self._push()

    async def send_progress(self, value: float):
        """更新这一段的进度（0-100）。"""
        self.percent = round(self._low + (self._high - self._low) * value / 100, 1)
        await self._push()

    async def _push(self):
        if self._send is None:
            return
        try:
            await self._send({"type": "progress", "stage": self.stage, "percent": self.percent})
        except Exception as e:
            logger.warning(f"进度推送失败，后面不再推送：{e}")
            self._send = None
