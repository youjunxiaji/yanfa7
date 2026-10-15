"""app_gearLoad/views.py 的 histories、history、save_history —— 查、取、存 TMB 服务器上的齿轮计算历史

假服务器（backend/conftest.py 的 tmb_server）照网页版接口的样子回：列表只有 id 和「齿轮单元/风机/载荷谱」，
取一条按 id，存的时候回 created 说是新建还是覆盖。存的报文照网页版 Ctrl+S 发的写，原样转过去。
"""

import json

import pytest

HISTORIES_PATH = "/shanghai_yanfa7/gearCalculation/history/"
AUTH = {"Authorization": "Bearer access-1"}

INPUT_DATA = [
    {
        "parameter": "Gear stage arrangement",
        "stageI": "Planetary",
        "stageII": "Helical",
        "stageIII": "Planetary",
        "stageIIII": "Planetary",
        "editable": False,
    },
    {
        "parameter": "Centre distance a (mm)",
        "stageI": "381",
        "stageII": "610",
        "stageIII": "",
        "stageIIII": "",
        "editable": True,
    },
]
CONDITIONS = [{"torque": "1000", "rpm": "12"}, {"torque": "800", "rpm": "10.5"}]
FORM = {"gearUnit": "NGC-6X", "windTurbine": "GW-V16", "loadSpectrum": "LDD-2026"}

# 网页版存好时的响应：created 是 True 说明新建，False 说明覆盖了同样三项的那条
SAVED = {"status": "success", "message": "保存成功", "id": 12, "created": True}
OVERWRITTEN = {**SAVED, "id": 7, "created": False}


def web_record(**overrides) -> dict:
    """网页版存的一条记录（tmb_web_v1 的 GearCalculationHistorySerializer）。"""
    record = {
        "id": 7,
        "gear_unit": "NGC-6X",
        "wind_turbine": "GW-V16",
        "load_spectrum": "LDD-2026",
        "vars_json": INPUT_DATA,
        # 从库里取出来的记录，转速排在扭矩前面
        "selected_data_json": [{"rpm": "12", "torque": "1000"}],
        "created_by": 3,
    }
    record.update(overrides)
    return record


def save(api_client, headers: dict | None = None, **overrides):
    body = {"formData": FORM, "inputData": INPUT_DATA, "selectedData": CONDITIONS}
    body.update(overrides)
    return api_client.post(
        "/api/gear-load/histories", json=body, headers=AUTH if headers is None else headers
    )


class TestList:
    def test_带着令牌和关键字去查(self, api_client, tmb_server):
        results = [{"id": 9, "label": "NGC-6X/GW-V16/LDD-2026"}, {"id": 3, "label": "A/B/C"}]
        tmb_server.reply("GET", HISTORIES_PATH, {"results": results})

        response = api_client.get("/api/gear-load/histories", params={"query": "GW"}, headers=AUTH)

        assert response.json() == results
        sent = tmb_server.requests[0]
        assert sent.url.params["query"] == "GW"
        assert sent.headers["Authorization"] == "Bearer access-1"

    def test_没登录_401_不找服务器(self, api_client, tmb_server):
        response = api_client.get("/api/gear-load/histories")

        assert response.status_code == 401
        assert tmb_server.requests == []

    def test_令牌过期_401(self, api_client, tmb_server):
        tmb_server.reply("GET", HISTORIES_PATH, {"detail": "令牌无效或已过期"}, status=401)

        response = api_client.get("/api/gear-load/histories", headers=AUTH)

        assert response.status_code == 401
        assert response.json()["detail"] == "登录已过期，请重新登录"


