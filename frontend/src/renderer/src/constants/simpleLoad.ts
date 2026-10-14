// 载荷简化里 txt 各列的含义，值就是后端计算用的列名，和 backend/common/constants.py 的 LoadColumn 一致
export enum LoadColumn {
    TIME = 'Time[s]',
    SPEED = 'speed[rpm]',
    FX = 'Fx[KN]',
    FY = 'Fy[KN]',
    FZ = 'Fz[KN]',
    MX = 'Mx[KNm]',
    MY = 'My[KNm]',
    MZ = 'Mz[KNm]'
}

// 六个力 / 力矩分量，顺序即区间表和分布图的顺序
export const LOAD_COMPONENTS: LoadColumn[] = [
    LoadColumn.FX,
    LoadColumn.FY,
    LoadColumn.FZ,
    LoadColumn.MX,
    LoadColumn.MY,
    LoadColumn.MZ
]

// 加载时必须对上的列；Time 可以没有，没有时用频次表的仿真时间
export const REQUIRED_COLUMNS: LoadColumn[] = [LoadColumn.SPEED, ...LOAD_COMPONENTS]

// 坐标轴；载荷文件的轴可以带负号，表示取反
export type Axis = 'x' | 'y' | 'z'
export type SourceAxis = Axis | '-x' | '-y' | '-z'

export const SOURCE_AXES: SourceAxis[] = ['x', 'y', 'z', '-x', '-y', '-z']

// 绕各轴的力矩，不管正反：Romax z 轴取的是载荷文件的哪个轴，那个轴上的力矩就是绕转轴的扭矩
export const MOMENT_OF_AXIS: Record<SourceAxis, LoadColumn> = {
    x: LoadColumn.MX,
    '-x': LoadColumn.MX,
    y: LoadColumn.MY,
    '-y': LoadColumn.MY,
    z: LoadColumn.MZ,
    '-z': LoadColumn.MZ
}

// 文件里认不出列名时按这个顺序对（网页版的默认顺序）
export const DEFAULT_COLUMN_ORDER: LoadColumn[] = [
    LoadColumn.TIME,
    LoadColumn.SPEED,
    LoadColumn.MX,
    LoadColumn.MY,
    LoadColumn.MZ,
    LoadColumn.FX,
    LoadColumn.FY,
    LoadColumn.FZ
]

// 区间表每行 11 格：下界、9 个分段点、上界
export const INTERVAL_SLOTS = 11
