"""app_simpleLoad/views.py —— 预览、清空两个 HTTP 接口，加载、缩减两条 WebSocket

WebSocket 用 TestClient 在进程内连，跑的是真实计算，数据是 conftest 里两个工况各 4 行的合成数据集。
"""

import json

import pytest

from app_simpleLoad import views as views_module
from app_simpleLoad.module.cache import LoadedDataCache
from app_simpleLoad.tests import factories
from app_simpleLoad.tests.excel_io import read_gl, read_romax
from app_simpleLoad.tests.factories import build_dataset, ramp_case
from app_simpleLoad.tests.test_reduce_load import DEFAULT_BINS, SELECTED_COLUMNS

LOAD_PATH = "/ws/simple-load/load"
REDUCE_PATH = "/ws/simple-load/reduce"


def load_message(dataset, **overrides) -> dict:
    """加载数据时前端发的参数：合成数据集第一行是列名，跳过 1 行。"""
    body = {
        "loadDir": str(dataset.load_dir),
        "freqTablePath": str(dataset.freq_path),
        "columns": dataset.header,
        "skipRows": 1,
        "unitForce": 1000,
        "unitMoment": 1000,
        "unitSpeed": 1,
    }
    body.update(overrides)
    return body


def reduce_message(dataset, **overrides) -> dict:
    """载荷缩减时前端发的参数：默认坐标映射下五个分量参与分组。"""
    body = {
        "intervals": dict(zip(SELECTED_COLUMNS, DEFAULT_BINS)),
        "axisMapping": factories.ROMAX_ORIGIN,
        "keepTorque": False,
        "slope": 4,
        "temperature": 40,
        "tol": 1e-6,
        "outputDir": str(dataset.out_dir),
    }
    body.update(overrides)
    return body


def run_ws(api_client, path: str, payload: dict) -> list[dict]:
    """连上 WebSocket 发一条参数，收到 done 或 error 为止，返回收到的全部消息。"""
    messages = []
    with api_client.websocket_connect(path) as ws:
        ws.send_json(payload)
        while True:
            message = ws.receive_json()
            messages.append(message)
            if message["type"] in ("done", "error"):
                return messages


def last(messages: list[dict]) -> dict:
    return messages[-1]


@pytest.fixture
def loaded_via_ws(api_client, dataset):
    """先走一遍加载，缓存里有数据。"""
    assert last(run_ws(api_client, LOAD_PATH, load_message(dataset)))["type"] == "done"
    return dataset


# ─── POST /api/simple-load/preview ───────────────────────────

class TestPreview:
    def test_返回_txt_个数大小和第一个文件的开头(self, api_client, dataset):
        response = api_client.post("/api/simple-load/preview", json={"loadDir": str(dataset.load_dir)})

        body = response.json()
        assert response.status_code == 200
        assert body["fileCount"] == 2
        assert body["totalSize"] == sum(p.stat().st_size for p in dataset.load_dir.glob("*.txt"))
        assert body["sampleFile"] == "c1.txt"
        assert body["lines"] == dataset.txt_path("c1").read_text(encoding="utf-8").splitlines()

    def test_子文件夹里的_txt_一起数(self, api_client, dataset):
        nested = dataset.load_dir / "DLC12" / "a.txt"
        nested.parent.mkdir()
        nested.write_text("1 2 3\n", encoding="utf-8")

        body = api_client.post(
            "/api/simple-load/preview", json={"loadDir": str(dataset.load_dir)}
        ).json()

        assert body["fileCount"] == 3
        assert body["sampleFile"].replace("\\", "/") == "DLC12/a.txt"

    def test_最多读二十行_空行不算(self, api_client, tmp_path):
        lines = ["Time Fx", "", *[f"{i} {i}" for i in range(30)]]
        (tmp_path / "a.txt").write_text("\n".join(lines), encoding="utf-8")

        body = api_client.post("/api/simple-load/preview", json={"loadDir": str(tmp_path)}).json()

        assert body["lines"] == ["Time Fx", *[f"{i} {i}" for i in range(19)]]

    def test_文件夹不存在(self, api_client, tmp_path):
        response = api_client.post(
            "/api/simple-load/preview", json={"loadDir": str(tmp_path / "没有")}
        )

        assert response.status_code == 400
        assert response.json()["detail"].startswith("载荷文件夹不存在")

    def test_文件夹里没有_txt(self, api_client, tmp_path):
        response = api_client.post("/api/simple-load/preview", json={"loadDir": str(tmp_path)})

        assert response.status_code == 400
        assert response.json()["detail"].startswith("载荷文件夹里没有 txt 文件")


