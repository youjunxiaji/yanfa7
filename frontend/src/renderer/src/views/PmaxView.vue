<template>
    <div class="page">
        <PageHeader />
        <div class="tool-body">
            <section class="param-pane">
                <div class="param-scroll">
                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">数据</span>
                            <button
                                v-if="tableData.length"
                                class="link-btn is-danger"
                                @click="clearAll"
                            >
                                清空
                            </button>
                        </div>
                        <n-button block @click="openPasteDialog">
                            <template #icon><ClipboardPaste :size="16" /></template>
                            {{ tableData.length ? '重新粘贴数据' : '粘贴数据' }}
                        </n-button>
                        <div class="section-note num">
                            {{
                                tableData.length
                                    ? `已导入 ${tableData.length} 行`
                                    : '从 Excel 复制 4 列后粘贴'
                            }}
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">分箱参数</span>
                            <span class="section-meta">单位 MPa</span>
                        </div>
                        <div class="bin-grid">
                            <span />
                            <span class="bin-head">前轴承</span>
                            <span class="bin-head">后轴承</span>
                            <template v-for="field in BIN_FIELDS" :key="field.key">
                                <span class="field-label">{{ field.label }}</span>
                                <NumberInput
                                    v-model="binConfig.front[field.key]"
                                    :step="field.step"
                                    :min="field.min"
                                    :max="field.max"
                                />
                                <NumberInput
                                    v-model="binConfig.rear[field.key]"
                                    :step="field.step"
                                    :min="field.min"
                                    :max="field.max"
                                />
                            </template>
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">图表样式</span>
                        </div>
                        <div class="sub-label">字号</div>
                        <div class="font-grid">
                            <label v-for="field in FONT_FIELDS" :key="field.key" class="font-field">
                                <span class="font-label">{{ field.label }}</span>
                                <NumberInput v-model="chartConfig[field.key]" :min="1" :max="30" />
                            </label>
                        </div>
                        <div class="field">
                            <span class="field-label">图形尺寸</span>
                            <div class="field-control">
                                <NumberInput
                                    v-model="chartConfig.width"
                                    :min="1"
                                    :max="20"
                                    suffix="in"
                                />
                                <span class="pair-sep">×</span>
                                <NumberInput
                                    v-model="chartConfig.height"
                                    :min="1"
                                    :max="20"
                                    suffix="in"
                                />
                            </div>
                        </div>
                        <div class="field">
                            <span class="field-label">图表语言</span>
                            <div class="field-control">
                                <n-tabs
                                    :value="language"
                                    type="segment"
                                    size="small"
                                    :animated="false"
                                    @update:value="handleLanguageChange"
                                >
                                    <n-tab
                                        v-for="lang in LANGUAGE_OPTIONS"
                                        :key="lang"
                                        :name="lang"
                                    >
                                        {{ lang }}
                                    </n-tab>
                                </n-tabs>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="param-footer">
                    <n-button
                        type="primary"
                        size="large"
                        block
                        :disabled="tableData.length === 0"
                        :loading="generating"
                        @click="generateCharts"
                    >
                        <template #icon><ChartColumn :size="15" /></template>
                        {{ generating ? '生成中…' : '生成图表' }}
                    </n-button>
                    <p v-if="tableData.length === 0" class="action-hint">
                        <Info :size="13" />
                        请先粘贴数据
                    </p>
                </div>
            </section>

            <section class="result-pane">
                <div class="result-toolbar">
                    <span class="toolbar-title">图表预览</span>
                    <span v-if="tableData.length" class="count-pill"
                        >{{ tableData.length }} 行</span
                    >
                    <span class="toolbar-spacer" />
                    <span v-if="hasCharts" class="toolbar-note">
                        <Move :size="13" />
                        拖动图片可以直接放进 Word
                    </span>
                </div>
                <div class="result-body">
                    <EmptyState
                        v-if="generating"
                        busy
                        title="正在生成图表…"
                        desc="按分箱参数统计各区间的时间占比"
                    />
                    <div v-else-if="hasCharts" class="chart-scroll">
                        <div v-if="stats.length" class="stat-bar">
                            <div v-for="item in stats" :key="item.label" class="stat">
                                <div class="stat-label">{{ item.label }}</div>
                                <div class="stat-value num">{{ item.value }}</div>
                            </div>
                        </div>
                        <div class="figure-grid">
                            <figure v-for="chart in charts" :key="chart.key" class="figure">
                                <figcaption class="figure-head">
                                    <span>{{ chart.label }}</span>
                                    <span class="figure-hint">
                                        <GripVertical :size="13" />
                                        拖到 Word
                                    </span>
                                </figcaption>
                                <div class="figure-paper">
                                    <img
                                        :src="toLocalFileUrl(chart.path, imgCacheBuster)"
                                        :alt="chart.label"
                                        draggable="true"
                                        @dragstart="handleDragStart($event, chart.path)"
                                    />
                                </div>
                            </figure>
                        </div>
                    </div>
                    <EmptyState
                        v-else-if="tableData.length > 0"
                        :icon="ChartColumn"
                        :title="`已导入 ${tableData.length} 行数据`"
                        desc="确认左侧参数后生成图表"
                        @click="generateCharts"
                    >
                        <n-button type="primary" @click="generateCharts">
                            <template #icon><ChartColumn :size="15" /></template>
                            生成图表
                        </n-button>
                    </EmptyState>
                    <EmptyState
                        v-else
                        :icon="ClipboardPaste"
                        title="暂无数据"
                        desc="从 Excel 复制持续时间和 Pmax 共 4 列，粘贴进来后生成图表"
                        @click="openPasteDialog"
                    >
                        <n-button @click="openPasteDialog">
                            <template #icon><ClipboardPaste :size="16" /></template>
                            粘贴数据
                        </n-button>
                    </EmptyState>
                </div>
            </section>
        </div>

        <n-modal
            v-model:show="pasteDialogVisible"
            preset="card"
            title="粘贴数据"
            :style="{ width: '680px' }"
            :bordered="false"
            :mask-closable="false"
            @after-enter="focusPasteArea"
        >
            <div
                ref="pasteAreaRef"
                class="paste-area"
                :class="{ 'has-data': pendingData.length > 0 }"
                tabindex="0"
                @paste="handlePaste"
            >
                <template v-if="pendingData.length > 0">
                    <n-data-table
                        :columns="PASTE_COLUMNS"
                        :data="pendingData"
                        size="small"
                        :bordered="false"
                        :max-height="300"
                        virtual-scroll
                    />
                    <div class="paste-info">
                        已解析 <b>{{ pendingData.length }}</b> 行，确认后导入
                    </div>
                </template>
                <template v-else>
                    <div class="paste-icon"><ClipboardPaste :size="20" /></div>
                    <div class="paste-title">从 Excel 粘贴数据</div>
                    <div class="paste-desc">
                        点一下这里，再按 <kbd>{{ isMac ? '⌘' : 'Ctrl' }}</kbd> <kbd>V</kbd> 粘贴
                    </div>
                    <div class="paste-cols">
                        <span>持续时间 [h]</span>
                        <span>Pmax (MPa)-前</span>
                        <span>持续时间 [h]</span>
                        <span>Pmax (MPa)-后</span>
                    </div>
                </template>
            </div>
            <template #footer>
                <div class="modal-actions">
                    <n-button @click="cancelPaste">取消</n-button>
                    <n-button
                        type="primary"
                        :disabled="pendingData.length === 0"
                        @click="confirmPaste"
                    >
                        确认导入（{{ pendingData.length }} 行）
                    </n-button>
                </div>
            </template>
        </n-modal>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from 'vue'
