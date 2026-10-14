import { defineStore } from 'pinia'
import {
    clearLoadedData,
    loadData,
    previewLoadDir,
    reduceLoad,
    type AxisMapping,
    type ComponentStats,
    type HistoryRecord,
    type LoadParams,
    type PreviewResult,
    type ReduceParams
} from '@renderer/api/simpleLoad'
import {
    DEFAULT_COLUMN_ORDER,
    INTERVAL_SLOTS,
    LOAD_COMPONENTS,
    LoadColumn,
    MOMENT_OF_AXIS,
    REQUIRED_COLUMNS
} from '@renderer/constants/simpleLoad'

// 区间表的一行：11 格依次是下界、9 个分段点、上界，没填的是 null
export type IntervalRow = (number | null)[]

// 预览里 txt 的一列：文件里的列名（认不出时为空串）和第一行数据里的值
export interface PreviewColumn {
    index: number
    name: string
    sample: string
}

// 区间表一行的状态：分了几段，边界是否从小到大
export interface IntervalState {
    segments: number
    valid: boolean
}

export interface LoadedData {
    fileCount: number
    rowCount: number
    stats: Partial<Record<LoadColumn, ComponentStats>>
    // 加载时的参数快照：和现在的参数对不上，说明加载后又改过，要重新加载
    key: string
}

export interface ReduceResult {
    cellCount: number
    files: string[]
    // 缩减时的参数快照：对不上说明改过区间或参数，结果已经不是现在这套参数的
    key: string
}

export type SimpleLoadTask = 'load' | 'reduce'
export type SimpleLoadStatus = 'idle' | 'processing' | 'done' | 'error'

// ========== 预览：和后端读 txt 一样按空白切列 ==========
const NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/

const splitData = (line: string): string[] => line.trim().split(/\s+/).filter(Boolean)

// 列名里常有空格（Rotor speed[rpm]），有 tab 就按 tab 切
const splitHeader = (line: string): string[] =>
    (line.includes('\t') ? line.split('\t') : line.trim().split(/\s+/))
        .map((cell) => cell.trim())
        .filter(Boolean)

const isDataLine = (line: string): boolean => {
    const cells = splitData(line)
    return cells.length > 0 && cells.every((cell) => NUMBER.test(cell))
}

// 第一行全是数字的行之前的都跳过（列名、END_OF_HEADER 这类）
const detectSkipRows = (lines: string[]): number => Math.max(0, lines.findIndex(isDataLine))

// 列名里的分量写法，单位方括号去掉后按字母数字切词，词对上就算
const COLUMN_WORDS: [LoadColumn, string[]][] = [
    [LoadColumn.TIME, ['time']],
    [LoadColumn.SPEED, ['speed', 'rpm']],
    [LoadColumn.FX, ['fx']],
    [LoadColumn.FY, ['fy']],
    [LoadColumn.FZ, ['fz']],
    [LoadColumn.MX, ['mx']],
    [LoadColumn.MY, ['my']],
    [LoadColumn.MZ, ['mz']]
]

const nameWords = (name: string): string[] =>
    name
        .replace(/\[[^\]]*\]/g, ' ')
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .filter(Boolean)

// 按列名认分量，每个分量只认第一列；文件里没有列名时按网页版的默认顺序
const matchColumns = (columns: PreviewColumn[]): (LoadColumn | null)[] => {
    if (columns.every((column) => column.name === '')) {
        return columns.map((_, index) => DEFAULT_COLUMN_ORDER[index] ?? null)
    }
    const used = new Set<LoadColumn>()
    return columns.map((column) => {
        const words = nameWords(column.name)
        const hit = COLUMN_WORDS.find(
            ([target, keys]) => !used.has(target) && keys.some((key) => words.includes(key))
        )
        if (!hit) return null
        used.add(hit[0])
        return hit[0]
    })
}

// ========== 区间表 ==========
const emptyRow = (): IntervalRow => Array<number | null>(INTERVAL_SLOTS).fill(null)

const emptyIntervals = (): Partial<Record<LoadColumn, IntervalRow>> =>
    Object.fromEntries(LOAD_COMPONENTS.map((component) => [component, emptyRow()]))

