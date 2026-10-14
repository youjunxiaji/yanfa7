<template>
    <div class="column-map">
        <p v-if="!store.preview" class="map-note" :class="{ 'is-error': !!store.previewError }">
            <Info :size="13" />
            {{ emptyNote }}
        </p>
        <template v-else>
            <div class="file-info num">
                第一个文件 {{ store.preview.sampleFile }}，共 {{ store.preview.fileCount }} 个
                txt、{{ formatBytes(store.preview.totalSize) }}
            </div>
            <div class="skip-row">
                <span class="skip-label">跳过前</span>
                <NumberInput
                    class="skip-input"
                    :model-value="store.skipRows"
                    :min="0"
                    :max="maxSkip"
                    size="small"
                    suffix="行"
                    @update:model-value="store.setSkipRows"
                />
                <span class="skip-note">列名、END_OF_HEADER 这类；按第一行纯数字自动认出</span>
            </div>

            <div class="raw-lines">
                <div
                    v-for="line in rawLines"
                    :key="line.no"
                    class="raw-line"
                    :class="{ 'is-skipped': line.skipped }"
                >
                    <span class="raw-no num">{{ line.no }}</span>
                    <span class="raw-text">{{ line.text }}</span>
                    <span v-if="line.skipped" class="raw-tag">跳过</span>
                </div>
            </div>

            <n-data-table
                :columns="tableColumns"
                :data="store.previewColumns"
                :row-key="rowKey"
                size="small"
                :bordered="false"
            />

            <p class="map-note" :class="{ 'is-error': !!store.columnIssue }">
                <Info :size="13" />
                {{
                    store.columnIssue ||
                    '必需 speed[rpm] 和六个力 / 力矩；Time[s] 可选，没有就用频次表里的仿真时间'
                }}
            </p>
        </template>
    </div>
</template>

<script setup lang="ts">
// 「文件格式」弹窗里的列对应：预览第一个 txt 的开头，给每一列选它是哪个分量，不用的列选「不使用」
import { computed, h, type VNode } from 'vue'
import { NDataTable, NEllipsis, NSelect, type DataTableColumns, type SelectOption } from 'naive-ui'
import { Info } from '@lucide/vue'
import { LoadColumn } from '@renderer/constants/simpleLoad'
import { useSimpleLoadStore, type PreviewColumn } from '@renderer/stores/simpleLoad'
import NumberInput from '@renderer/components/NumberInput.vue'

// 下拉里「不使用」的取值；Naive 的选项值不能是 null
const UNUSED = ''

// 开头几行里多显示两行数据，看得出从哪一行起是数
const EXTRA_DATA_LINES = 2

const formatBytes = (n: number): string => {
    if (n >= 1073741824) return `${(n / 1073741824).toFixed(1)} GB`
    if (n >= 1048576) return `${(n / 1048576).toFixed(1)} MB`
    return `${Math.max(1, Math.round(n / 1024))} KB`
}

const store = useSimpleLoadStore()

const options: SelectOption[] = [
    { label: '不使用', value: UNUSED },
    ...Object.values(LoadColumn).map((column) => ({ label: column, value: column }))
]

const emptyNote = computed(() => {
    if (store.previewing) return '正在读取载荷文件夹…'
    return store.previewError || '先选载荷文件夹，读出第一个 txt 的开头后在这里核对每一列'
})

const maxSkip = computed(() => Math.max((store.preview?.lines.length ?? 1) - 1, 0))

const rawLines = computed(() =>
    (store.preview?.lines ?? [])
        .slice(0, store.skipRows + 1 + EXTRA_DATA_LINES)
        .map((text, index) => ({ no: index + 1, text, skipped: index < store.skipRows }))
)

// 同一个分量对了不止一列时，这几列的下拉都标红
const repeated = computed(() => {
    const used = store.columns.filter((column): column is LoadColumn => column !== null)
    return new Set(used.filter((column, index) => used.indexOf(column) !== index))
})

const rowKey = (row: PreviewColumn): number => row.index

const handleSelect = (index: number, value: string): void => {
    store.setColumn(index, Object.values(LoadColumn).find((column) => column === value) ?? null)
}

const renderSelect = (row: PreviewColumn): VNode => {
    const value = store.columns[row.index] ?? null
    return h(NSelect, {
        value: value ?? UNUSED,
        options,
        size: 'small',
        disabled: store.isBusy,
        status: value !== null && repeated.value.has(value) ? 'error' : undefined,
        'onUpdate:value': (next: string) => handleSelect(row.index, next)
    })
}

const tableColumns: DataTableColumns<PreviewColumn> = [
    {
        key: 'index',
        title: '#',
        width: 48,
        align: 'center',
        render: (row) => h('span', { class: 'num cell-muted' }, String(row.index + 1))
    },
    {
        key: 'name',
        title: '文件里的列名',
        render: (row) =>
            row.name
                ? h(NEllipsis, { tooltip: { delay: 200 } }, { default: () => row.name })
                : h('span', { class: 'cell-muted' }, '—')
    },
    {
        key: 'sample',
        title: '第一行数据',
        width: 150,
        align: 'right',
        render: (row) => h('span', { class: 'num' }, row.sample)
    },
    { key: 'column', title: '对应为', width: 150, render: renderSelect }
]
</script>

<style scoped>
.column-map {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.file-info {
    overflow: hidden;
    font-size: 12px;
    color: var(--text-3);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.skip-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}

.skip-label {
    color: var(--text-2);
}

.skip-input {
    width: 88px;
}

.skip-note {
    font-size: 12px;
    color: var(--text-3);
}

/* 文件开头的原文：跳过的行灰掉，一行放不下就截断 */
.raw-lines {
    flex-shrink: 0;
    padding: 6px 0;
    font-family: var(--font-mono);
    font-size: 12px;
    background: var(--subtle);
    border: 1px solid var(--border);
    border-radius: 8px;
}

.raw-line {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 22px;
    padding: 0 12px;
    color: var(--text-1);
}

.raw-line.is-skipped {
    color: var(--text-3);
}

.raw-no {
    flex-shrink: 0;
    width: 22px;
    text-align: right;
    color: var(--text-3);
}

.raw-text {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: pre;
    tab-size: 4;
}

.raw-tag {
    flex-shrink: 0;
    font-family: var(--font-sans);
    color: var(--text-3);
}

.map-note {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    font-size: 12px;
    color: var(--text-3);
}

.map-note.is-error {
    color: var(--danger);
}

/* 表格单元格由 render 函数生成，不带本组件的 scoped 标记 */
.column-map :deep(.cell-muted) {
    color: var(--text-3);
}
</style>
