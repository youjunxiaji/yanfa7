<template>
    <div class="preview-page">
        <template v-if="columns.length > 0">
            <header class="pv-toolbar">
                <div class="pv-file">
                    <FileText :size="16" />
                    <span class="pv-file-name" :title="fileStem">{{ fileStem }}</span>
                </div>
                <div class="pv-controls">
                    <n-tabs
                        :value="selectedCol"
                        type="segment"
                        size="small"
                        :animated="false"
                        class="pv-col-tabs"
                        :style="{ '--col-count': columns.length }"
                        @update:value="handleColumnChange"
                    >
                        <n-tab v-for="col in columns" :key="col" :name="col">第 {{ col }} 列</n-tab>
                    </n-tabs>
                    <n-tabs
                        :value="stressPosition"
                        type="segment"
                        size="small"
                        :animated="false"
                        class="pv-track"
                        @update:value="handlePositionChange"
                    >
                        <n-tab name="inner">内滚道</n-tab>
                        <n-tab name="outer">外滚道</n-tab>
                    </n-tabs>
                </div>
            </header>

            <div class="pv-body">
                <n-split
                    direction="horizontal"
                    :default-size="0.42"
                    :min="0.25"
                    :max="0.7"
                    :resize-trigger-size="10"
                    @drag-end="resizePlots"
                >
                    <template #1>
                        <div class="pv-cell">
                            <section class="pv-pane">
                                <header class="pv-pane-head">
                                    <span class="pv-pane-title">交互图表</span>
                                    <div class="pv-pane-extra">
                                        <n-button
                                            size="small"
                                            :type="dragModeEnabled ? 'primary' : 'default'"
                                            :secondary="dragModeEnabled"
                                            :disabled="draggableIndex < 0"
                                            @click="toggleDrag"
                                        >
                                            <template #icon><MoveVertical :size="15" /></template>
                                            {{ dragModeEnabled ? '退出拖拽编辑' : '拖拽编辑' }}
                                        </n-button>
                                    </div>
                                </header>
                                <div class="pv-pane-body">
                                    <div v-if="dragModeEnabled" class="drag-banner">
                                        <Info :size="14" />
                                        拖动「去峰后数据」上的点修改应力值，松手后自动同步并重画报告图片
                                    </div>
                                    <template v-if="chartData.length > 0">
                                        <div v-for="(chart, idx) in chartData" :key="idx">
                                            <div class="pv-caption">
                                                {{ chart.label }}
                                                <span
                                                    v-if="dragModeEnabled && idx === draggableIndex"
                                                    class="caption-tag"
                                                >
                                                    可拖拽
                                                </span>
                                            </div>
                                            <div
                                                :ref="(el) => setPlotRef(el, idx)"
                                                class="plotly-container"
                                            />
                                        </div>
                                    </template>
                                    <EmptyState
                                        v-else-if="chartLoading"
                                        busy
                                        title="加载图表数据…"
                                    />
                                    <EmptyState
                                        v-else
                                        :icon="FileText"
                                        title="图表数据不存在"
                                        :clickable="false"
                                    />
                                </div>
                            </section>
                        </div>
                    </template>
                    <template #2>
                        <n-split
                            direction="horizontal"
                            :default-size="0.5"
                            :min="0.3"
                            :max="0.7"
                            :resize-trigger-size="10"
                        >
                            <template #1>
                                <div class="pv-cell">
                                    <section class="pv-pane">
                                        <header class="pv-pane-head">
                                            <span class="pv-pane-title">应力曲线</span>
                                        </header>
                                        <div class="pv-pane-body">
                                            <div v-for="img in stressImages" :key="img.key">
                                                <div class="pv-caption">
                                                    {{ img.caption }}
                                                    <span v-if="img.path" class="drag-hint">
                                                        <GripVertical :size="13" />
                                                        拖到 Word
                                                    </span>
                                                </div>
                                                <div
                                                    v-if="img.path"
                                                    class="pv-image"
                                                    :class="{ 'is-static': !img.zoomable }"
                                                    @click="openImagePreview(img)"
                                                >
                                                    <img
                                                        :src="
                                                            localFileUrl(img.path, imgCacheBuster)
                                                        "
                                                        :alt="img.caption"
                                                        draggable="true"
                                                        @dragstart="
                                                            handleDragStart($event, img.path)
                                                        "
                                                    />
                                                </div>
                                                <div v-else class="pv-missing">图片不存在</div>
                                            </div>
                                        </div>
                                    </section>
                                </div>
                            </template>
                            <template #2>
                                <div class="pv-cell">
                                    <section class="pv-pane">
                                        <header class="pv-pane-head">
                                            <span class="pv-pane-title">雷达图</span>
                                            <div class="pv-pane-extra">
                                                <n-tooltip placement="bottom" :delay="300">
                                                    <template #trigger>
                                                        <NumberInput
                                                            v-model="loadPolarMin"
                                                            :step="0.5"
                                                            :min="-9999"
                                                            :max="0"
                                                            size="small"
                                                            prefix="载荷"
                                                            class="polar-input"
                                                        />
                                                    </template>
                                                    载荷雷达图的径向最小值，0 表示自动
                                                </n-tooltip>
                                                <n-tooltip placement="bottom" :delay="300">
                                                    <template #trigger>
                                                        <NumberInput
                                                            v-model="pressPolarMin"
                                                            :step="0.5"
                                                            :min="-9999"
                                                            :max="0"
                                                            size="small"
                                                            prefix="应力"
                                                            class="polar-input"
                                                        />
                                                    </template>
                                                    应力雷达图的径向最小值，0 表示自动
                                                </n-tooltip>
                                            </div>
                                        </header>
                                        <div class="pv-pane-body">
                                            <div v-for="img in polarImages" :key="img.key">
                                                <div class="pv-caption">
                                                    {{ img.caption }}
                                                    <span v-if="img.path" class="drag-hint">
                                                        <GripVertical :size="13" />
                                                        拖到 Word
                                                    </span>
                                                </div>
                                                <div
                                                    v-if="img.path"
                                                    class="pv-image"
                                                    @click="openImagePreview(img)"
                                                >
                                                    <img
                                                        :src="
                                                            localFileUrl(img.path, imgCacheBuster)
                                                        "
                                                        :alt="img.caption"
                                                        draggable="true"
                                                        @dragstart="
                                                            handleDragStart($event, img.path)
                                                        "
                                                    />
                                                </div>
                                                <div v-else class="pv-missing">图片不存在</div>
                                            </div>
                                        </div>
                                    </section>
                                </div>
                            </template>
                        </n-split>
                    </template>
                </n-split>
            </div>
        </template>

        <EmptyState v-else :icon="FileText" title="无预览数据" :clickable="false" />

        <n-modal
            v-model:show="imagePreviewVisible"
            preset="card"
            :title="imagePreviewTitle"
            :style="{ width: '80%', maxWidth: '1200px' }"
            :bordered="false"
        >
            <template #header-extra>
                <span class="drag-hint">
                    <GripVertical :size="13" />
                    拖到 Word
                </span>
            </template>
            <div class="zoom-paper">
                <img
                    v-if="imagePreviewSrc"
                    :src="localFileUrl(imagePreviewSrc, imgCacheBuster)"
                    :alt="imagePreviewTitle"
                    draggable="true"
                    @dragstart="handleDragStart($event, imagePreviewSrc)"
                />
            </div>
        </n-modal>
    </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { NButton, NModal, NSplit, NTab, NTabs, NTooltip, useMessage } from 'naive-ui'
