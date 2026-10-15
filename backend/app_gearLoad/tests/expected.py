"""期望值：网页版原代码（tests/reference.py）算出来的结果

网页版写死了 4 级。4 级以内直接用网页版原代码算；超过 4 级的，每一级单独用它算，再把上一级四舍五入后的输出扭矩、
转速接到下一级（网页版算第二级以后就是这么接的），拼成一份。4 级以内两种算法一模一样，test_calculation.py 里验证了。
逐级拼只用在正常的齿轮箱上：上一级算出空串、Infinity 时，网页版原代码单独算下一级会整级不算，和连着算不一样。
"""

from dataclasses import replace

from app_gearLoad.tests.factories import STAGE_KEYS, WEB_STAGES, Gearbox, input_rows, selected_rows
from app_gearLoad.tests.reference import reference_results, reference_tables


def expected_results(gearbox: Gearbox, torque: float, speed: float) -> dict:
    """算一个工况，结果同网页版接口：级名 → input_data、gear_loads、speed_of_components、equivalent_diameter。"""
    if len(gearbox.stages) <= WEB_STAGES:
        return reference_results(input_rows(gearbox, torque, speed))
    return chained_results(gearbox, torque, speed)


def chained_results(gearbox: Gearbox, torque: float, speed: float) -> dict:
    """每一级单独用网页版原代码算，上一级四舍五入后的输出扭矩、转速当下一级的输入。"""
    results = {}
    for key, stage in zip(STAGE_KEYS, gearbox.stages):
        result = reference_results(input_rows(replace(gearbox, stages=(stage,)), torque, speed))["stageI"]
        results[key] = result
        torque, speed = result["input_data"][1], result["input_data"][2]
    return results


def expected_tables(gearbox: Gearbox, conditions) -> dict:
    """导出多工况，结果同网页版：级名 → {"headers": 表头, "data": 数据行}。页面上 Stage I 的扭矩、转速是第一组工况。"""
    if len(gearbox.stages) <= WEB_STAGES:
        return reference_tables(input_rows(gearbox, *conditions[0]), selected_rows(conditions))
    return chained_tables(gearbox, conditions)


def chained_tables(gearbox: Gearbox, conditions) -> dict:
    """每一组工况逐级拼着算，排成网页版导出的表：每行是序号、9 项齿轮载荷、3 项转速。"""
    first = replace(gearbox, stages=gearbox.stages[:1])
    headers = reference_tables(input_rows(first, *conditions[0]), selected_rows(conditions[:1]))["stageI"]["headers"]
    tables = {key: {"headers": headers, "data": []} for key in STAGE_KEYS[: len(gearbox.stages)]}
    for index, (torque, speed) in enumerate(conditions):
        for key, result in chained_results(gearbox, torque, speed).items():
            tables[key]["data"].append([str(index), *result["gear_loads"], *result["speed_of_components"]])
    return tables