// 一行里填了的边界，按格子顺序
const filledEdges = (row: IntervalRow | undefined): number[] =>
    (row ?? []).filter((value): value is number => value !== null)

// ========== 历史记录 ==========
// 回填时用记录里的跳过行数和列对应，不按文件重新认
interface FileFormat {
    skipRows: number
    columns: (LoadColumn | null)[]
}

// 列对应补齐或截到文件的列数：网页版存的列名可以比文件的列少，后面的列不用
const fitColumns = (columns: (LoadColumn | null)[], count: number): (LoadColumn | null)[] =>
    Array.from({ length: count }, (_, index) => columns[index] ?? null)

export const useSimpleLoadStore = defineStore('simpleLoad', {
    state: () => ({
        // ---- 数据：这几项改了要重新加载 ----
        loadDir: '',
        freqTablePath: '',
        skipRows: 0,
        // txt 每一列对应的分量，null 是不用的列
        columns: [] as (LoadColumn | null)[],
        unitForce: 1000,
        unitMoment: 1000,
        unitSpeed: 1,

        preview: null as PreviewResult | null,
        previewing: false,
        previewError: '',

        outputDir: '',

        // ---- 缩减参数：改了直接再缩减 ----
        // 依次是 Romax 的 x、y、z
        axisMapping: [
            { romax: 'x', origin: '-y' },
            { romax: 'y', origin: '-z' },
            { romax: 'z', origin: 'x' }
        ] as AxisMapping[],
        keepTorque: false,
        slope: 4.05,
        temperature: 60,
        tol: 0.0001,
        // 按分量存，换坐标映射或开关保留扭矩时，各分量的区间跟着自己走
        intervals: emptyIntervals(),

        selectedComponent: LoadColumn.FX,

        loaded: null as LoadedData | null,
        reduceResult: null as ReduceResult | null,

        // ---- 最近一次加载或缩减的进度 ----
        task: 'load' as SimpleLoadTask,
        status: 'idle' as SimpleLoadStatus,
        stage: '',
        percent: 0,
        error: ''
    }),

    getters: {
        isBusy: (state) => state.status === 'processing',
        isLoading: (state) => state.status === 'processing' && state.task === 'load',
        isReducing: (state) => state.status === 'processing' && state.task === 'reduce',

        // 预览的第一行数据切出来的各列，列名取跳过的行里第一个列数对得上的
        previewColumns: (state): PreviewColumn[] => {
            const lines = state.preview?.lines ?? []
            const sample = lines[state.skipRows]
            if (sample === undefined) return []
            const values = splitData(sample)
            const names = lines
                .slice(0, state.skipRows)
                .map(splitHeader)
                .find((cells) => cells.length === values.length)
            return values.map((value, index) => ({
                index,
                name: names?.[index] ?? '',
                sample: value
            }))
        },

        columnIssue: (state): string => {
            const used = state.columns.filter((column): column is LoadColumn => column !== null)
            const repeated = Object.values(LoadColumn).filter(
                (column) => used.filter((item) => item === column).length > 1
            )
            if (repeated.length) return `${repeated.join('、')} 对了不止一列`
            const missing = REQUIRED_COLUMNS.filter((column) => !used.includes(column))
            return missing.length ? `列对应缺少 ${missing.join('、')}` : ''
        },

        loadKey: (state): string =>
            JSON.stringify([
                state.loadDir,
                state.freqTablePath,
                state.columns,
                state.skipRows,
                state.unitForce,
                state.unitMoment,
                state.unitSpeed
            ]),

        isStale(): boolean {
            return this.loaded !== null && this.loaded.key !== this.loadKey
        },

        loadHint(): string {
            if (this.isBusy) return ''
            if (!this.loadDir) return '请先选择载荷文件夹'
            if (!this.freqTablePath) return '请先选择频次表'
            if (Math.min(this.unitForce, this.unitMoment, this.unitSpeed) <= 0) {
                return '力、力矩、转速的转换系数要大于 0'
            }
            if (this.previewing) return '正在读取载荷文件夹…'
            if (!this.preview) return this.previewError || '载荷文件夹还没读出来'
            if (!this.columns.length) return '文件开头没找到数据行，到「文件格式」里改跳过的行数'
            return this.columnIssue && `${this.columnIssue}，到「文件格式」里改`
        },

        canLoad(): boolean {
            return !this.isBusy && !this.loadHint
        },

        // 绕 Romax z 轴的扭矩，默认不参与分组
        torqueComponent: (state): LoadColumn => MOMENT_OF_AXIS[state.axisMapping[2]?.origin ?? 'z'],

        participating(): LoadColumn[] {
            return this.keepTorque
                ? LOAD_COMPONENTS
                : LOAD_COMPONENTS.filter((component) => component !== this.torqueComponent)
        },

        // 分布图和区间表高亮的分量：选中的不参与分组了就换成第一个
        activeComponent(): LoadColumn {
            return this.participating.includes(this.selectedComponent)
                ? this.selectedComponent
                : this.participating[0]!
        },

        intervalStates: (state): Partial<Record<LoadColumn, IntervalState>> =>
            Object.fromEntries(
                LOAD_COMPONENTS.map((component) => {
                    const edges = filledEdges(state.intervals[component])
                    return [
                        component,
                        {
                            segments: Math.max(edges.length - 1, 0),
                            valid: edges.every((edge, i) => i === 0 || edge > edges[i - 1]!)
                        }
                    ]
                })
            ),

        // 总格子数：各分量段数相乘，还没分段的分量不算
        totalCells(): number {
            const counts = this.participating
                .map((component) => this.intervalStates[component]?.segments ?? 0)
                .filter((count) => count > 0)
            return counts.length ? counts.reduce((product, count) => product * count, 1) : 0
        },

        axisIssue: (state): string => {
            const axes = new Set(
                state.axisMapping.map((mapping) => mapping.origin.replace('-', ''))
            )
            return axes.size === 3 ? '' : 'Romax 坐标里载荷文件的 x、y、z 要各用一次'
        },

        intervalIssue(): string {
            for (const component of this.participating) {
                const state = this.intervalStates[component]
                if (!state || state.segments < 1) return `${component} 至少要有下界和上界`
                if (!state.valid) return `${component} 的边界没有从小到大`
            }
            return ''
        },

        reduceParams(): ReduceParams {
            return {
                intervals: Object.fromEntries(
                    this.participating.map((component) => [
                        component,
                        filledEdges(this.intervals[component])
                    ])
                ),
                axisMapping: this.axisMapping.map((mapping) => ({ ...mapping })),
                keepTorque: this.keepTorque,
                slope: this.slope,
                temperature: this.temperature,
                tol: this.tol,
                outputDir: this.outputDir
            }
        },

        reduceKey(): string {
            return JSON.stringify([this.reduceParams, this.loaded?.key])
        },

        // 和现在这套参数对得上的缩减结果
        currentReduceResult(): ReduceResult | null {
            return this.reduceResult?.key === this.reduceKey ? this.reduceResult : null
        },

        reduceHint(): string {
            if (this.isBusy) return ''
            if (!this.loaded) return '请先加载数据'
            if (this.isStale) return '数据相关的参数改过，请重新加载'
            if (!this.outputDir) return '请先选择输出目录'
            if (this.slope <= 0) return '转换系数要大于 0'
            return this.axisIssue || this.intervalIssue
        },

        canReduce(): boolean {
            return !this.isBusy && !this.reduceHint
        }
    },

    actions: {
        // 读载荷文件夹里第一个 txt 的开头，认出跳过几行、每列是什么；回填历史配置时用记录里的
        async previewFolder(format?: FileFormat) {
            const dir = this.loadDir
            this.preview = null
            this.previewError = ''
            if (!dir) {
                this.columns = []
                this.previewing = false
                return
            }
            this.previewing = true
            try {
                const result = await previewLoadDir(dir)
                if (dir !== this.loadDir) return
                this.preview = result
                this.skipRows = format ? format.skipRows : detectSkipRows(result.lines)
                this.columns = format
                    ? fitColumns(format.columns, this.previewColumns.length)
                    : matchColumns(this.previewColumns)
            } catch (err) {
                if (dir === this.loadDir) this.previewError = (err as Error).message
            } finally {
                if (dir === this.loadDir) this.previewing = false
            }
        },

        // 回填网页版存的一条配置：路径、文件格式、转换系数、缩减参数和区间表都换成记录里的，再读一遍载荷文件夹
        applyHistory(record: HistoryRecord) {
            this.loadDir = record.loadDir
            this.freqTablePath = record.freqTablePath
            this.outputDir = record.outputDir
            this.unitForce = record.unitForce
            this.unitMoment = record.unitMoment
            this.unitSpeed = record.unitSpeed
            this.axisMapping = record.axisMapping.map((mapping) => ({ ...mapping }))
            this.keepTorque = record.keepTorque
            this.slope = record.slope
            this.temperature = record.temperature
            this.tol = record.tol
            this.intervals = Object.fromEntries(
                LOAD_COMPONENTS.map((component) => {
                    const row = record.intervals[component] ?? []
                    return [
                        component,
                        Array.from({ length: INTERVAL_SLOTS }, (_, i) => row[i] ?? null)
                    ]
                })
            )
            this.previewFolder({ skipRows: record.skipRows, columns: record.columns })
        },

        setSkipRows(value: number) {
            this.skipRows = value
            this.columns = matchColumns(this.previewColumns)
        },

        setColumn(index: number, value: LoadColumn | null) {
            this.columns[index] = value
        },

        setEdge(component: LoadColumn, slot: number, value: number | null) {
            const row = this.intervals[component]
            if (row) row[slot] = value
        },

        begin(task: SimpleLoadTask) {
            this.task = task
            this.status = 'processing'
            this.stage = '正在连接后端…'
            this.percent = 0
            this.error = ''
        },

        fail(message: string) {
            this.status = 'error'
            this.error = message
        },

        startLoad() {
            if (!this.canLoad) return
            const key = this.loadKey
            const params: LoadParams = {
                loadDir: this.loadDir,
                freqTablePath: this.freqTablePath,
                columns: [...this.columns],
                skipRows: this.skipRows,
                unitForce: this.unitForce,
                unitMoment: this.unitMoment,
                unitSpeed: this.unitSpeed
            }
            // 后端开始加载前就丢掉旧数据，这边也跟着清掉
            this.loaded = null
            this.reduceResult = null
            this.begin('load')
            loadData(params, (msg) => {
                if (msg.type === 'progress') {
                    this.stage = msg.stage
                    this.percent = msg.percent
                } else if (msg.type === 'done') {
                    const stats: Partial<Record<LoadColumn, ComponentStats>> = {}
                    for (const item of msg.components) {
                        stats[item.component] = item
                        // 下界、上界填数据的最值，中间的分段点不动
                        this.setEdge(item.component, 0, item.min)
                        this.setEdge(item.component, INTERVAL_SLOTS - 1, item.max)
                    }
                    this.loaded = { fileCount: msg.fileCount, rowCount: msg.rowCount, stats, key }
                    this.status = 'done'
                    this.percent = 100
                } else {
                    this.fail(msg.message)
                }
            })
        },

        startReduce() {
            if (!this.canReduce) return
            const params = this.reduceParams
            const key = this.reduceKey
            this.reduceResult = null
            this.begin('reduce')
            reduceLoad(params, (msg) => {
                if (msg.type === 'progress') {
                    this.stage = msg.stage
                    this.percent = msg.percent
                } else if (msg.type === 'done') {
                    this.reduceResult = { cellCount: msg.cellCount, files: msg.files, key }
                    this.status = 'done'
                    this.percent = 100
                } else {
                    this.fail(msg.message)
                }
            })
        },

        // 丢掉后端加载过的数据，参数和区间表都留着；后端连不上时数据也不在了，这边照样清
        async clearData() {
            try {
                await clearLoadedData()
            } finally {
                this.loaded = null
                this.reduceResult = null
                this.status = 'idle'
            }
        }
    }
})
