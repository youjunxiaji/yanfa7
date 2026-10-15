"""日志测试的 fixture"""

import pytest

from app_log.module.buffer import LogBuffer


@pytest.fixture(autouse=True)
def _empty_buffer():
    """每个用例从空的日志开始；main.py 还没导入过时先接上。"""
    LogBuffer.install()
    LogBuffer.clear()
    yield
    LogBuffer.clear()


@pytest.fixture
def api_client():
    """FastAPI 测试客户端：进程内调应用，不开端口。"""
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as client:
        yield client
