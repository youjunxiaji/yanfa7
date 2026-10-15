"""app_simpleLoad/views.py 的 histories、save_history —— 查、存 TMB 服务器上的载荷简化配置

假服务器（backend/conftest.py 的 tmb_server）的记录照生产库里的样子写：路径缺 keep_torque_component，
列对应带「占位符」，区间表的格子数字、数字字符串、空串都有，标题行行号是 2。
存的报文照网页版「存储」发的写，存下的记录照网页版的 post 换：项目名取输出目录的最后一段。
"""

import json

import pytest

from common.constants import LoadColumn

HISTORIES_PATH = "/shanghai_yanfa7/simple-load-calculation-histories/"
AUTH = {"Authorization": "Bearer access-1"}

# 网页版存好时的响应，新建和覆盖一样
SAVED = {"status": "success", "message": "保存成功", "id": 12}


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


def config_body(**overrides) -> dict:
    """前端「保存配置」发的报文：区间表只带参与分组的分量（z 取 -x，Mx 不参与）。"""
    body = {
        "loadDir": "D:/load/GW-V16",
        "freqTablePath": "D:/load/GW-V16.xlsx",
        "outputDir": "D:/out/GW-V16",
        "skipRows": 3,
        "columns": [
            "Time[s]", None, "speed[rpm]", "Mx[KNm]", "My[KNm]", "Mz[KNm]", "Fx[KN]", "Fy[KN]", "Fz[KN]", None,
        ],
        "unitForce": 1000,
        "unitMoment": 1000,
        "unitSpeed": 1,
        "axisMapping": [
            {"romax": "x", "origin": "y"},
            {"romax": "y", "origin": "-z"},
            {"romax": "z", "origin": "-x"},
        ],
        "keepTorque": False,
        "slope": 4.05,
        "temperature": 60,
        "tol": 0.0001,
        "intervals": {
            "Fx[KN]": [-940, -290, None, -170, 0, None, None, None, None, 909, 985],
            "My[KNm]": [1.5, None, None, None, None, None, None, None, None, None, 2.5],
        },
    }
    body.update(overrides)
    return body


def save(api_client, headers: dict | None = None, **overrides):
    return api_client.post(
        "/api/simple-load/histories", json=config_body(**overrides), headers=AUTH if headers is None else headers
    )


def sent_body(tmb_server) -> dict:
    """转给假服务器的报文。"""
    return json.loads(tmb_server.requests[0].content)


def stored(sent: dict) -> dict:
    """网页版收到「存储」的报文后存下、再查出来的记录，项目名和它的 post 一样取输出目录的最后一段。"""
    return {
        "id": SAVED["id"],
        "proj_name": sent["file_path"]["result_folder_save_path"].replace("\\", "/").split("/")[-1],
        "file_path_json": sent["file_path"],
        "draggable_elements_json": sent["draggable_elements"],
        "conversion_factors_json": sent["conversion_factors"],
        "romax_origin_json": sent["romax_origin"],
        "table_data_json": sent["table_data"],
        "created_by": 3,
    }


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

    def test_新建的排在前面(self, api_client, tmb_server):
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


