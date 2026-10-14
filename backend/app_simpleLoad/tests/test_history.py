"""app_simpleLoad/views.py 的 histories —— 查网页版存在 TMB 服务器上的配置，换成回填用的字段

假服务器（backend/conftest.py 的 tmb_server）的记录照生产库里的样子写：路径缺 keep_torque_component，
列对应带「占位符」，区间表的格子数字、数字字符串、空串都有，标题行行号是 2。
"""

from common.constants import LoadColumn

HISTORIES_PATH = "/shanghai_yanfa7/simple-load-calculation-histories/"
AUTH = {"Authorization": "Bearer access-1"}


def web_record(**overrides) -> dict:
    """网页版存的一条记录（tmb_web_v1 的 SimpleLoadCalculationHistorySerializer）。"""
    record = {
        "id": 7,
        "proj_name": "GW-V16",
        "file_path_json": {
            "result_folder_save_path": "D:/out/GW-V16",
            "load_file_folder_path": "D:/load/GW-V16",
            "freq_table_path": "D:/load/GW-V16.xlsx",
        },
        "draggable_elements_json": [
            {"name": "Time[s]"},
            {"name": "占位符1"},
            {"name": "speed[rpm]"},
            {"name": "Mx[KNm]"},
            {"name": "My[KNm]"},
            {"name": "Mz[KNm]"},
            {"name": "Fx[KN]"},
            {"name": "Fy[KN]"},
            {"name": "Fz[KN]"},
        ],
        "conversion_factors_json": {
            "tol": 0.0001,
            "title_row": 2,
            "unit_force": 1000,
            "unit_speed": 1,
            "temperature": 60,
            "unit_moment": 1000,
            "translate_factor": 4.05,
        },
        "romax_origin_json": [
            {"romax": "x", "origin": "y"},
            {"romax": "y", "origin": "-z"},
            {"romax": "z", "origin": "-x"},
        ],
        "table_data_json": [
            {
                "0": -940, "1": "-290", "2": "", "3": "-170", "4": "0", "5": "",
                "6": "", "7": "", "8": "", "9": "909", "10": 985,
                "index": 0, "component": "Fx[KN]",
            },
            {"0": 1.5, "10": 2.5, "component": "My[KNm]"},
        ],
        "created_by": 3,
    }
    record.update(overrides)
    return record


def fetch(api_client, query: str = "", headers: dict | None = None):
    return api_client.get(
        "/api/simple-load/histories", params={"query": query}, headers=AUTH if headers is None else headers
    )


class TestConvert:
    def test_换成回填用的字段(self, api_client, tmb_server):
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [web_record()]})

        [record] = fetch(api_client).json()

        assert record["projName"] == "GW-V16"
        assert record["loadDir"] == "D:/load/GW-V16"
        assert record["freqTablePath"] == "D:/load/GW-V16.xlsx"
        assert record["outputDir"] == "D:/out/GW-V16"
        # 标题行是第 2 行（从 0 数），连它跳过 3 行
        assert record["skipRows"] == 3
        assert record["columns"] == [
            "Time[s]", None, "speed[rpm]", "Mx[KNm]", "My[KNm]", "Mz[KNm]", "Fx[KN]", "Fy[KN]", "Fz[KN]",
        ]
        assert (record["unitForce"], record["unitMoment"], record["unitSpeed"]) == (1000, 1000, 1)
        assert record["axisMapping"] == web_record()["romax_origin_json"]
        assert record["keepTorque"] is False
        assert (record["slope"], record["temperature"], record["tol"]) == (4.05, 60, 0.0001)

    def test_区间表按分量名取_格子换成数字_空的是_null(self, api_client, tmb_server):
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [web_record()]})

        [record] = fetch(api_client).json()

        assert record["intervals"] == {
            LoadColumn.FX.value: [-940, -290, None, -170, 0, None, None, None, None, 909, 985],
            LoadColumn.MY.value: [1.5, None, None, None, None, None, None, None, None, None, 2.5],
        }

    def test_没有标题行时不跳过(self, api_client, tmb_server):
        factors = {**web_record()["conversion_factors_json"], "title_row": None}
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [web_record(conversion_factors_json=factors)]})

        [record] = fetch(api_client).json()

        assert record["skipRows"] == 0

    def test_缺的字段按网页版的默认值补_填了_0_的留着(self, api_client, tmb_server):
        bare = {
            "id": 1,
            "proj_name": None,
            "file_path_json": None,
            "draggable_elements_json": None,
            "conversion_factors_json": {"temperature": 0},
            "romax_origin_json": None,
            "table_data_json": None,
        }
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [bare]})

        [record] = fetch(api_client).json()

        assert record["projName"] == "" and record["loadDir"] == ""
        assert record["skipRows"] == 0
        assert record["columns"] == []
        assert (record["unitForce"], record["unitMoment"], record["unitSpeed"]) == (1000, 1000, 1)
        assert (record["slope"], record["temperature"], record["tol"]) == (4.05, 0, 0.0001)
        assert record["axisMapping"] == [
            {"romax": "x", "origin": "-y"},
            {"romax": "y", "origin": "-z"},
            {"romax": "z", "origin": "x"},
        ]
        assert record["intervals"] == {}

    def test_保留扭矩的开关跟着记录走(self, api_client, tmb_server):
        paths = {**web_record()["file_path_json"], "keep_torque_component": True}
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [web_record(file_path_json=paths)]})

        [record] = fetch(api_client).json()

        assert record["keepTorque"] is True

    def test_新存的排在前面(self, api_client, tmb_server):
        records = [web_record(id=3, proj_name="旧"), web_record(id=9, proj_name="新")]
        tmb_server.reply("GET", HISTORIES_PATH, {"results": records})

        names = [record["projName"] for record in fetch(api_client).json()]

        assert names == ["新", "旧"]


class TestForward:
    def test_带着令牌和项目名去查(self, api_client, tmb_server):
        tmb_server.reply("GET", HISTORIES_PATH, {"results": []})

        response = fetch(api_client, query="GW")

        assert response.json() == []
        sent = tmb_server.requests[0]
        assert sent.url.params["query"] == "GW"
        assert sent.headers["Authorization"] == "Bearer access-1"

    def test_没登录_401_不找服务器(self, api_client, tmb_server):
        response = fetch(api_client, headers={})

        assert response.status_code == 401
        assert tmb_server.requests == []

    def test_令牌过期_401(self, api_client, tmb_server):
        tmb_server.reply("GET", HISTORIES_PATH, {"detail": "令牌无效或已过期"}, status=401)

        response = fetch(api_client)

        assert response.status_code == 401
        assert response.json()["detail"] == "登录已过期，请重新登录"
