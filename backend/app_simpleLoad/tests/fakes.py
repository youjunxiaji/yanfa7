"""测试替身（fake / stub）

只放「假对象」，不放 fixture —— fixture 在 conftest.py 里组装。
"""
import asyncio
from typing import Any


class FakeWebSocket:
    """进度推送的接收端：记录 send_json 收到的消息，可通过 fail_on_send 模拟连接已断。"""

    def __init__(self, *, fail_on_send: bool = False) -> None:
        self.sent_json: list[dict[str, Any]] = []
        self.fail_on_send = fail_on_send

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.fail_on_send:
            raise RuntimeError("连接已关闭")
        self.sent_json.append(payload)

    # ── 便捷断言 ──────────────────────────────────────────
    @property
    def texts(self) -> list[str]:
        """推过的阶段说明，相邻重复的只留一条。"""
        texts: list[str] = []
        for message in self.sent_json:
            stage = message["stage"]
            if stage and (not texts or texts[-1] != stage):
                texts.append(stage)
        return texts

    @property
    def progresses(self) -> list[float]:
        return [float(message["percent"]) for message in self.sent_json]


class RecordingProgress:
    """ProgressReporter 的替身：只记录，不推送。"""

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.progresses: list[float] = []

    async def send_text(self, message: str) -> None:
        self.texts.append(message)

    async def send_progress(self, value: float) -> None:
        self.progresses.append(float(value))


class InstantSleepAsyncio:
    """asyncio 模块的替身：sleep 立即返回，其余属性透传给真 asyncio。

    用于把 sleep 循环压缩到 0 耗时::

        monkeypatch.setattr(some_module, "asyncio", InstantSleepAsyncio())
    """

    def __init__(self, real: Any = asyncio) -> None:
        self._real = real
        self.slept: list[float] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    async def sleep(self, delay: float, result: Any = None) -> Any:
        self.slept.append(delay)
        return result