import {
    NButton,
    NDataTable,
    NModal,
    NTab,
    NTabs,
    useMessage,
    type DataTableColumns
} from 'naive-ui'
import { ChartColumn, ClipboardPaste, GripVertical, Info, Move } from '@lucide/vue'
import { convertFileSrc } from '@tauri-apps/api/core'
import { Language, LANGUAGE_OPTIONS } from '@renderer/constants/language'
import { analyzePmax, type AnalyzeResponse } from '@renderer/api/pmax'
import PageHeader from '@renderer/components/PageHeader.vue'
import EmptyState from '@renderer/components/EmptyState.vue'
import NumberInput from '@renderer/components/NumberInput.vue'

interface TableRow {
    timeFront: string
    pmaxFront: string
    timeRear: string
    pmaxRear: string
}

interface BinRange {
    min: number
    max: number
    step: number
}

interface ChartConfig {
    titleFontSize: number
    labelFontSize: number
    tickFontSize: number
    textFontSize: number
    width: number
    height: number
}

const BIN_FIELDS: { key: keyof BinRange; label: string; step: number; min: number; max: number }[] =
    [
        { key: 'min', label: '最小值', step: 50, min: 0, max: 100000 },
        { key: 'max', label: '最大值', step: 50, min: 0, max: 100000 },
        { key: 'step', label: '步长', step: 50, min: 1, max: 500 }
    ]