import { FileText, GripVertical, Info, MoveVertical } from '@lucide/vue'
import Plotly from 'plotly.js-dist-min'
import { convertFileSrc } from '@tauri-apps/api/core'
import { usePlotlyDrag, type DragEndInfo } from '@renderer/composables/usePlotlyDrag'
import { useDarkClass } from '@renderer/composables/useDarkClass'
import { API_BASE } from '@renderer/api/backend'
import EmptyState from '@renderer/components/EmptyState.vue'
import NumberInput from '@renderer/components/NumberInput.vue'

declare global {
    interface Window {
        previewAPI: {
            getSearchParams: () => Record<string, string>
        }
    }
}

type StressPosition = 'inner' | 'outer'

interface ChartItem {
    label: string
    traces: Plotly.Data[]
    layout: Record<string, unknown>
}

interface ImageItem {
    key: string
    caption: string
    title: string
    path: string
    zoomable: boolean
}

const DRAGGABLE_LABEL = '去峰后数据'

const message = useMessage()
const isDark = useDarkClass()

const params = window.previewAPI.getSearchParams()

const fileStem = params.fileStem ?? ''
const outputDir = (params.outputDir ?? '').replace(/\\/g, '/')
const columns = (params.columns ?? '').split(',').filter(Boolean).map(Number)

