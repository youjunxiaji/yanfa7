"""齿轮箱用例：不依赖实现地描述一台齿轮箱，再换成网页版输入表的写法

几何参数照风电齿轮箱的量级编：行星级的齿圈齿数 = 太阳轮 + 2 × 行星轮；中心距取模数、齿数、螺旋角算出的标准中心距，
再加一点变位。随机用例按种子生成，每次跑的都是同一批。
"""

import math
import random
from dataclasses import dataclass

#: 网页版输入表的 16 行参数名，顺序同页面
PARAMS = (
    "Gear stage arrangement",
    "Nominal pressure angle αn (°)",
    "Helix angle β (°)",
    "Helix angle LH of RH - sun wheel or pinion",
    "Module in the normal section mn (mm)",
    "Number of teeth ring wheel zR / wheel z1",
    "Number of teeth planet zpl / pinion z2",
    "Number of teeth sun zsun",
    "Centre distance a (mm)",
    "Number of planets",
    "Power P (kW)",
    "Torque T (kNm)",
    "Input speed n (RPM)",
    "Root diameter df (mm)",
    "Tip diameter da (mm)",
    "Load factor KY",
)
STAGE_KEYS = ("stageI", "stageII", "stageIII", "stageIIII")

#: 没用到的级：网页版页面上布置默认 Planetary、旋向默认 L，其余空着
EMPTY_COLUMN = ("Planetary", "", "", "L") + ("",) * 12


@dataclass(frozen=True)
class Stage:
    """一级齿轮。平行级用不到太阳轮齿数、行星轮数和 KY，网页版也得填，这里填 0、0、1"""

    arrangement: str  # Planetary / Helical
    module: float  # 法向模数 mn (mm)
    z_ring: float  # 行星级是齿圈 zR，平行级是大齿轮 z1
    z_planet: float  # 行星级是行星轮 zpl，平行级是小齿轮 z2
    z_sun: float  # 太阳轮 zsun
    centre_distance: float  # a (mm)
    planets: float
    helix_angle: float  # β (°)
    pressure_angle: float  # αn (°)
    root_diameter: float  # df (mm)，和 da 都是 0 表示没填
    tip_diameter: float  # da (mm)
    load_factor: float  # KY
    hand: str  # 旋向 L / R，不参与计算


@dataclass(frozen=True)
class Gearbox:
    stages: tuple[Stage, ...]
    power: float = 6000.0  # 功率 (kW)，不参与计算，原样传给下一级


def standard_centre_distance(module: float, z1: float, z2: float, helix_angle: float) -> float:
    """两个外啮合齿轮的标准中心距。"""
    return module * (z1 + z2) / (2 * math.cos(math.radians(helix_angle)))


def planetary(
    module: float,
    z_sun: float,
    z_planet: float,
    *,
    planets: float = 3,
    helix_angle: float = 7.0,
    pressure_angle: float = 20.0,
    shift: float = 0.0,
    load_factor: float = 1.1,
    root_diameter: float = 0.0,
    tip_diameter: float = 0.0,
    hand: str = "L",
) -> Stage:
    """行星级：中心距按太阳轮和行星轮算，再加 shift。"""
    return Stage(
        arrangement="Planetary",
        module=module,
        z_ring=z_sun + 2 * z_planet,
        z_planet=z_planet,
        z_sun=z_sun,
        centre_distance=standard_centre_distance(module, z_sun, z_planet, helix_angle) + shift,
        planets=planets,
        helix_angle=helix_angle,
        pressure_angle=pressure_angle,
        root_diameter=root_diameter,
        tip_diameter=tip_diameter,
        load_factor=load_factor,
        hand=hand,
    )


def helical(
    module: float,
    z_wheel: float,
    z_pinion: float,
    *,
    helix_angle: float = 10.0,
    pressure_angle: float = 20.0,
    shift: float = 0.0,
    root_diameter: float = 0.0,
    tip_diameter: float = 0.0,
    hand: str = "R",
) -> Stage:
    """平行级：大齿轮带小齿轮，中心距按两个齿轮算，再加 shift。"""
    return Stage(
        arrangement="Helical",
        module=module,
        z_ring=z_wheel,
        z_planet=z_pinion,
        z_sun=0,
        centre_distance=standard_centre_distance(module, z_wheel, z_pinion, helix_angle) + shift,
        planets=0,
        helix_angle=helix_angle,
        pressure_angle=pressure_angle,
        root_diameter=root_diameter,
        tip_diameter=tip_diameter,
        load_factor=1,
        hand=hand,
    )


#: 常见的几种布置；行星轮、小齿轮的齿根圆、齿顶圆按分度圆 −2.5 mn、+2 mn 估
TYPICAL = {
    "一级行星两级平行": Gearbox((planetary(16, 27, 36), helical(12, 98, 23), helical(8, 101, 26, helix_angle=12))),
    "两级行星一级平行": Gearbox(
        (planetary(18, 24, 40, planets=4), planetary(12, 21, 33, load_factor=1.05), helical(10, 93, 25))
    ),
    "三级行星": Gearbox(
        (
            planetary(20, 30, 45, planets=5, load_factor=1.15),
            planetary(14, 24, 38, planets=4, helix_angle=6.5),
            planetary(9, 22, 31, helix_angle=8),
        )
    ),
    "四级": Gearbox(
        (
            planetary(22, 28, 44, planets=4),
            planetary(14, 23, 37),
            helical(10, 96, 24, pressure_angle=22.5),
            helical(7, 104, 27, helix_angle=12),
        )
    ),
    "平行级开头": Gearbox((helical(14, 110, 30), planetary(10, 25, 35, planets=4))),
    "行星级填了齿根圆齿顶圆": Gearbox(
        (planetary(16, 27, 36, root_diameter=540.33, tip_diameter=612.33),)
    ),
    "平行级填了齿根圆齿顶圆": Gearbox((helical(12, 98, 23, root_diameter=250.27, tip_diameter=304.27),)),
    "直齿": Gearbox((planetary(16, 27, 36, helix_angle=0), helical(12, 98, 23, helix_angle=0))),
    "变位": Gearbox((planetary(16, 27, 36, shift=3.5), helical(12, 98, 23, shift=-2.0))),
}