# ─── POST /api/simple-load/clear ─────────────────────────────

class TestClear:
    def test_丢掉加载过的数据(self, api_client, loaded_via_ws):
        response = api_client.post("/api/simple-load/clear")

        assert response.status_code == 204
        assert LoadedDataCache.load() is None


# ─── WS /ws/simple-load/load ─────────────────────────────────

class TestLoad:
    def test_推进度并带回六个分量的最值和分布(self, api_client, dataset):
        messages = run_ws(api_client, LOAD_PATH, load_message(dataset))

        done = last(messages)
        progresses = [m["percent"] for m in messages if m["type"] == "progress"]
        assert done["type"] == "done"
        assert (done["fileCount"], done["rowCount"]) == (2, 8)
        assert progresses == sorted(progresses) and progresses[-1] == 100
        assert [c["component"] for c in done["components"]] == [
            "Fx[KN]", "Fy[KN]", "Fz[KN]", "Mx[KNm]", "My[KNm]", "Mz[KNm]",
        ]
        for component in done["components"]:
            assert component["min"] <= component["max"]
            assert len(component["binLeft"]) == len(component["binRight"]) == len(component["share"])
            assert sum(component["share"]) == pytest.approx(1.0)
        assert LoadedDataCache.load() is not None

    def test_跳过行数和单位换算生效(self, api_client, tmp_path):
        dataset = build_dataset(tmp_path, [ramp_case("c1", n_rows=4)])
        txt = dataset.txt_path("c1")
        lines = txt.read_text(encoding="utf-8").splitlines()
        txt.write_text("\n".join([lines[0], "END_OF_HEADER", *lines[1:]]), encoding="utf-8")

        done = last(run_ws(api_client, LOAD_PATH, load_message(dataset, skipRows=2, unitForce=2)))

        fx = next(c for c in done["components"] if c["component"] == "Fx[KN]")
        # ramp_case 的 Fx 是第 4 个分量：4000 + 100·i，力除以 2
        assert (done["rowCount"], fx["min"], fx["max"]) == (4, 2000, 2150)

    def test_列对应不全时推_error(self, api_client, dataset):
        columns = [c for c in dataset.header if c != "Fz[KN]"]

        done = last(run_ws(api_client, LOAD_PATH, load_message(dataset, columns=columns)))

        assert done == {"type": "error", "message": "列对应缺少 Fz[KN]"}

    def test_字段不合法时带上字段名(self, api_client, dataset):
        done = last(run_ws(api_client, LOAD_PATH, load_message(dataset, skipRows=-1)))

        assert done["type"] == "error"
        assert done["message"].startswith("skipRows：")

    def test_频次表不存在(self, api_client, dataset):
        payload = load_message(dataset, freqTablePath=str(dataset.root / "没有.xlsx"))

        done = last(run_ws(api_client, LOAD_PATH, payload))

        assert done["type"] == "error"
        assert done["message"].startswith("频次表不存在")

    def test_频次表和_txt_对不上时推_error_旧数据也清掉(self, api_client, loaded_via_ws, tmp_path):
        other = build_dataset(
            tmp_path / "other", [ramp_case("c1"), ramp_case("c2")], freq_names=["c1", "c3"]
        )

        done = last(run_ws(api_client, LOAD_PATH, load_message(other)))

        assert done["type"] == "error"
        assert "频次表与载荷文件不匹配" in done["message"]
        assert LoadedDataCache.load() is None


# ─── WS /ws/simple-load/reduce ───────────────────────────────