const selectedCol = ref(columns[0] ?? 1)
const stressPosition = ref<StressPosition>('inner')
const loadPolarMin = ref(0)
const pressPolarMin = ref(0)

const handleColumnChange = (value: string | number): void => {
    selectedCol.value = Number(value)
}

const handlePositionChange = (value: string | number): void => {
    stressPosition.value = value === 'outer' ? 'outer' : 'inner'
}

const localFileUrl = (filePath: string, cacheBuster?: number): string => {
    const base = convertFileSrc(filePath)
    return cacheBuster != null ? `${base}?t=${cacheBuster}` : base
}

// ========== 报告图片路径 ==========
const getGroupName = (stem: string): string => {
    const idx = stem.indexOf('(')
    return idx > 0 ? stem.substring(0, idx).trimEnd() : stem
}

const basePath = computed(() => {
    if (!outputDir || !fileStem) return ''
    return `${outputDir}/res-output/${getGroupName(fileStem)}`
})

const positionLabel = computed(() =>
    stressPosition.value === 'inner' ? '内滚道接触应力' : '外滚道接触应力'
)

const imagePath = (suffix: string): string => {
    if (!basePath.value || columns.length === 0) return ''
    return `${basePath.value}/${fileStem}-${suffix}`
}

const stressImages = computed<ImageItem[]>(() => {
    const prefix = `${positionLabel.value}-第${selectedCol.value}列`
    return [
        {
            key: 'cn',
            caption: '中文',
            title: '应力曲线 · 中文',
            zoomable: true,
            path: imagePath(`${prefix}-中.png`)
        },
        {
            key: 'en',
            caption: '英文',
            title: '应力曲线 · 英文',
            zoomable: true,
            path: imagePath(`${prefix}-英.png`)
        },
        {
            key: 'contour',
            caption: '等高线图',
            title: '等高线图',
            zoomable: false,
            path: imagePath(`${prefix}-contour.png`)
        }
    ]
})

const polarImages = computed<ImageItem[]>(() => [
    {
        key: 'load',
        caption: '载荷分布',
        title: '载荷雷达图',
        zoomable: true,
        path: imagePath(`第${selectedCol.value}列-载荷雷达图.png`)
    },
    {
        key: 'press',
        caption: '应力分布',
        title: '应力雷达图',
        zoomable: true,
        path: imagePath(`第${selectedCol.value}列-应力雷达图.png`)
    }
])

const imgCacheBuster = ref(Date.now())

const imagePreviewVisible = ref(false)
const imagePreviewSrc = ref('')
const imagePreviewTitle = ref('')

const openImagePreview = (img: ImageItem): void => {
    if (!img.zoomable) return
    imagePreviewSrc.value = img.path
    imagePreviewTitle.value = img.title
    imagePreviewVisible.value = true
}

// webview 自己拖 <img> 只带 asset 链接，Word、PPT、Excel 读不到，改走原生文件拖拽
const handleDragStart = (event: DragEvent, filePath: string): void => {
    event.preventDefault()
    window.electronAPI.startDrag(filePath)
}

// ========== Plotly 交互图表 ==========
const chartApiUrl = computed(() => {
    if (!fileStem || columns.length === 0) return ''
    const query = new URLSearchParams({
        file_stem: fileStem,
        col_index: String(selectedCol.value),
        position: stressPosition.value
    })
    return `${API_BASE}/api/chart-data?${query}`
})

const chartData = ref<ChartItem[]>([])
const chartLoading = ref(false)
const plotRefs: (HTMLElement | null)[] = []

const setPlotRef = (el: unknown, idx: number): void => {
    plotRefs[idx] = el as HTMLElement | null
}

