"""齿轮载荷的计算 —— 生产代码和网页版原代码（tests/reference.py）对跑，再加几条不依赖参照的物理关系

网页版写死了 4 级，超过 4 级的期望值是用它逐级拼出来的，见 tests/expected.py。
优化算法、改写法的时候，这里的用例和断言都不动：生产代码的输入输出变了，只改 conftest.py 的 `calculate`。
数对不上就是改出了问题；有意改算法（比如不再四舍五入了再传给下一级），先和使用者对过，再改对应的用例。
"""

import math
import random
from dataclasses import replace

import pytest

from app_gearLoad.tests.compare import assert_same_results, normalize
from app_gearLoad.tests.expected import chained_results, expected_results
from app_gearLoad.tests.factories import (
    CONDITIONS,
    TYPICAL,
    WEB_STAGES,
    Gearbox,
    helical,
    input_rows,
    planetary,
    random_condition,
    random_gearbox,
    random_long_gearbox,
)
from app_gearLoad.tests.reference import reference_results

#: 随机齿轮箱的个数，种子是 0～RANDOM_CASES-1；5、6 级的另外随机 RANDOM_LONG_CASES 个
RANDOM_CASES = 100
RANDOM_LONG_CASES = 30

# 结果里各格的位置，同网页版的结果表
POWER, OUTPUT_TORQUE, OUTPUT_SPEED = 0, 1, 2  # input_data
PLANET_FORCE, MESH_TANGENTIAL, MESH_RADIAL, MESH_AXIAL = 0, 1, 2, 3  # gear_loads
RING_TANGENTIAL, RING_RADIAL, RING_AXIAL, SUN_AXIAL = 4, 5, 6, 8
PLANETARY_ONLY_LOADS = (PLANET_FORCE, RING_TANGENTIAL, RING_RADIAL, RING_AXIAL, SUN_AXIAL)


class TestSameAsWeb:
    @pytest.mark.parametrize("torque, speed", CONDITIONS)
    @pytest.mark.parametrize("name", list(TYPICAL))
    def test_常见布置(self, calculate, name, torque, speed):
        gearbox = TYPICAL[name]

        assert_same_results(calculate(gearbox, torque, speed), expected_results(gearbox, torque, speed))

    @pytest.mark.parametrize("seed", range(RANDOM_CASES))
    def test_随机齿轮箱(self, calculate, seed):
        rng = random.Random(seed)
        gearbox = random_gearbox(rng)
        torque, speed = random_condition(rng)

        assert_same_results(calculate(gearbox, torque, speed), expected_results(gearbox, torque, speed))

    @pytest.mark.parametrize("seed", range(RANDOM_LONG_CASES))
    def test_随机_5_6_级(self, calculate, seed):
        rng = random.Random(seed)
        gearbox = random_long_gearbox(rng)
        torque, speed = random_condition(rng)

        assert_same_results(calculate(gearbox, torque, speed), expected_results(gearbox, torque, speed))


class TestChainedReference:
    """超过 4 级的期望值是逐级拼出来的；4 级以内拼出来的要和网页版原代码直接算的一模一样，拼法才可信。"""

    @pytest.mark.parametrize("name", [name for name, gearbox in TYPICAL.items() if len(gearbox.stages) <= WEB_STAGES])
    def test_常见布置(self, name):
        gearbox = TYPICAL[name]
        torque, speed = CONDITIONS[0]

        direct = reference_results(input_rows(gearbox, torque, speed))
        assert_same_results(chained_results(gearbox, torque, speed), direct)

    @pytest.mark.parametrize("seed", range(20))
    def test_随机齿轮箱(self, seed):
        rng = random.Random(seed)
        gearbox = random_gearbox(rng)
        torque, speed = random_condition(rng)

        direct = reference_results(input_rows(gearbox, torque, speed))
        assert_same_results(chained_results(gearbox, torque, speed), direct)


