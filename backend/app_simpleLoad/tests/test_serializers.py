"""app_simpleLoad/serializers.py —— 请求报文模型

重点验证两件事：
1. 报文里不合理的组合（列对应缺列、重复，坐标映射重复用轴）在入口就拦下；
2. 交给计算层的是 module.config 里的 dataclass 和 simple_load2 认的区间表，不是 Pydantic 对象。
"""

import pytest
from pydantic import ValidationError

from app_simpleLoad.module.config import AxisMapping, ConversionConfig, PathConfig
from app_simpleLoad.serializers import LoadRequest, ReduceRequest
from app_simpleLoad.tests import factories


def load_body(**overrides) -> dict:
    body = {
        "loadDir": "load",
        "freqTablePath": "freq.xlsx",
        "columns": list(factories.DEFAULT_HEADER),
        "skipRows": 1,
        "unitForce": 1000,
        "unitMoment": 1000,
        "unitSpeed": 1,
    }
    body.update(overrides)
    return body


def reduce_body(**overrides) -> dict:
    body = {
        "intervals": {"Fx[KN]": [-100, 0, 100], "Fy[KN]": [-100, 100]},
        "axisMapping": factories.ROMAX_ORIGIN,
        "keepTorque": False,
        "slope": 4,
        "temperature": 40,
        "tol": 1e-6,
        "outputDir": "out",
    }
    body.update(overrides)
    return body


class TestLoadRequest:
    def test_列对应展开成按列顺序的列名(self):
        request = LoadRequest.model_validate(load_body())

        assert request.header == factories.DEFAULT_HEADER

    def test_不用的列起占位符的名字(self):
        columns = [None, *factories.DEFAULT_HEADER, None]

        request = LoadRequest.model_validate(load_body(columns=columns))

        assert request.header == ["占位符0", *factories.DEFAULT_HEADER, "占位符9"]

    def test_Time_可以没有(self):
        columns = [c for c in factories.DEFAULT_HEADER if c != "Time[s]"]

        assert LoadRequest.model_validate(load_body(columns=columns)).header == columns

    def test_缺必需的列(self):
        columns = [c for c in factories.DEFAULT_HEADER if c not in ("Fz[KN]", "speed[rpm]")]

        with pytest.raises(ValidationError, match="列对应缺少 speed\\[rpm\\]、Fz\\[KN\\]"):
            LoadRequest.model_validate(load_body(columns=columns))

    def test_同一个分量不能对两列(self):
        columns = [*factories.DEFAULT_HEADER, "Mx[KNm]"]

        with pytest.raises(ValidationError, match="Mx\\[KNm\\] 选了不止一列"):
            LoadRequest.model_validate(load_body(columns=columns))

    def test_不认识的列名(self):
        columns = [*factories.DEFAULT_HEADER, "扭矩"]

        with pytest.raises(ValidationError):
            LoadRequest.model_validate(load_body(columns=columns))

    @pytest.mark.parametrize(("skip_rows", "title_row"), [(0, None), (1, 0), (2, 1)])
    def test_跳过的最后一行当标题行(self, skip_rows, title_row):
        request = LoadRequest.model_validate(load_body(skipRows=skip_rows))

        assert request.conversion_config().title_row == title_row

    def test_换成计算层的_dataclass(self):
        request = LoadRequest.model_validate(load_body(unitForce=10, unitMoment=20, unitSpeed=3))

        paths = request.path_config()
        config = request.conversion_config()
        assert isinstance(paths, PathConfig) and isinstance(config, ConversionConfig)
        assert (paths.load_file_folder_path, paths.freq_table_path) == ("load", "freq.xlsx")
        assert (config.unit_force, config.unit_moment, config.unit_speed) == (10, 20, 3)

    @pytest.mark.parametrize("field", ["unitForce", "unitMoment", "unitSpeed"])
    def test_换算系数必须大于_0(self, field):
        with pytest.raises(ValidationError, match=field):
            LoadRequest.model_validate(load_body(**{field: 0}))

    def test_路径不能为空(self):
        with pytest.raises(ValidationError, match="loadDir"):
            LoadRequest.model_validate(load_body(loadDir=""))


class TestReduceRequest:
    def test_区间表每行带分量名(self):
        request = ReduceRequest.model_validate(reduce_body())

        assert request.table_data() == [
            {"component": "Fx[KN]", "0": -100, "1": 0, "2": 100},
            {"component": "Fy[KN]", "0": -100, "1": 100},
        ]

    def test_坐标映射换成_AxisMapping(self):
        request = ReduceRequest.model_validate(reduce_body())

        assert request.axis_mappings() == factories.axis_mappings()
        assert all(isinstance(item, AxisMapping) for item in request.axis_mappings())

    def test_Romax_的轴要依次给出(self):
        mapping = list(reversed(factories.ROMAX_ORIGIN))

        with pytest.raises(ValidationError, match="依次给出 Romax 的 x、y、z"):
            ReduceRequest.model_validate(reduce_body(axisMapping=mapping))

    def test_载荷文件的轴不能重复用(self):
        mapping = [
            {"romax": "x", "origin": "x"},
            {"romax": "y", "origin": "-x"},
            {"romax": "z", "origin": "y"},
        ]

        with pytest.raises(ValidationError, match="各用一次"):
            ReduceRequest.model_validate(reduce_body(axisMapping=mapping))

    def test_区间表不能为空(self):
        with pytest.raises(ValidationError, match="intervals"):
            ReduceRequest.model_validate(reduce_body(intervals={}))

    def test_S_N_斜率必须大于_0(self):
        with pytest.raises(ValidationError, match="slope"):
            ReduceRequest.model_validate(reduce_body(slope=0))
