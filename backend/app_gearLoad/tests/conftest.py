"""齿轮载荷接口测试的 fixture；假 TMB 服务器 `tmb_server` 几个 app 共用，在 backend/conftest.py"""

import pytest


@pytest.fixture
def api_client():
    """FastAPI 测试客户端：进程内调应用，不开端口。"""
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as client:
        yield client
