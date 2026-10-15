import { defineStore } from 'pinia'
import {
    calculateGearLoads,
    exportGearLoads,
    type CalculateResult,
    type ConditionRow,
    type HistoryDetail,
    type HistoryForm,
    type HistorySaveParams,
    type InputRow,
    type StageValue
} from '@renderer/api/gearLoad'
import {
    CHAINED_PARAMS,
    GearArrangement,
    HelixHand,
    InputParam,
    NUMBER_PARAMS,
    WEB_STAGES,
    stageKey,
    stageName,
    type GearStage
} from '@renderer/constants/gearLoad'

const PARAMS: string[] = Object.values(InputParam)

// 新加的一级同网页版的空列：布置 Planetary、旋向 L，其余空着
const defaultValue = (parameter: string): string => {
    if (parameter === InputParam.ARRANGEMENT) return GearArrangement.PLANETARY
    if (parameter === InputParam.HELIX_HAND) return HelixHand.LEFT
    return ''
}

// 网页版的 editable：布置、旋向是下拉框，其余是输入框；网页版回填历史记录时靠它
const isEditable = (parameter: string): boolean =>
    parameter !== InputParam.ARRANGEMENT && parameter !== InputParam.HELIX_HAND

const isChained = (parameter: string): boolean => CHAINED_PARAMS.some((item) => item === parameter)

const stageKeys = (count: number): GearStage[] =>
    Array.from({ length: count }, (_, index) => stageKey(index))

// 输入表有几级：从 stageI 起连着数
const countStages = (rows: InputRow[]): number => {
    let count = 0
    while (rows.some((row) => stageKey(count) in row)) count++
    return count
}

const createInputData = (count: number): InputRow[] =>
    PARAMS.map((parameter) => {
        const row = { parameter, editable: isEditable(parameter) } as InputRow
        for (const key of stageKeys(count)) row[key] = defaultValue(parameter)
        return row
    })

// 历史记录里的输入表补齐成 16 行、顺序同网页版，级数按记录里有几级，至少一级
const normalizeInputData = (rows: InputRow[]): InputRow[] => {
    const keys = stageKeys(Math.max(countStages(rows), 1))
    return PARAMS.map((parameter) => {
        const source = rows.find((row) => row.parameter === parameter)
        const row = { parameter, editable: isEditable(parameter) } as InputRow
        for (const key of keys) row[key] = source?.[key] ?? defaultValue(parameter)
        return row
    })
}

// 同网页版：结果填回输入表时转成字符串，算不出来的是空串
const toCell = (value: StageValue | undefined): string => value?.toString() || ''

// 参数连着改时，只认最后一次计算的结果
let calcSeq = 0

