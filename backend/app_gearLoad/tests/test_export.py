"""齿轮载荷的保存为 Excel —— 生产代码写出的 xlsx 和网页版原代码对跑，每一行还要和页面上算这一组工况的一样

参照按转速、扭矩排好多工况再交给网页版原代码，是网页版导出对的那种情况；网页版新录入的工况会把扭矩、转速对调，
见 serializers.py 的 `ExportRequest.condition_frame`。超过 4 级的期望值是逐级拼出来的，见 tests/expected.py。
改写法时只改 conftest.py 的 `export_tables`、`calculate`。
"""

import random

import pytest

from app_gearLoad.tests.compare import assert_same_tables, assert_same_value
from app_gearLoad.tests.expected import expected_tables
from app_gearLoad.tests.factories import (
    CONDITIONS,
    TYPICAL,
    random_condition,
    random_gearbox,
    random_long_gearbox,
)

#: 随机齿轮箱的个数，每台随机 1～30 组工况；5、6 级的另外随机 RANDOM_LONG_CASES 个
RANDOM_CASES = 20
RANDOM_LONG_CASES = 10


class TestSameAsWeb:
    @pytest.mark.parametrize("name", list(TYPICAL))
    def test_常见布置(self, export_tables, name):
        gearbox = TYPICAL[name]

        assert_same_tables(export_tables(gearbox, CONDITIONS), expected_tables(gearbox, CONDITIONS))

    @pytest.mark.parametrize("seed", range(RANDOM_CASES))
    def test_随机齿轮箱(self, export_tables, seed):
        rng = random.Random(seed)
        gearbox = random_gearbox(rng)
        conditions = [random_condition(rng) for _ in range(rng.randint(1, 30))]

        assert_same_tables(export_tables(gearbox, conditions), expected_tables(gearbox, conditions))

    @pytest.mark.parametrize("seed", range(RANDOM_LONG_CASES))
    def test_随机_5_6_级(self, export_tables, seed):
        rng = random.Random(seed)
        gearbox = random_long_gearbox(rng)
        conditions = [random_condition(rng) for _ in range(rng.randint(1, 10))]

        tables = export_tables(gearbox, conditions)

        assert list(tables)[4:] == ["stageV", "stageVI"][: len(gearbox.stages) - 4]
        assert_same_tables(tables, expected_tables(gearbox, conditions))


class TestSameAsPage:
    @pytest.mark.parametrize("name", list(TYPICAL))
    def test_每一行和页面上算这一组工况的一样(self, export_tables, calculate, name):
        gearbox = TYPICAL[name]

        tables = export_tables(gearbox, CONDITIONS)

        for row_index, (torque, speed) in enumerate(CONDITIONS):
            page = calculate(gearbox, torque, speed)
            assert list(tables) == list(page)
            for stage, table in tables.items():
                # 导出的 12 列是页面上 Gear loads 的 9 项加 Speed of components 的 3 项
                cells = page[stage]["gear_loads"] + page[stage]["speed_of_components"]
                for column, (cell, want) in enumerate(zip(table["data"][row_index][1:], cells), start=1):
                    assert_same_value(cell, want, f"{stage}[{row_index}][{column}]")