class TestDetail:
    def test_换成回填用的字段(self, api_client, tmb_server):
        tmb_server.reply("GET", f"{HISTORIES_PATH}7/detail/", web_record())

        response = api_client.get("/api/gear-load/histories/7", headers=AUTH)

        assert response.json() == {
            "formData": FORM,
            "inputData": INPUT_DATA,
            "selectedData": [{"torque": "1000", "rpm": "12"}],
        }

    def test_数字换成字符串_null_换成空串_没有的级不补(self, api_client, tmb_server):
        row = {"parameter": "Centre distance a (mm)", "stageI": 381, "stageII": None, "editable": True}
        tmb_server.reply("GET", f"{HISTORIES_PATH}7/detail/", web_record(vars_json=[row]))

        [cell] = api_client.get("/api/gear-load/histories/7", headers=AUTH).json()["inputData"]

        assert cell == {"parameter": "Centre distance a (mm)", "editable": True, "stageI": "381", "stageII": ""}

    def test_第_5_级以后原样回填(self, api_client, tmb_server):
        row = {"parameter": "Centre distance a (mm)", "stageI": "381", "stageIIII": "300", "stageV": "250"}
        tmb_server.reply("GET", f"{HISTORIES_PATH}7/detail/", web_record(vars_json=[row]))

        [cell] = api_client.get("/api/gear-load/histories/7", headers=AUTH).json()["inputData"]

        assert (cell["stageIIII"], cell["stageV"]) == ("300", "250")

    def test_不是级的键丢掉(self, api_client, tmb_server):
        row = {"parameter": "Centre distance a (mm)", "stageI": "381", "note": "备注", "stage5": "1"}
        tmb_server.reply("GET", f"{HISTORIES_PATH}7/detail/", web_record(vars_json=[row]))

        [cell] = api_client.get("/api/gear-load/histories/7", headers=AUTH).json()["inputData"]

        assert cell == {"parameter": "Centre distance a (mm)", "editable": False, "stageI": "381"}

    def test_没存输入表和多工况的记录给_null(self, api_client, tmb_server):
        record = web_record(vars_json=None, selected_data_json=None, load_spectrum=None)
        tmb_server.reply("GET", f"{HISTORIES_PATH}7/detail/", record)

        detail = api_client.get("/api/gear-load/histories/7", headers=AUTH).json()

        assert detail["inputData"] is None and detail["selectedData"] is None
        assert detail["formData"]["loadSpectrum"] == ""

    def test_没登录_401_不找服务器(self, api_client, tmb_server):
        response = api_client.get("/api/gear-load/histories/7")

        assert response.status_code == 401
        assert tmb_server.requests == []


class TestSave:
    def test_报文原样转给网页版(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)

        response = save(api_client)

        assert response.status_code == 200
        assert response.json() == {"created": True}
        sent = tmb_server.requests[0]
        assert sent.headers["Authorization"] == "Bearer access-1"
        assert json.loads(sent.content) == {"formData": FORM, "inputData": INPUT_DATA, "selectedData": CONDITIONS}

    def test_第_5_级以后原样转给网页版(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, SAVED)
        rows = [{**row, "stageV": "250"} for row in INPUT_DATA]

        save(api_client, inputData=rows)

        sent = json.loads(tmb_server.requests[0].content)["inputData"]
        assert [row["stageV"] for row in sent] == ["250", "250"]

    def test_存过同名的是覆盖(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, OVERWRITTEN)

        response = save(api_client)

        assert response.json() == {"created": False}

    @pytest.mark.parametrize("field", ["gearUnit", "windTurbine", "loadSpectrum"])
    def test_基础设置没填全_400_不找服务器(self, api_client, tmb_server, field):
        response = save(api_client, formData={**FORM, field: ""})

        assert response.status_code == 400
        assert response.json()["detail"] == "请填写完整的基本信息"
        assert tmb_server.requests == []

    def test_没登录_401_不找服务器(self, api_client, tmb_server):
        response = save(api_client, headers={})

        assert response.status_code == 401
        assert tmb_server.requests == []

    def test_没有存的权限_给出服务器的原话(self, api_client, tmb_server):
        tmb_server.reply("POST", HISTORIES_PATH, {"detail": "您没有执行该操作的权限。"}, status=403)

        response = save(api_client)

        assert response.status_code == 400
        assert response.json()["detail"] == "您没有执行该操作的权限。"