#: 输入扭矩 (kNm)、转速 (rpm)：额定、部分负载、反拖、停机
CONDITIONS = ((3215.5, 11.8), (1480.25, 9.35), (-420.75, 6.5), (0.0, 0.0))


def random_planetary(rng: random.Random) -> Stage:
    """随机一个行星级，几何参数在风电齿轮箱常见的范围里，一半填了齿根圆、齿顶圆。"""
    module = rng.choice((6, 8, 10, 12, 14, 16, 18, 20, 22, 25))
    z_sun, z_planet = rng.randint(17, 40), rng.randint(20, 60)
    helix_angle = rng.choice((0.0, 5.0, 6.5, 7.0, 7.5, 8.0, 10.0))
    pitch = module * z_planet / math.cos(math.radians(helix_angle))
    with_diameters = rng.random() < 0.5
    return planetary(
        module,
        z_sun,
        z_planet,
        planets=rng.randint(3, 7),
        helix_angle=helix_angle,
        pressure_angle=rng.choice((20.0, 22.5, 25.0)),
        shift=standard_centre_distance(module, z_sun, z_planet, helix_angle) * rng.uniform(-0.01, 0.02),
        load_factor=round(rng.uniform(1.0, 1.3), 2),
        root_diameter=round(pitch - 2.5 * module, 2) if with_diameters else 0.0,
        tip_diameter=round(pitch + 2 * module, 2) if with_diameters else 0.0,
        hand=rng.choice("LR"),
    )


def random_helical(rng: random.Random) -> Stage:
    """随机一个平行级，一半填了小齿轮的齿根圆、齿顶圆。"""
    module = rng.choice((5, 6, 7, 8, 10, 12, 14, 16, 18, 20))
    z_wheel, z_pinion = rng.randint(60, 130), rng.randint(17, 35)
    helix_angle = rng.choice((0.0, 8.0, 9.0, 10.0, 12.0, 14.0))
    pitch = module * z_pinion / math.cos(math.radians(helix_angle))
    with_diameters = rng.random() < 0.5
    return helical(
        module,
        z_wheel,
        z_pinion,
        helix_angle=helix_angle,
        pressure_angle=rng.choice((20.0, 22.5, 25.0)),
        shift=standard_centre_distance(module, z_wheel, z_pinion, helix_angle) * rng.uniform(-0.01, 0.02),
        root_diameter=round(pitch - 2.5 * module, 2) if with_diameters else 0.0,
        tip_diameter=round(pitch + 2 * module, 2) if with_diameters else 0.0,
        hand=rng.choice("LR"),
    )


def random_gearbox(rng: random.Random) -> Gearbox:
    """随机 1～4 级，多数是三级；第一级多半是行星级，后面行星、平行都有。"""
    count = rng.choice((1, 2, 3, 3, 3, 4))
    stages = [random_planetary(rng) if rng.random() < 0.8 else random_helical(rng)]
    stages += [random_planetary(rng) if rng.random() < 0.4 else random_helical(rng) for _ in range(count - 1)]
    return Gearbox(tuple(stages), power=round(rng.uniform(1000, 15000), 1))


def random_condition(rng: random.Random) -> tuple[float, float]:
    """随机一组输入扭矩 (kNm)、转速 (rpm)，扭矩有正有负。"""
    return round(rng.uniform(-1000, 9000), 3), round(rng.uniform(0, 20), 3)


def cell(value: float) -> str:
    """网页版输入框里是字符串；repr 读回来还是同一个数。"""
    return repr(float(value))


def stage_column(stage: Stage, power: float, torque: float, speed: float) -> tuple[str, ...]:
    """一级在输入表里的 16 格，顺序同 PARAMS。"""
    return (
        stage.arrangement,
        cell(stage.pressure_angle),
        cell(stage.helix_angle),
        stage.hand,
        cell(stage.module),
        cell(stage.z_ring),
        cell(stage.z_planet),
        cell(stage.z_sun),
        cell(stage.centre_distance),
        cell(stage.planets),
        cell(power),
        cell(torque),
        cell(speed),
        cell(stage.root_diameter),
        cell(stage.tip_diameter),
        cell(stage.load_factor),
    )


def input_rows(gearbox: Gearbox, torque: float, speed: float) -> list[dict]:
    """网页版页面算这个工况时发的输入表。

    二级以后的扭矩、转速算的时候由上一级的输出顶掉，这里先占个位，整列才算填满；
    功率照网页版前端填的，和 Stage I 一样。
    """
    columns = [
        stage_column(stage, gearbox.power, *((torque, speed) if index == 0 else (0, 0)))
        for index, stage in enumerate(gearbox.stages)
    ]
    columns += [EMPTY_COLUMN] * (len(STAGE_KEYS) - len(columns))
    return [
        {
            "parameter": name,
            **{key: column[index] for key, column in zip(STAGE_KEYS, columns)},
            "editable": index not in (0, 3),
        }
        for index, name in enumerate(PARAMS)
    ]


def selected_rows(conditions: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> list[dict]:
    """多工况，同网页版的 selectedData。"""
    return [{"torque": cell(torque), "rpm": cell(speed)} for torque, speed in conditions]
