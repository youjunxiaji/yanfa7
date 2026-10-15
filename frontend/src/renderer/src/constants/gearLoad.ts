// 齿轮载荷：页面照搬网页版（tmb_web_v1 的 gearLoadsView.vue）。输入表的英文参数名、结果表的行原样保留：
// 后端 backend/app_gearLoad/module/cal_gearLoads.py 按参数名取值、按这里的行序给结果，历史记录也存这些参数名

// 4 级的列；有几列 16 行都填了，后端就算 Stage I 起的前几级
export const GEAR_STAGES = ['stageI', 'stageII', 'stageIII', 'stageIIII'] as const

export type GearStage = (typeof GEAR_STAGES)[number]

export const STAGE_TITLES: Record<GearStage, string> = {
    stageI: 'Stage I',
    stageII: 'Stage II',
    stageIII: 'Stage III',
    stageIIII: 'Stage IIII'
}

// 上一级算完，把它的功率、输出扭矩、输出转速填到下一级
export const NEXT_STAGE: Partial<Record<GearStage, GearStage>> = {
    stageI: 'stageII',
    stageII: 'stageIII',
    stageIII: 'stageIIII'
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

// 后端结果 input_data 的顺序：二级以后这三行只读，由上一级的结果填
export const CHAINED_PARAMS: InputParam[] = [InputParam.POWER, InputParam.TORQUE, InputParam.SPEED]

export enum GearArrangement {
    PLANETARY = 'Planetary',
    HELICAL = 'Helical'
}

export enum HelixHand {
    LEFT = 'L',
    RIGHT = 'R'
}

// 齿轮载荷的 9 行，顺序同后端的 gear_loads；符号、单位两列照网页版原样
export const GEAR_LOAD_ROWS = [
    { parameter: 'Tangential force 2Ftan (kN)', symbol: '', unit: '' },
    { parameter: 'Tangential force (kN)', symbol: 'Ft,pl-sun', unit: '/ Ftan' },
    { parameter: 'Radial force (kN)', symbol: 'Fr,pl-sun', unit: '/ Frad' },
    { parameter: 'Axial force (kN)', symbol: 'Fa,pl-sun', unit: '/ Fax' },
    { parameter: 'Tangential force ring (kN)', symbol: 'Ft,pl-ring', unit: '' },
    { parameter: 'Radial force (kN)', symbol: 'Fr,pl-ring', unit: '' },
    { parameter: 'Axial force (kN)', symbol: 'Fa,pl-ring', unit: '' },
    { parameter: 'Torque T (kNm)', symbol: '', unit: '' },
    { parameter: 'Axial force sunwheel (kN)', symbol: '', unit: '' }
]

// 部件转速、等效直径各 3 行，顺序同后端的 speed_of_components、equivalent_diameter。
// 第二列有两种写法：Stage I 是行星级取前一个，是平行级取后一个（同网页版，不看各级自己的布置）
export const SPEED_ROWS = [
    { parameter: 'Speed (RPM)', symbol: ['LS-Sun', 'LS-S'] },
    { parameter: 'Speed (RPM)', symbol: ['LS-P', 'LIS-S'] },
    { parameter: 'Speed (RPM)', symbol: ['LS-R', ''] }
]

export const DIAMETER_ROWS = [
    {
        parameter: 'Operating pitch planet radius or pinion diameter (mm)',
        symbol: ['Plan/Sun', 'Pinion']
    },
    {
        parameter: 'Operating pitch planet radius or pinion diameter (mm)',
        symbol: ['Plan/Ring', '']
    },
    { parameter: 'Average of root & tip diameter (mm)', symbol: ['', ''] }
]