class TestReduce:
    def test_没加载过时提示先加载(self, api_client, dataset):
        done = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset)))

        assert done == {"type": "error", "message": "请先加载数据"}

    def test_写出两个_Excel_并带回格子数(self, api_client, loaded_via_ws):
        dataset = loaded_via_ws

        messages = run_ws(api_client, REDUCE_PATH, reduce_message(dataset))

        done = last(messages)
        assert done["type"] == "done"
        assert done["cellCount"] == len(read_gl(dataset.gl_excel()))
        assert [path.replace("\\", "/") for path in done["files"]] == [
            dataset.gl_excel().as_posix(),
            dataset.romax_excel().as_posix(),
        ]
        assert [m["percent"] for m in messages if m["type"] == "progress"][-1] == 100

    def test_缩减参数随请求生效(self, api_client, loaded_via_ws):
        dataset = loaded_via_ws

        run_ws(api_client, REDUCE_PATH, reduce_message(dataset, temperature=55))

        definition = read_romax(dataset.romax_excel())["工况表格定义"]
        assert (definition["温度(C)"] == 55).all()

    def test_改了区间直接再缩减(self, api_client, loaded_via_ws):
        dataset = loaded_via_ws
        coarse = dict.fromkeys(SELECTED_COLUMNS, [-10000, 10000])

        first = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset)))
        second = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset, intervals=coarse)))

        assert first["type"] == second["type"] == "done"
        assert second["cellCount"] < first["cellCount"]

    def test_保留扭矩时六个分量都要给区间(self, api_client, loaded_via_ws):
        dataset = loaded_via_ws

        done = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset, keepTorque=True)))

        assert done == {"type": "error", "message": "区间表缺少分量：My[KNm]"}

    def test_区间没有从小到大时推_error(self, api_client, loaded_via_ws):
        dataset = loaded_via_ws
        intervals = dict(zip(SELECTED_COLUMNS, DEFAULT_BINS)) | {"Fx[KN]": [100, 0, -100]}

        done = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset, intervals=intervals)))

        assert done == {"type": "error", "message": "Fx[KN]的区间值必须是单调递增的"}

    def test_输出目录不存在(self, api_client, loaded_via_ws):
        payload = reduce_message(loaded_via_ws, outputDir=str(loaded_via_ws.root / "没有"))

        done = last(run_ws(api_client, REDUCE_PATH, payload))

        assert done["type"] == "error"
        assert done["message"].startswith("输出目录不存在")

    def test_结果文件被占用时不缩减(self, api_client, loaded_via_ws, monkeypatch):
        dataset = loaded_via_ws
        monkeypatch.setattr(views_module, "is_locked", lambda path: "_GL-" in path)

        done = last(run_ws(api_client, REDUCE_PATH, reduce_message(dataset)))

        assert done == {
            "type": "error",
            "message": f"{dataset.gl_excel().name} 正被其他程序占用，请关闭后重试",
        }
        assert not dataset.gl_excel().exists()


# ─── 工具函数 ────────────────────────────────────────────────

def same_for_all(value) -> dict:
    """六个分量都用同一个值。"""
    return dict.fromkeys(factories.LOAD_COLUMNS, value)


class TestComponentStats:
    def test_区间写法拆成左右边界(self):
        min_max = {"min": same_for_all(-10.0), "max": same_for_all(10.0)}
        histograms = same_for_all(json.dumps({"(-10, 0]": 0.4, "(0, 10]": 0.6}))

        stats = views_module.component_stats(min_max, histograms)

        assert stats[0].model_dump(mode="json") == {
            "component": "Fx[KN]",
            "min": -10.0,
            "max": 10.0,
            "binLeft": [-10.0, 0.0],
            "binRight": [0.0, 10.0],
            "share": [0.4, 0.6],
        }

    def test_认不出的区间写法直接报错(self):
        min_max = {"min": same_for_all(0.0), "max": same_for_all(1.0)}
        histograms = same_for_all(json.dumps({"0 到 1": 1.0}))

        with pytest.raises(ValueError, match="分布区间无法识别"):
            views_module.component_stats(min_max, histograms)


class TestIsLocked:
    def test_文件不存在不算占用(self, tmp_path):
        assert views_module.is_locked(str(tmp_path / "a.xlsx")) is False

    def test_能打开来写不算占用(self, tmp_path):
        path = tmp_path / "a.xlsx"
        path.write_bytes(b"")

        assert views_module.is_locked(str(path)) is False
