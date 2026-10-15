"""齿轮载荷的保存为 Excel —— 生产代码写出的 xlsx 和网页版原代码对跑，每一行还要和页面上算这一组工况的一样

参照按转速、扭矩排好多工况再交给网页版原代码，是网页版导出对的那种情况；网页版新录入的工况会把扭矩、转速对调，
见 serializers.py 的 `ExportRequest.condition_frame`。改写法时只改 conftest.py 的 `export_tables`、`calculate`。
"""

import random

import pytest

from app_gearLoad.tests.compare import assert_same_tables, assert_same_value
from app_gearLoad.tests.factories import (
    CONDITIONS,
    TYPICAL,
    Gearbox,
    input_rows,
    random_condition,
    random_gearbox,
    selected_rows,
)
from app_gearLoad.tests.reference import reference_tables

#: 随机齿轮箱的个数，每台随机 1～30 组工况
RANDOM_CASES = 20


def expected(gearbox: Gearbox, conditions) -> dict:
    """网页版原代码导出的表，页面上 Stage I 的扭矩、转速是第一组工况。"""
    return reference_tables(input_rows(gearbox, *conditions[0]), selected_rows(conditions))


class TestSameAsWeb:
    @pytest.mark.parametrize("name", list(TYPICAL))
    def test_常见布置(self, export_tables, name):
        gearbox = TYPICAL[name]

        assert_same_tables(export_tables(gearbox, CONDITIONS), expected(gearbox, CONDITIONS))

    @pytest.mark.parametrize("seed", range(RANDOM_CASES))
    def test_随机齿轮箱(self, export_tables, seed):
        rng = random.Random(seed)
        gearbox = random_gearbox(rng)
        conditions = [random_condition(rng) for _ in range(rng.randint(1, 30))]

        assert_same_tables(export_tables(gearbox, conditions), expected(gearbox, conditions))


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