const FONT_FIELDS: { key: keyof ChartConfig; label: string }[] = [
    { key: 'titleFontSize', label: '标题' },
    { key: 'labelFontSize', label: '标签' },
    { key: 'tickFontSize', label: '坐标轴' },
    { key: 'textFontSize', label: '标注' }
]

const PASTE_COLUMNS: DataTableColumns<TableRow> = [
    { key: 'index', title: '#', width: 56, align: 'center', render: (_, index) => index + 1 },
    { key: 'timeFront', title: '持续时间 [h]', align: 'right' },
    { key: 'pmaxFront', title: 'Pmax-前', align: 'right' },
    { key: 'timeRear', title: '持续时间 [h]', align: 'right' },
    { key: 'pmaxRear', title: 'Pmax-后', align: 'right' }
]

const message = useMessage()
const isMac = window.electron.process.platform === 'darwin'

// ========== 参数配置 ==========
const binConfig = reactive<{ front: BinRange; rear: BinRange }>({
    front: { min: 800, max: 1700, step: 100 },
    rear: { min: 400, max: 1200, step: 50 }
})

const chartConfig = reactive<ChartConfig>({
    titleFontSize: 25,
    labelFontSize: 20,
    tickFontSize: 20,
    textFontSize: 25,
    width: 20,
    height: 15
})

const language = ref<Language>(Language.ZH)

const handleLanguageChange = (value: string | number): void => {
    language.value = LANGUAGE_OPTIONS.find((lang) => lang === value) ?? Language.ZH
}

// ========== 表格数据 ==========
const tableData = ref<TableRow[]>([])
const analyzeResult = ref<AnalyzeResponse | null>(null)

const formatRange = (min: number, max: number): string => `${min.toFixed(2)} – ${max.toFixed(2)}`

const stats = computed(() => {
    if (!analyzeResult.value) return []
    const f = analyzeResult.value.front.stats
    const r = analyzeResult.value.rear.stats
    return [
        { label: '持续时间 · 前轴承 (h)', value: formatRange(f.timeMin, f.timeMax) },
        { label: 'Pmax · 前轴承 (MPa)', value: formatRange(f.pmaxMin, f.pmaxMax) },
        { label: 'Pmax · 后轴承 (MPa)', value: formatRange(r.pmaxMin, r.pmaxMax) }
    ]
})

// ========== 图表 ==========
const chartPaths = reactive({ front: '', rear: '' })
const imgCacheBuster = ref(Date.now())

const hasCharts = computed(() => !!(chartPaths.front || chartPaths.rear))

const charts = computed(() =>
    [
        { key: 'front', label: '前轴承', path: chartPaths.front },
        { key: 'rear', label: '后轴承', path: chartPaths.rear }
    ].filter((chart) => chart.path)
)

const toLocalFileUrl = (filePath: string, cacheBuster?: number): string => {
    const base = convertFileSrc(filePath)
    return cacheBuster != null ? `${base}?t=${cacheBuster}` : base
}

const handleDragStart = (event: DragEvent, filePath: string): void => {
    event.preventDefault()
    window.electronAPI.startDrag(filePath)
}

// ========== 粘贴数据 ==========
const pasteDialogVisible = ref(false)
const pasteAreaRef = ref<HTMLElement>()
const pendingData = ref<TableRow[]>([])

const openPasteDialog = (): void => {
    pendingData.value = []
    pasteDialogVisible.value = true
}

const focusPasteArea = (): void => {
    nextTick(() => pasteAreaRef.value?.focus())
}

const handlePaste = (event: ClipboardEvent): void => {
    const text = event.clipboardData?.getData('text/plain')
    if (!text) return
    event.preventDefault()

    const parsed: TableRow[] = []
    for (const row of text.trim().split('\n')) {
        const cols = row.split('\t')
        if (cols.length < 2) continue
        parsed.push({
            timeFront: cols[0]?.trim() ?? '',
            pmaxFront: cols[1]?.trim() ?? '',
            timeRear: cols[2]?.trim() ?? '',
            pmaxRear: cols[3]?.trim() ?? ''
        })
    }

    if (parsed.length === 0) {
        message.warning('未检测到有效数据')
        return
    }

    pendingData.value = parsed
}

const confirmPaste = (): void => {
    tableData.value = pendingData.value
    analyzeResult.value = null
    chartPaths.front = ''
    chartPaths.rear = ''
    message.success(`已导入 ${pendingData.value.length} 行数据`)
    pendingData.value = []
    pasteDialogVisible.value = false
}