export const useGearLoadStore = defineStore('gearLoad', {
    state: () => ({
        // 基础设置：历史记录按登录的人 + 这三项存
        form: { gearUnit: '', windTurbine: '', loadSpectrum: '' } as HistoryForm,
        // 输入表，网页版的写法：一行一个参数，各级的值在 stageI、stageII…… 里
        inputData: createInputData(WEB_STAGES),
        // 多工况：粘贴进来的扭矩、转速，原样留着字符串
        conditions: [] as ConditionRow[],
        // 结果区看的那一组工况，Stage I 的扭矩、转速就是它
        selected: 0,
        // 参数栏正在填的那一级
        current: 0,
        results: {} as CalculateResult,
        calculating: false,
        error: '',
        exporting: false
    }),

    getters: {
        stageCount: (state): number => countStages(state.inputData),

        stages(): GearStage[] {
            return stageKeys(this.stageCount)
        },

        currentKey(): GearStage {
            return stageKey(this.current)
        },

        // 某一级某个参数在输入表里的值
        cell:
            (state) =>
            (parameter: InputParam, key: GearStage): string =>
                state.inputData.find((row) => row.parameter === parameter)?.[key] ?? '',

        // 某一级还没填的参数：布置、旋向总有值；Stage I 还要填功率，扭矩、转速来自工况
        missing(): (index: number) => InputParam[] {
            return (index: number): InputParam[] => {
                const key = stageKey(index)
                const required = index === 0 ? [...NUMBER_PARAMS, InputParam.POWER] : NUMBER_PARAMS
                return required.filter((parameter) => !this.cell(parameter, key).trim())
            }
        },

        // 算不了的原因：没有工况，或 Stage I 没填全
        calcHint(): string {
            if (!this.conditions.length) return '请先粘贴工况'
            const missing = this.missing(0).length
            return missing ? `Stage I 还有 ${missing} 项没填` : ''
        },

        computedCount(): number {
            return this.stages.filter((key) => this.results[key]).length
        },

        // 第一个没算到的级为什么没算：它还有参数没填，它和后面的级都没算
        pendingNote(): string {
            if (this.calcHint || this.error || this.computedCount >= this.stageCount) return ''
            const index = this.stages.findIndex((_, stage) => this.missing(stage).length > 0)
            if (index < 0) return ''
            return `Stage ${stageName(index)} 还有 ${this.missing(index).length} 项没填，它和后面的级没算`
        },

        // 参数改了才重算：二级以后的功率、扭矩、转速是算出来填的，不算在内
        calcKey(): string {
            return JSON.stringify(
                this.inputData.map((row) =>
                    isChained(row.parameter) ? [row.parameter, row.stageI] : row
                )
            )
        },

        historyLabel: (state): string =>
            [state.form.gearUnit, state.form.windTurbine, state.form.loadSpectrum].join(' / '),

        saveHint: (state): string =>
            state.form.gearUnit && state.form.windTurbine && state.form.loadSpectrum
                ? ''
                : '请先填 Gear unit、Wind turbine、Load spectrum：历史记录按这三项存',

        // 存成历史记录的报文同网页版 Ctrl+S 发的：基础设置、整张输入表和多工况
        historyParams(): HistorySaveParams {
            return {
                formData: { ...this.form },
                inputData: this.inputData,
                selectedData: this.conditions
            }
        }
    },

    actions: {
        setCell(parameter: InputParam, key: GearStage, value: string) {
            const row = this.inputData.find((item) => item.parameter === parameter)
            if (row) row[key] = value
        },

        addStage() {
            const key = stageKey(this.stageCount)
            for (const row of this.inputData) row[key] = defaultValue(row.parameter)
            this.current = this.stageCount - 1
        },

        removeLastStage() {
            if (this.stageCount <= 1) return
            const key = stageKey(this.stageCount - 1)
            for (const row of this.inputData) delete row[key]
            delete this.results[key]
            this.current = Math.min(this.current, this.stageCount - 1)
        },

        importConditions(conditions: ConditionRow[]) {
            this.conditions = conditions
            this.selectCondition(0)
        },

        // 选一组工况：Stage I 的扭矩、转速换成这一组的
        selectCondition(index: number) {
            const condition = this.conditions[index]
            this.selected = condition ? index : 0
            this.setCell(InputParam.TORQUE, 'stageI', condition?.torque ?? '')
            this.setCell(InputParam.SPEED, 'stageI', condition?.rpm ?? '')
        },

        // 同网页版：上一级算完，把它的功率、输出扭矩、输出转速填到下一级。有填进新值才返回 true
        fillChained(results: CalculateResult): boolean {
            let changed = false
            this.stages.forEach((key, index) => {
                const result = results[key]
                const next = this.stages[index + 1]
                if (!result || !next) return
                CHAINED_PARAMS.forEach((parameter, position) => {
                    const value = toCell(result.input_data[position])
                    if (this.cell(parameter, next) === value) return
                    this.setCell(parameter, next, value)
                    changed = true
                })
            })
            return changed
        },

        // 后端只算整列填满的级，二级以后的功率、扭矩、转速要等上一级算完才填得上，网页版因此要点好几次。
        // 这里算完一轮就填好接着算，填进去的值不再变就是都算完了
        async calculate() {
            const seq = ++calcSeq
            if (this.calcHint) {
                this.results = {}
                this.error = ''
                this.calculating = false
                return
            }
            this.calculating = true
            try {
                let results: CalculateResult = {}
                for (let round = 0; round <= this.stageCount; round++) {
                    results = await calculateGearLoads(this.inputData)
                    if (seq !== calcSeq) return
                    if (!this.fillChained(results)) break
                }
                this.results = results
                this.error = ''
            } catch (err) {
                if (seq !== calcSeq) return
                this.results = {}
                this.error = (err as Error).message
            } finally {
                if (seq === calcSeq) this.calculating = false
            }
        },

        // 先按现在的参数算一遍，二级以后的功率填好了，后端才认得出有几级
        async exportExcel(path: string) {
            this.exporting = true
            try {
                await this.calculate()
                await exportGearLoads({
                    inputData: this.inputData,
                    selectedData: this.conditions,
                    path
                })
            } finally {
                this.exporting = false
            }
        },

        // 同网页版：基础设置、输入表、多工况换成记录里的，记录里没有输入表或多工况就留着现在的；
        // 结果区看的那一组是 Stage I 的扭矩、转速对得上的第一组
        applyHistory(detail: HistoryDetail) {
            this.form = { ...detail.formData }
            if (detail.inputData) this.inputData = normalizeInputData(detail.inputData)
            if (detail.selectedData) this.conditions = detail.selectedData
            const torque = this.cell(InputParam.TORQUE, 'stageI')
            const speed = this.cell(InputParam.SPEED, 'stageI')
            const index = this.conditions.findIndex(
                (item) => item.torque === torque && item.rpm === speed
            )
            this.selectCondition(Math.max(index, 0))
            this.current = 0
            this.results = {}
        }
    }
})
