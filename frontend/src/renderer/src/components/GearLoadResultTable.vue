<template>
    <div class="table-wrap">
        <n-data-table
            size="small"
            :bordered="false"
            :columns="columns"
            :data="rows"
            :row-key="(row: ResultRow) => row.key"
            :row-props="rowProps"
            :scroll-x="scrollX"
            flex-height
            class="result-table"
        />
    </div>
</template>

<script setup lang="ts">
// 齿轮载荷的结果表：每级一列，分输入、齿轮载荷、部件转速、等效直径四组，看的是结果区选中的那一组工况。
// 参数名、分组名照网页版的英文原名；符号前一个是 Planetary 级的、后一个是 Helical 级的
import { computed, h, type HTMLAttributes } from 'vue'
import { NDataTable, type DataTableColumns } from 'naive-ui'
import type { StageResult, StageValue } from '@renderer/api/gearLoad'
import {
    DIAMETER_LINES,
    GEAR_LOAD_LINES,
    InputParam,
    SPEED_LINES,
    stageName,
    type ResultLine
} from '@renderer/constants/gearLoad'
import { useGearLoadStore } from '@renderer/stores/gearLoad'

// 一行结果；group 是分组的标题行，横跨整行
interface ResultRow {
    key: string
    group?: string
    parameter?: string
    symbol?: string
    cells?: string[]
}

const PARAMETER_WIDTH = 250
const SYMBOL_WIDTH = 120
const STAGE_WIDTH = 104

const store = useGearLoadStore()

// 算不出来的格子显示 —；没算到的级留空
const format = (value: StageValue | undefined): string => {
    if (value === undefined) return ''
    if (value === '') return '—'
    if (value === 'Infinity') return '∞'
    if (value === '-Infinity') return '−∞'
    const number = Number(value)
    return Number.isFinite(number) ? number.toFixed(3) : String(value)
}

const resultOf = (index: number): StageResult | undefined => {
    const key = store.stages[index]
    return key ? store.results[key] : undefined
}

// 每级的输入扭矩、转速：Stage I 是选中的工况，后面各级接上一级的输出
const inputCell = (index: number, position: 1 | 2): string => {
    if (!resultOf(index)) return ''
    if (index === 0) {
        const condition = store.conditions[store.selected]
        return format(position === 1 ? condition?.torque : condition?.rpm)
    }
    return format(resultOf(index - 1)?.input_data[position])
}

const lineRows = (
    prefix: string,
    lines: ResultLine[],
    pick: (result: StageResult) => StageValue[]
): ResultRow[] =>
    lines.map((line, position) => ({
        key: `${prefix}-${position}`,
        ...line,
        cells: store.stages.map((_, index) => {
            const result = resultOf(index)
            return result ? format(pick(result)[position]) : ''
        })
    }))

const rows = computed<ResultRow[]>(() => [
    { key: 'input', group: 'Input data' },
    {
        key: 'input-torque',
        parameter: InputParam.TORQUE,
        symbol: 'T',
        cells: store.stages.map((_, index) => inputCell(index, 1))
    },
    {
        key: 'input-speed',
        parameter: InputParam.SPEED,
        symbol: 'n',
        cells: store.stages.map((_, index) => inputCell(index, 2))
    },
    { key: 'loads', group: 'Gear loads' },
    ...lineRows('load', GEAR_LOAD_LINES, (result) => result.gear_loads),
    { key: 'speeds', group: 'Speed of components' },
    ...lineRows('speed', SPEED_LINES, (result) => result.speed_of_components),
    {
        key: 'diameters',
        group: 'Equivalent diameter - Input data for modelling planet wheel and pinions'
    },
    ...lineRows('diameter', DIAMETER_LINES, (result) => result.equivalent_diameter)
])

const columns = computed<DataTableColumns<ResultRow>>(() => [
    {
        key: 'parameter',
        title: '',
        width: PARAMETER_WIDTH,
        // 分组标题横跨整行
        colSpan: (row) => (row.group ? store.stageCount + 2 : 1),
        ellipsis: { tooltip: { contentClass: 'long-tip' } },
        render: (row) =>
            row.group ? h('span', { class: 'group-title' }, row.group) : row.parameter
    },
    { key: 'symbol', title: '', width: SYMBOL_WIDTH, className: 'symbol-cell' },
    ...store.stages.map((key, index) => ({
        key,
        title: () =>
            h(
                'span',
                { class: { 'stage-title': true, 'is-pending': !resultOf(index) } },
                `Stage ${stageName(index)}`
            ),
        minWidth: STAGE_WIDTH,
        align: 'right' as const,
        className: 'num',
        render: (row: ResultRow) => row.cells?.[index] ?? ''
    }))
])

const scrollX = computed(() => PARAMETER_WIDTH + SYMBOL_WIDTH + store.stageCount * STAGE_WIDTH)

const rowProps = (row: ResultRow): HTMLAttributes => (row.group ? { class: 'group-row' } : {})
</script>

<style scoped>
/* render 出来的单元格不带 scoped 标记，要用 :deep */
.result-table :deep(.group-row td) {
    background: var(--subtle);
}

.result-table :deep(.group-title) {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-2);
}

.result-table :deep(.symbol-cell) {
    color: var(--text-3);
}

.result-table :deep(.stage-title.is-pending) {
    color: var(--text-3);
    font-weight: 400;
}
</style>