const cancelPaste = (): void => {
    pendingData.value = []
    pasteDialogVisible.value = false
}

// ========== 生成图表 ==========
const generating = ref(false)

const generateCharts = async (): Promise<void> => {
    if (tableData.value.length === 0 || generating.value) return

    generating.value = true
    chartPaths.front = ''
    chartPaths.rear = ''
    analyzeResult.value = null
    try {
        const data = tableData.value.map((r) => [r.timeFront, r.pmaxFront, r.timeRear, r.pmaxRear])
        const res = await analyzePmax({
            data,
            binConfig: {
                front: { ...binConfig.front },
                rear: { ...binConfig.rear }
            },
            chartConfig: { ...chartConfig },
            language: language.value
        })
        analyzeResult.value = res
        chartPaths.front = res.front.chartPath
        chartPaths.rear = res.rear.chartPath
        imgCacheBuster.value = Date.now()
        message.success('图表生成完成')
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : '图表生成失败'
        message.error(msg, { duration: 5000 })
    } finally {
        generating.value = false
    }
}

// ========== 清空 ==========
const clearAll = (): void => {
    tableData.value = []
    analyzeResult.value = null
    chartPaths.front = ''
    chartPaths.rear = ''
}
</script>

<style scoped>
.bin-grid {
    display: grid;
    grid-template-columns: 52px minmax(0, 1fr) minmax(0, 1fr);
    align-items: center;
    gap: 8px;
}

.bin-head,
.sub-label {
    font-size: 12px;
    color: var(--text-3);
}

.sub-label {
    margin-bottom: -2px;
}

.font-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px 12px;
}

.font-field {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.font-label {
    flex-shrink: 0;
    width: 40px;
    color: var(--text-2);
}

.font-field > :last-child {
    flex: 1;
    min-width: 0;
}

/* ========== 结果区 ========== */
.chart-scroll {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    padding: 16px 20px 24px;
    overflow-y: auto;
}

.stat-bar {
    display: grid;
    flex-shrink: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    background: var(--subtle);
    border: 1px solid var(--divider);
    border-radius: 8px;
}

.stat {
    min-width: 0;
    padding: 9px 12px;
}

.stat + .stat {
    border-left: 1px solid var(--divider);
}

.stat-label,
.stat-value {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.stat-label {
    font-size: 12px;
    color: var(--text-3);
}

.stat-value {
    margin-top: 1px;
    font-weight: 600;
}

.figure-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
    gap: 16px;
}

.figure {
    margin: 0;
    overflow: hidden;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.figure-head {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 36px;
    padding: 0 10px 0 12px;
    font-size: 12.5px;
    font-weight: 600;
    border-bottom: 1px solid var(--divider);
}

.figure-hint {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: auto;
    font-size: 12px;
    font-weight: 400;
    color: var(--text-3);
}

.figure-paper {
    padding: 8px;
    background: var(--paper);
}

.figure-paper img {
    display: block;
    width: 100%;
    max-height: calc(100vh - 220px);
    object-fit: contain;
    cursor: grab;
}

/* ========== 粘贴弹窗 ========== */
.paste-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    min-height: 340px;
    padding: 24px;
    text-align: center;
    border: 1.5px dashed var(--border-strong);
    border-radius: 10px;
    outline: none;
    transition:
        border-color 0.15s,
        background 0.15s;
}

.paste-area:focus {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.paste-area.has-data {
    align-items: stretch;
    justify-content: flex-start;
    padding: 0;
    text-align: left;
    background: transparent;
    border-style: solid;
    border-color: var(--border);
}

.paste-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    margin-bottom: 10px;
    color: var(--accent);
    background: var(--panel);
    border-radius: 12px;
    box-shadow: var(--shadow-sm);
}

.paste-title {
    font-size: 14px;
    font-weight: 600;
}

.paste-desc {
    font-size: 12.5px;
    color: var(--text-3);
}

.paste-desc kbd {
    margin: 0 1px;
}

.paste-cols {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
    margin-top: 12px;
}

.paste-cols span {
    padding: 2px 8px;
    font-size: 12px;
    color: var(--text-2);
    background: var(--muted);
    border-radius: 5px;
}

.paste-info {
    padding: 10px 14px;
    font-size: 12.5px;
    color: var(--text-2);
    border-top: 1px solid var(--divider);
}

.paste-info b {
    color: var(--accent);
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
