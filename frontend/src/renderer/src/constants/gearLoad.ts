// 齿轮载荷。输入表沿用网页版（tmb_web_v1 的 gearLoadsView.vue）的写法：一行一个参数，参数名是网页版的英文原名，
// 各级的值放在 stageI、stageII…… 里。后端 backend/app_gearLoad 按参数名和这些键取值，历史记录存的也是它们，改了要两边一起改

// 网页版页面固定 4 级；这边不限级数，新页面照旧先给 4 级
export const WEB_STAGES = 4

// 各级在输入表里的键
export type GearStage = `stage${string}`

const ROMAN_NUMERALS: [number, string][] = [
    [1000, 'M'],
    [900, 'CM'],
    [500, 'D'],
    [400, 'CD'],
    [100, 'C'],
    [90, 'XC'],
    [50, 'L'],
    [40, 'XL'],
    [10, 'X'],
    [9, 'IX'],
    [5, 'V'],
    [4, 'IV'],
    [1, 'I']
]

// 正整数写成罗马数字，如 4 是 IV
export const roman = (value: number): string => {
    let rest = value
    return ROMAN_NUMERALS.map(([unit, letter]) => {
        const count = Math.floor(rest / unit)
        rest -= count * unit
        return letter.repeat(count)
    }).join('')
}

// 第 index 级（从 0 数）的键：前 4 级沿用网页版的 stageI～stageIIII（第 4 级网页版写成 IIII），往后接 stageV、stageVI……，
// 同后端 cal_gearLoads.py 的 stage_keys
export const stageKey = (index: number): GearStage =>
    index === 3 ? 'stageIIII' : `stage${roman(index + 1)}`

// 页面上显示的级名：I、II、III、IV、V……，第 4 级显示成 IV，键还是 stageIIII
export const stageName = (index: number): string => roman(index + 1)

export enum GearArrangement {
    PLANETARY = 'Planetary',
    HELICAL = 'Helical'
}

export enum HelixHand {
    LEFT = 'L',
    RIGHT = 'R'
}

// 输入表的 16 行，顺序同网页版；值就是网页版的参数名，一个字都不能改
export enum InputParam {
    ARRANGEMENT = 'Gear stage arrangement',
    PRESSURE_ANGLE = 'Nominal pressure angle αn (°)',
    HELIX_ANGLE = 'Helix angle β (°)',
    HELIX_HAND = 'Helix angle LH of RH - sun wheel or pinion',
    MODULE = 'Module in the normal section mn (mm)',
    TEETH_RING = 'Number of teeth ring wheel zR / wheel z1',
    TEETH_PLANET = 'Number of teeth planet zpl / pinion z2',
    TEETH_SUN = 'Number of teeth sun zsun',
    CENTRE_DISTANCE = 'Centre distance a (mm)',
    PLANETS = 'Number of planets',
    POWER = 'Power P (kW)',
    TORQUE = 'Torque T (kNm)',
    SPEED = 'Input speed n (RPM)',
    ROOT_DIAMETER = 'Root diameter df (mm)',
    TIP_DIAMETER = 'Tip diameter da (mm)',
    LOAD_FACTOR = 'Load factor KY'
}

// 后端结果 input_data 的顺序：功率、输出扭矩、输出转速。二级以后这三行由上一级的结果填，不让手改
export const CHAINED_PARAMS: InputParam[] = [InputParam.POWER, InputParam.TORQUE, InputParam.SPEED]

// 参数栏里逐级填的数值参数，顺序同网页版的输入表；布置、旋向用分段选择单独放
export const NUMBER_PARAMS: InputParam[] = [
    InputParam.PRESSURE_ANGLE,
    InputParam.HELIX_ANGLE,
    InputParam.MODULE,
    InputParam.TEETH_RING,
    InputParam.TEETH_PLANET,
    InputParam.TEETH_SUN,
    InputParam.CENTRE_DISTANCE,
    InputParam.PLANETS,
    InputParam.ROOT_DIAMETER,
    InputParam.TIP_DIAMETER,
    InputParam.LOAD_FACTOR
]

// Helical 级用不到的参数：网页版也要填，不填这一级不算
export const PLANETARY_ONLY_PARAMS: InputParam[] = [
    InputParam.TEETH_SUN,
    InputParam.PLANETS,
    InputParam.LOAD_FACTOR
]

// 结果表的一行：参数名同网页版；符号前一个是 Planetary 级的、后一个是 Helical 级的
export interface ResultLine {
    parameter: string
    symbol: string
}

// 后端 gear_loads 的 9 项，顺序不能变
export const GEAR_LOAD_LINES: ResultLine[] = [
    { parameter: 'Tangential force 2Ftan (kN)', symbol: '2Ftan' },
    { parameter: 'Tangential force (kN)', symbol: 'Ft,pl-sun / Ftan' },
    { parameter: 'Radial force (kN)', symbol: 'Fr,pl-sun / Frad' },
    { parameter: 'Axial force (kN)', symbol: 'Fa,pl-sun / Fax' },
    { parameter: 'Tangential force ring (kN)', symbol: 'Ft,pl-ring' },
    { parameter: 'Radial force (kN)', symbol: 'Fr,pl-ring' },
    { parameter: 'Axial force (kN)', symbol: 'Fa,pl-ring' },
    { parameter: 'Torque T (kNm)', symbol: 'T' },
    { parameter: 'Axial force sunwheel (kN)', symbol: '' }
]

// 后端 speed_of_components 的 3 项
export const SPEED_LINES: ResultLine[] = [
    { parameter: 'Speed (RPM)', symbol: 'LS-Sun / LS-S' },
    { parameter: 'Speed (RPM)', symbol: 'LS-P / LIS-S' },
    { parameter: 'Speed (RPM)', symbol: 'LS-R' }
]

// 后端 equivalent_diameter 的 3 项
export const DIAMETER_LINES: ResultLine[] = [
    {
        parameter: 'Operating pitch planet radius or pinion diameter (mm)',
        symbol: 'Plan/Sun / Pinion'
    },
    { parameter: 'Operating pitch planet radius or pinion diameter (mm)', symbol: 'Plan/Ring' },
    { parameter: 'Average of root & tip diameter (mm)', symbol: '' }
]