const draggableIndex = computed(() => chartData.value.findIndex((c) => c.label === DRAGGABLE_LABEL))

const loadChartData = async (url: string): Promise<void> => {
    if (!url) {
        chartData.value = []
        return
    }
    chartLoading.value = true
    try {
        const resp = await fetch(url)
        if (!resp.ok) {
            let msg = '获取图表数据失败'
            try {
                const body = await resp.json()
                if (body.detail) msg = body.detail
            } catch {
                /* ignore parse error */
            }
            message.error(msg, { duration: 5000 })
            chartData.value = []
            return
        }
        chartData.value = await resp.json()
    } catch {
        message.error('无法连接后端服务', { duration: 5000 })
        chartData.value = []
    } finally {
        chartLoading.value = false
    }
}

// Plotly 的配色从设计变量读，跟着亮暗主题走（UI Skill 界面标准第九节）
const cssVar = (name: string): string =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim()

const themeLayout = (): Record<string, unknown> => {
    const tick = cssVar('--text-3')
    const line = cssVar('--border-strong')
    const axis = {
        gridcolor: cssVar('--divider'),
        linecolor: line,
        zerolinecolor: line,
        tickfont: { color: tick }
    }
    return {
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        plot_bgcolor: 'rgba(0, 0, 0, 0)',
        font: { family: cssVar('--font-sans'), color: cssVar('--text-2'), size: 12 },
        xaxis: axis,
        yaxis: axis,
        legend: { font: { color: cssVar('--text-2') } },
        modebar: { bgcolor: 'rgba(0, 0, 0, 0)', color: tick, activecolor: cssVar('--accent') }
    }
}

