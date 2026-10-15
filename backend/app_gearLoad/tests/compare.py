"""比较两份齿轮载荷结果：生产代码的和参照实现（网页版原代码）的

网页版的写法里，这一级没有、算不出来的格子是空串，除以 0 是 "Infinity"；写进 Excel 再读回来，空串成了 None。
以后重构也可能换成 None、inf。这里先统一成 None、±inf 和数再比：写法变了不算错，数变了才算。
"""

import math
from typing import Any

#: 现在要求和网页版一模一样。以后改了运算顺序（比如 numpy 换成 math），个别数会在第 3 位小数上差 1，下一级跟着差一点；
#: 确认是这种情况，再把它放宽，比如 1e-6
REL_TOL = 0.0

#: 计算结果每级的四张表，顺序同网页版
RESULT_TABLES = ("input_data", "gear_loads", "speed_of_components", "equivalent_diameter")


def normalize(value: Any) -> float | None:
    """空串、None、NaN 都是算不出来的格子，换成 None；"Infinity" 换成 inf，其余换成数。"""
    if value is None or value == "":
        return None
    number = float(value)
    return None if math.isnan(number) else number


def assert_same_value(actual: Any, expected: Any, where: str) -> None:
    got, want = normalize(actual), normalize(expected)
    if got is None or want is None or math.isinf(want):
        assert got == want, f"{where}：算出 {actual!r}，网页版是 {expected!r}"
    else:
        assert math.isclose(got, want, rel_tol=REL_TOL), f"{where}：算出 {actual!r}，网页版是 {expected!r}"


def assert_same_results(actual: dict, expected: dict) -> None:
    """两份计算结果：算到的级一样，每级四张表逐格一样。"""
    assert list(actual) == list(expected), f"算到的级不一样：{list(actual)} ≠ {list(expected)}"
    for stage, want in expected.items():
        for table in RESULT_TABLES:
            got_cells, want_cells = actual[stage][table], want[table]
            assert len(got_cells) == len(want_cells), f"{stage}.{table} 的格数不一样"
            for index, (got, cell) in enumerate(zip(got_cells, want_cells)):
                assert_same_value(got, cell, f"{stage}.{table}[{index}]")


def assert_same_tables(actual: dict, expected: dict) -> None:
    """两份导出的表：表名、表头一样，每行的工况序号和 12 个数一样。"""
    assert list(actual) == list(expected), f"表不一样：{list(actual)} ≠ {list(expected)}"
    for sheet, want in expected.items():
        got = actual[sheet]
        assert [normalize_header(cell) for cell in got["headers"]] == [
            normalize_header(cell) for cell in want["headers"]
        ], f"{sheet} 的表头不一样"
        assert len(got["data"]) == len(want["data"]), f"{sheet} 的行数不一样"
        for row_index, (got_row, want_row) in enumerate(zip(got["data"], want["data"])):
            assert str(got_row[0]) == str(want_row[0]), f"{sheet} 第 {row_index} 行的序号不一样"
            assert len(got_row) == len(want_row), f"{sheet} 第 {row_index} 行的格数不一样"
            for column, (cell, want_cell) in enumerate(zip(got_row[1:], want_row[1:]), start=1):
                assert_same_value(cell, want_cell, f"{sheet}[{row_index}][{column}]")


def normalize_header(cell: Any) -> str:
    """表头第一格是空的：网页版写空串，读回来是 None。"""
    return "" if cell is None else str(cell)
