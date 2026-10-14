"""pytest 公共 fixture

原则：
1. 每个测试都跑在自己的临时目录里，互不干扰；
2. 全局单例（加载完的数据缓存）在每个用例前后自动清空，避免用例之间互相污染；
3. 计算实例默认不推进度，要看进度的用例用 `connected_ws` 接一个假连接。
"""
import asyncio
from pathlib import Path

import pytest

from app_simpleLoad.module.cache import LoadedDataCache
from app_simpleLoad.module.config import AxisMapping, ConversionConfig
from app_simpleLoad.module.cal_simpleLoad import CalSimpleLoad
from app_simpleLoad.module.progress import ProgressReporter
from app_simpleLoad.tests import factories
from app_simpleLoad.tests.factories import Dataset, build_dataset, ramp_case
from app_simpleLoad.tests.fakes import FakeWebSocket, InstantSleepAsyncio

# 真实算例五百多 MB、不入库，放在 backend/测试案例/，不随测试放进 app 里
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REAL_CASE_DIR = BACKEND_ROOT / "测试案例"


# ─── 全局状态隔离 ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_cache():
    """LoadedDataCache 是类属性，用例之间必须清干净。"""
    LoadedDataCache.clear()
    yield
    LoadedDataCache.clear()


# ─── 基础配置 ────────────────────────────────────────────────

@pytest.fixture
def header() -> list[str]:
    """txt 各列的列名（前端列对应展开后的样子）。"""
    return list(factories.DEFAULT_HEADER)


@pytest.fixture
def config() -> ConversionConfig:
    """典型换算配置：力/力矩 N→KN、Nm→KNm，S-N 斜率 4。"""
    return ConversionConfig(
        title_row=0,
        unit_moment=1000.0,
        unit_force=1000.0,
        unit_speed=1.0,
        translate_factor=4.0,
        temperature=40.0,
        tol=1e-6,
    )


@pytest.fixture
def romax_origin() -> list[AxisMapping]:
    """Romax 坐标映射：x←x, y←-z, z←y（即排除原始 y 轴力矩 My）。

    计算层收的是 `AxisMapping` dataclass；发 HTTP 请求时用报文形态
    `factories.ROMAX_ORIGIN`。
    """
    return factories.axis_mappings()


# ─── 合成数据集 ──────────────────────────────────────────────

@pytest.fixture
def dataset(tmp_path: Path) -> Dataset:
    """两个工况、各 4 行的确定性数据集（含 Time 列）。

    - c1 正值、发生次数 100；c2 负值、发生次数 200
    - 工况占比 = 1/3 与 2/3，便于手算
    """
    return build_dataset(
        tmp_path,
        [
            ramp_case("c1", n_rows=4, occurrences=100.0, speed=10.0, sign=1.0),
            ramp_case("c2", n_rows=4, occurrences=200.0, speed=20.0, sign=-1.0, offset=500.0),
        ],
    )


@pytest.fixture
def dataset_no_time(tmp_path: Path) -> Dataset:
    """不含 Time 列的数据集：采样间隔需由频次表的仿真时间反推。"""
    header = [c for c in factories.DEFAULT_HEADER if c != "Time[s]"]
    cases = [
        ramp_case("c1", n_rows=4, occurrences=100.0, speed=10.0, with_time=False),
        ramp_case("c2", n_rows=4, occurrences=200.0, speed=20.0, sign=-1.0, with_time=False),
    ]
    for case in cases:
        case.sim_time = 0.3
    return build_dataset(tmp_path, cases, header=header)


def make_instance(dataset: Dataset, config: ConversionConfig) -> CalSimpleLoad:
    """按数据集参数构造一个已 setInit 的实例（未加载数据）。"""
    instance = CalSimpleLoad()
    instance.setInit(paths=dataset.path_config(), header=dataset.header, config=config)
    return instance


@pytest.fixture
def instance(dataset: Dataset, config: ConversionConfig) -> CalSimpleLoad:
    """已 setInit、尚未读文件的实例。"""
    return make_instance(dataset, config)


@pytest.fixture
async def loaded(instance: CalSimpleLoad) -> CalSimpleLoad:
    """已完成步骤一（加载与预处理）的实例。"""
    await instance.simple_Pre_processing()
    return instance


@pytest.fixture
async def divided(loaded: CalSimpleLoad, romax_origin) -> CalSimpleLoad:
    """已完成步骤二（划分区间）的实例，可直接调用 savePic / simple_load2。"""
    await loaded.simple_load1(romax_origin)
    return loaded


# ─── WebSocket / 进度 ────────────────────────────────────────

@pytest.fixture
def fake_ws() -> FakeWebSocket:
    """记录推送内容的假连接。"""
    return FakeWebSocket()


@pytest.fixture
def connected_ws(instance: CalSimpleLoad, fake_ws: FakeWebSocket) -> FakeWebSocket:
    """把 `instance` 的进度推到假连接上（同一个用例里 loaded、divided 也是这个实例）。"""
    instance.progress = ProgressReporter(fake_ws.send_json)
    return fake_ws


@pytest.fixture
def instant_sleep(monkeypatch):
    """把某个模块里的 asyncio.sleep 变成瞬时返回。

    进度推送本身不 sleep，算法用例看进度前仍会调它；模块没 import asyncio 时直接挂上去，不报错。

    用法::

        instant_sleep(progress_module)
    """

    def _patch(module) -> InstantSleepAsyncio:
        fake = InstantSleepAsyncio(asyncio)
        monkeypatch.setattr(module, "asyncio", fake, raising=False)
        return fake

    return _patch


# ─── HTTP 客户端 ─────────────────────────────────────────────

@pytest.fixture
def api_client():
    """FastAPI 测试客户端：进程内调应用，不开端口。"""
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as client:
        yield client


# ─── 真实测试案例（可选） ────────────────────────────────────

@pytest.fixture(scope="session")
def real_case_dir() -> Path:
    """本地 `测试案例/` 目录；不存在时跳过（该目录不入库）。"""
    folder = REAL_CASE_DIR / "GW-V16-MB-适应性分析载荷-20260210"
    freq = REAL_CASE_DIR / "GW-V16-MB-适应性分析载荷-20260210.xlsx"
    if not folder.is_dir() or not freq.is_file():
        pytest.skip("本地未提供 测试案例/ 数据，跳过真实数据回归")
    return REAL_CASE_DIR
