"""app_simpleLoad/module/progress.py —— 进度推送"""

import pytest

from app_simpleLoad.module.progress import ProgressReporter
from app_simpleLoad.tests.fakes import FakeWebSocket


@pytest.fixture
def receiver() -> FakeWebSocket:
    return FakeWebSocket()


@pytest.fixture
def reporter(receiver: FakeWebSocket) -> ProgressReporter:
    return ProgressReporter(receiver.send_json)


class TestPush:
    async def test_每条消息带当前阶段和进度(self, reporter, receiver):
        await reporter.send_text("开始处理")
        await reporter.send_progress(33.333333)

        assert receiver.sent_json == [
            {"type": "progress", "stage": "开始处理", "percent": 0.0},
            {"type": "progress", "stage": "开始处理", "percent": 33.3},
        ]

    async def test_没给发送函数时只记不推(self):
        reporter = ProgressReporter()

        await reporter.send_text("没人听")
        await reporter.send_progress(50)

        assert (reporter.stage, reporter.percent) == ("没人听", 50.0)

    async def test_推送失败后不再推也不抛错(self):
        receiver = FakeWebSocket(fail_on_send=True)
        reporter = ProgressReporter(receiver.send_json)

        await reporter.send_text("连接已经断了")
        receiver.fail_on_send = False
        await reporter.send_progress(80)

        assert receiver.sent_json == []
        assert reporter.percent == 80.0


class TestSpan:
    async def test_默认按整段报(self, reporter, receiver):
        await reporter.send_progress(42)

        assert receiver.progresses == [42.0]

    async def test_一段的进度换算到总进度的一截(self, reporter, receiver):
        reporter.span(90, 100)

        for value in (0, 50, 100):
            await reporter.send_progress(value)

        assert receiver.progresses == [90.0, 95.0, 100.0]