class TestPhysics:
    """不靠参照实现也该成立的关系：算法改坏了，这几条往往先坏。"""

    @pytest.mark.parametrize("name", list(TYPICAL))
    def test_每级输出功率等于输入功率(self, calculate, name):
        torque, speed = CONDITIONS[0]

        result = calculate(TYPICAL[name], torque, speed)

        # 理想传动：输出扭矩 × 输出转速 = 输入扭矩 × 输入转速，只差输出扭矩、转速各自四舍五入到 3 位小数
        for stage in result.values():
            output_torque, output_speed = stage["input_data"][OUTPUT_TORQUE], stage["input_data"][OUTPUT_SPEED]
            rounding = 0.0005 * (abs(output_torque) + abs(output_speed)) + 1e-6
            assert math.isclose(output_torque * output_speed, torque * speed, rel_tol=1e-9, abs_tol=rounding)
            torque, speed = output_torque, output_speed

    def test_功率原样传到每一级(self, calculate):
        gearbox = TYPICAL["四级"]

        result = calculate(gearbox, *CONDITIONS[0])

        assert [stage["input_data"][POWER] for stage in result.values()] == [gearbox.power] * 4

    def test_行星级的传动比和转速(self, calculate):
        # 齿圈固定、行星架输入、太阳轮输出：传动比 1 + zR / zsun
        stage = calculate(Gearbox((planetary(16, 27, 36),)), 1000.0, 12.0)["stageI"]

        ratio = 1 + 99 / 27
        assert stage["input_data"][OUTPUT_TORQUE] == round(1000.0 / ratio, 3)
        assert stage["input_data"][OUTPUT_SPEED] == round(12.0 * ratio, 3)
        # 太阳轮、行星轮（相对行星架）、齿圈
        assert stage["speed_of_components"] == [round(12.0 * ratio, 3), round(-12.0 * 99 / 36, 3), 0]

    def test_平行级的传动比和转速(self, calculate):
        stage = calculate(Gearbox((helical(12, 98, 23),)), 1000.0, 12.0)["stageI"]

        assert stage["input_data"][OUTPUT_TORQUE] == round(1000.0 * 23 / 98, 3)
        assert stage["input_data"][OUTPUT_SPEED] == round(12.0 * 98 / 23, 3)
        # 大齿轮、小齿轮；平行级没有齿圈
        speeds = [normalize(value) for value in stage["speed_of_components"]]
        assert speeds == [12.0, round(12.0 * 98 / 23, 3), None]

    def test_平行级没有行星级才有的几项(self, calculate):
        stage = calculate(Gearbox((helical(12, 98, 23),)), 1000.0, 12.0)["stageI"]

        assert [normalize(stage["gear_loads"][index]) for index in PLANETARY_ONLY_LOADS] == [None] * 5
        assert [normalize(value) for value in stage["equivalent_diameter"][1:]] == [None, None]

    def test_扭矩翻倍载荷翻倍_转速不变(self, calculate):
        gearbox = TYPICAL["一级行星两级平行"]

        single, double = calculate(gearbox, 1000.0, 12.0), calculate(gearbox, 2000.0, 12.0)

        for stage in single:
            for once, twice in zip(single[stage]["gear_loads"], double[stage]["gear_loads"]):
                if normalize(once) is None:
                    assert normalize(twice) is None
                else:
                    # 每个数都四舍五入到 3 位小数，上一级的输出也是四舍五入后传下来的，倍数只差一点
                    assert math.isclose(2 * once, twice, rel_tol=1e-4, abs_tol=5e-3)
            assert single[stage]["speed_of_components"] == double[stage]["speed_of_components"]

    def test_直齿没有轴向力(self, calculate):
        result = calculate(TYPICAL["直齿"], *CONDITIONS[0])

        for stage in result.values():
            loads = stage["gear_loads"]
            assert normalize(loads[MESH_AXIAL]) == 0
            if normalize(loads[RING_AXIAL]) is not None:
                assert normalize(loads[RING_AXIAL]) == 0


class TestChaining:
    def test_下一级取上一级输出四舍五入到_3_位小数的值(self, calculate):
        # 一级输出转速 12.0001 × (1 + 99/27) = 56.00047，四舍五入成 56.0 再传给二级；
        # 二级小齿轮转速按 56.0 算是 428.235，按 56.00047 算会是 428.239
        gearbox = Gearbox((planetary(16, 27, 36), helical(12, 130, 17)))

        result = calculate(gearbox, 1000.0, 12.0001)

        assert result["stageI"]["input_data"][OUTPUT_SPEED] == 56.0
        assert result["stageII"]["speed_of_components"][1] == 428.235

    def test_行星级之后取太阳轮转速_平行级之后取小齿轮转速(self, calculate):
        gearbox = Gearbox((planetary(16, 27, 36), helical(12, 98, 23), helical(8, 101, 26)))

        result = calculate(gearbox, 1000.0, 12.0)

        sun_speed = result["stageI"]["speed_of_components"][0]
        pinion_speed = result["stageII"]["speed_of_components"][1]
        assert result["stageII"]["speed_of_components"][0] == sun_speed  # 二级大齿轮跟太阳轮一起转
        assert result["stageIII"]["speed_of_components"][0] == pinion_speed


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
class TestDegenerate:
    """不合理的输入：网页版不拦，算出 Infinity 或者空着。以后加了输入校验，这几条跟着改。"""

    def test_行星轮数是_0(self, calculate):
        gearbox = Gearbox((replace(planetary(16, 27, 36), planets=0),))

        result = calculate(gearbox, 1000.0, 12.0)

        assert_same_results(result, expected_results(gearbox, 1000.0, 12.0))
        assert normalize(result["stageI"]["gear_loads"][PLANET_FORCE]) == math.inf

    def test_太阳轮齿数是_0_无穷大传到下一级(self, calculate):
        gearbox = Gearbox((replace(planetary(16, 27, 36), z_sun=0), helical(12, 98, 23)))

        result = calculate(gearbox, 1000.0, 12.0)

        assert_same_results(result, expected_results(gearbox, 1000.0, 12.0))
        assert normalize(result["stageII"]["speed_of_components"][1]) == math.inf

    def test_中心距太小_径向力轴向力算不出来(self, calculate):
        gearbox = Gearbox((helical(12, 98, 23, shift=-60),))

        result = calculate(gearbox, 1000.0, 12.0)

        assert_same_results(result, expected_results(gearbox, 1000.0, 12.0))
        loads = result["stageI"]["gear_loads"]
        assert normalize(loads[MESH_TANGENTIAL]) is not None
        assert [normalize(loads[MESH_RADIAL]), normalize(loads[MESH_AXIAL])] == [None, None]