class TestSave:
    def test_换成网页版存储发的报文(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        response = save(api_client)

        assert response.status_code == 200
        assert response.json() == {"projName": "GW-V16"}
        assert tmb_server.requests[0].headers["Authorization"] == "Bearer access-1"
        assert sent_body(tmb_server) == {
            "file_path": {
                "result_folder_save_path": "D:/out/GW-V16",
                "load_file_folder_path": "D:/load/GW-V16",
                "freq_table_path": "D:/load/GW-V16.xlsx",
                "keep_torque_component": False,
            },
            # 不用的列和网页版添加的占位符一样，从 1 起编号
            "draggable_elements": [
                {"name": "Time[s]"},
                {"name": "占位符1"},
                {"name": "speed[rpm]"},
                {"name": "Mx[KNm]"},
                {"name": "My[KNm]"},
                {"name": "Mz[KNm]"},
                {"name": "Fx[KN]"},
                {"name": "Fy[KN]"},
                {"name": "Fz[KN]"},
                {"name": "占位符2"},
            ],
            # 跳过 3 行，标题行是第 2 行（从 0 数）
            "conversion_factors": {
                "unit_moment": 1000,
                "unit_force": 1000,
                "unit_speed": 1,
                "title_row": 2,
                "temperature": 60,
                "translate_factor": 4.05,
                "tol": 0.0001,
            },
            "romax_origin": config_body()["axisMapping"],
            # 空格子写空串
            "table_data": [
                {
                    "component": "Fx[KN]",
                    "0": -940, "1": -290, "2": "", "3": -170, "4": 0, "5": "",
                    "6": "", "7": "", "8": "", "9": 909, "10": 985,
                },
                {
                    "component": "My[KNm]",
                    "0": 1.5, "1": "", "2": "", "3": "", "4": "", "5": "",
                    "6": "", "7": "", "8": "", "9": "", "10": 2.5,
                },
            ],
        }

    def test_存下的记录查回来和存的一样(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)
        save(api_client)
        tmb_server.reply("GET", HISTORIES_PATH, {"results": [stored(sent_body(tmb_server))]})

        [record] = fetch(api_client).json()

        assert record == {"projName": "GW-V16", **config_body()}

    def test_一行都不跳时没有标题行(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        save(api_client, skipRows=0)

        assert sent_body(tmb_server)["conversion_factors"]["title_row"] is None

    def test_区间表按网页版的分量顺序排_补齐_11_格(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        save(api_client, intervals={"Mz[KNm]": [1, 2], "Fy[KN]": [None] * 11})

        rows = sent_body(tmb_server)["table_data"]
        assert [row["component"] for row in rows] == ["Fy[KN]", "Mz[KNm]"]
        assert rows[1] == {"component": "Mz[KNm]", "0": 1, "1": 2, **{str(i): "" for i in range(2, 11)}}

    def test_保留扭矩的开关跟着存(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        save(api_client, keepTorque=True)

        assert sent_body(tmb_server)["file_path"]["keep_torque_component"] is True

    def test_输出目录末尾的斜杠去掉_项目名取最后一级(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        response = save(api_client, outputDir=" D:\\out\\GW-V16\\ ")

        assert response.json() == {"projName": "GW-V16"}
        assert sent_body(tmb_server)["file_path"]["result_folder_save_path"] == "D:\\out\\GW-V16"

    @pytest.mark.parametrize("output_dir", ["", "  ", "\\", "/"])
    def test_没选输出目录_400_不找服务器(self, api_client, tmb_server, output_dir):
        response = save(api_client, outputDir=output_dir)

        assert response.status_code == 400
        assert "输出目录" in response.json()["detail"]
        assert tmb_server.requests == []

    def test_没登录_401_不找服务器(self, api_client, tmb_server):
        response = save(api_client, headers={})

        assert response.status_code == 401
        assert tmb_server.requests == []

    def test_令牌过期_401(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, {"detail": "令牌无效或已过期"}, status=401)

        response = save(api_client)

        assert response.status_code == 401
        assert response.json()["detail"] == "登录已过期，请重新登录"

    def test_服务器存失败_给出它的原话(self, api_client, tmb_server):
        failed = {
            "status": "error",
            "message": "保存失败: get() returned more than one SimpleLoadCalculationHistoryModel -- it returned 2!",
        }
        tmb_server.reply("POST", HISTORIES_PATH, failed, status=400)

        response = save(api_client)

        assert response.status_code == 400
        assert response.json()["detail"] == failed["message"]

    def test_没有存的权限_给出服务器的原话(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, {"detail": "您没有执行该操作的权限。"}, status=403)

        response = save(api_client)

        assert response.status_code == 400
        assert response.json()["detail"] == "您没有执行该操作的权限。"