const handleDragEnd = async (info: DragEndInfo): Promise<void> => {
    const payload = {
        file_stem: fileStem,
        col_index: selectedCol.value,
        position: stressPosition.value,
        trace_index: info.curveNumber,
        point_index: info.pointNumber,
        new_value: info.newY
    }
    try {
        const resp = await fetch(`${API_BASE}/api/update-stress-point`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        if (!resp.ok) {
            const body = await resp.json().catch(() => ({}))
            console.error('[DragEnd] backend error:', body.detail || resp.statusText)
            message.error(`同步失败：${body.detail || '更新应力点失败'}`, { duration: 5000 })
            return
        }
        imgCacheBuster.value = Date.now()
    } catch (e) {
        console.error('[DragEnd] network error:', e)
        message.error('同步失败：无法连接后端服务', { duration: 5000 })
    }
}

const {
    dragModeEnabled,
    toggleDragMode,
    setupDragListeners,
    reset: resetDrag
} = usePlotlyDrag(handleDragEnd)

const toggleDrag = (): void => {
    const el = plotRefs[draggableIndex.value]
    if (el) toggleDragMode(el)
}

const renderPlots = async (): Promise<void> => {
    resetDrag()

    await nextTick()
    const theme = themeLayout()
    for (let i = 0; i < chartData.value.length; i++) {
        const el = plotRefs[i]
        const chart = chartData.value[i]
        if (!el || !chart) continue
        const layout = {
            ...theme,
            xaxis: { ...(theme.xaxis as object), title: chart.layout.xaxis_title as string },
            yaxis: { ...(theme.yaxis as object), title: chart.layout.yaxis_title as string },
            height: (chart.layout.height as number) || 500,
            margin: { l: 60, r: 20, t: 30, b: 50 },
            showlegend: true,
            legend: { ...(theme.legend as object), orientation: 'v', x: 1.02, y: 0.5 }
        }
        const config = {
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['zoomIn2d', 'zoomOut2d', 'select2d', 'lasso2d']
        }

        await Plotly.newPlot(el, chart.traces, layout, config)

        if (i === draggableIndex.value) {
            setupDragListeners(el)
        }
    }
}

const resizePlots = (): void => {
    for (const el of plotRefs) {
        if (el) Plotly.Plots.resize(el)
    }
}

watch(chartApiUrl, (url) => loadChartData(url), { immediate: true })
watch(chartData, () => renderPlots())
watch(isDark, () => renderPlots())

// ========== 雷达图最小值 → 重新生成 ==========
let polarDebounceTimer: ReturnType<typeof setTimeout> | null = null

const regeneratePolar = async (): Promise<void> => {
    const payload = {
        file_stem: fileStem,
        col_index: selectedCol.value,
        load_polar_min: loadPolarMin.value,
        press_polar_min: pressPolarMin.value
    }
    try {
        const resp = await fetch(`${API_BASE}/api/regenerate-polar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        if (!resp.ok) {
            const body = await resp.json().catch(() => ({}))
            message.error(`雷达图生成失败：${body.detail || '重新生成雷达图失败'}`, {
                duration: 5000
            })
            return
        }
        imgCacheBuster.value = Date.now()
    } catch {
        message.error('雷达图生成失败：无法连接后端服务', { duration: 5000 })
    }
}

watch([loadPolarMin, pressPolarMin], () => {
    if (polarDebounceTimer) clearTimeout(polarDebounceTimer)
    polarDebounceTimer = setTimeout(regeneratePolar, 600)
})

onBeforeUnmount(() => {
    if (polarDebounceTimer) clearTimeout(polarDebounceTimer)
    for (const el of plotRefs) {
        if (el) Plotly.purge(el)
    }
})
</script>

<style scoped>
.preview-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--canvas);
}

/* ========== 工具栏 ========== */
.pv-toolbar {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 12px;
    height: 48px;
    padding: 0 12px 0 16px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
}

.pv-file {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 8px;
    min-width: 0;
    color: var(--text-3);
}

.pv-file-name {
    overflow: hidden;
    font-weight: 600;
    color: var(--text-1);
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 列号、内外滚道两个分段控件每段一样宽：列号有几列就几段（--col-count 在模板里按列数设），滚道固定两段 */
.pv-controls {
    --seg-width: 84px;

    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 12px;
}

.pv-col-tabs {
    width: calc(var(--col-count) * var(--seg-width));
}

.pv-track {
    width: calc(2 * var(--seg-width));
}

/* ========== 三栏 ========== */
.pv-body {
    flex: 1;
    min-height: 0;
    padding: 10px 5px;
}

.pv-cell {
    height: 100%;
    padding: 0 5px;
}

.pv-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.pv-pane-head {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 8px;
    height: 42px;
    padding: 0 8px 0 14px;
    border-bottom: 1px solid var(--divider);
}

.pv-pane-title {
    flex-shrink: 0;
    font-weight: 600;
}

.pv-pane-extra {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    margin-left: auto;
}

.polar-input {
    width: 92px;
}

.pv-pane-body {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    padding: 12px;
    overflow-y: auto;
}

.pv-caption {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
    font-size: 12px;
    color: var(--text-3);
}

.drag-hint {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: auto;
    font-size: 12px;
    color: var(--text-3);
}

.caption-tag {
    padding: 0 6px;
    font-size: 11px;
    line-height: 17px;
    color: var(--accent);
    background: var(--accent-soft);
    border-radius: 4px;
}

.drag-banner {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 6px;
    padding: 7px 10px;
    font-size: 12px;
    color: var(--accent);
    background: var(--accent-soft);
    border-radius: 7px;
}

.plotly-container {
    width: 100%;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 8px;
}

.plotly-container :deep(.nsewdrag) {
    cursor: crosshair;
}

/* ========== 报告图片 ========== */
.pv-image {
    overflow: hidden;
    background: var(--paper);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: zoom-in;
    transition:
        border-color 0.15s,
        box-shadow 0.15s;
}

.pv-image:hover {
    border-color: var(--border-strong);
    box-shadow: var(--shadow-md);
}

.pv-image.is-static {
    cursor: grab;
}

.pv-image.is-static:hover {
    border-color: var(--border);
    box-shadow: none;
}

.pv-image img {
    display: block;
    width: 100%;
}

.pv-missing {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 120px;
    font-size: 12.5px;
    color: var(--text-3);
    border: 1.5px dashed var(--border-strong);
    border-radius: 8px;
}

.zoom-paper {
    overflow: hidden;
    background: var(--paper);
    border-radius: 8px;
}

.zoom-paper img {
    display: block;
    max-width: 100%;
    max-height: 80vh;
    margin: 0 auto;
    object-fit: contain;
    cursor: grab;
}
</style>
