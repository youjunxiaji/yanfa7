<template>
    <div class="preview-page">
        <div
            v-if="columns.length > 0"
            class="preview-wrapper"
        >
            <!-- 顶部控制栏 -->
            <div class="control-bar">
                <div class="control-left">
                    <span class="file-name-tag">{{ fileStem }}</span>
                </div>
                <div class="control-right">
                    <el-select
                        v-model="selectedCol"
                        style="width: 100px;"
                        size="small"
                    >
                        <el-option
                            v-for="col in columns"
                            :key="col"
                            :label="`第 ${col} 列`"
                            :value="col"
                        />
                    </el-select>
                    <div class="track-switch">
                        <button
                            class="track-btn"
                            :class="{ active: stressPosition === 'inner' }"
                            @click="stressPosition = 'inner'"
                        >内滚道</button>
                        <button
                            class="track-btn"
                            :class="{ active: stressPosition === 'outer' }"
                            @click="stressPosition = 'outer'"
                        >外滚道</button>
                    </div>
                    <el-divider direction="vertical" />
                    <div class="polar-settings">
                        <label class="polar-label">载荷最小值</label>
                        <el-input-number
                            v-model="loadPolarMin"
                            :step="0.5"
                            :min="-9999"
                            :max="0"
                            size="small"
                            controls-position="right"
                            style="width: 110px;"
                        />
                        <label class="polar-label">应力最小值</label>
                        <el-input-number
                            v-model="pressPolarMin"
                            :step="0.5"
                            :min="-9999"
                            :max="0"
                            size="small"
                            controls-position="right"
                            style="width: 110px;"
                        />
                    </div>
                </div>
            </div>

            <!-- 三栏内容 -->
            <el-splitter class="content-splitter">
                <!-- 左栏: Plotly 交互式图表 -->
                <el-splitter-panel
                    :size="40"
                    :min="20"
                >
                    <div class="panel-wrapper">
                        <div class="panel-title">交互式图表</div>
                        <div class="panel-body panel-scroll">
                            <template v-if="chartData.length > 0">
                                <div
                                    v-for="(chart, idx) in chartData"
                                    :key="idx"
                                    class="plotly-section"
                                >
                                    <div class="plotly-label">{{ chart.label }}</div>
                                    <div
                                        :ref="el => setPlotRef(el, idx)"
                                        class="plotly-container"
                                    />
                                </div>
                            </template>
                            <div
                                v-else-if="chartLoading"
                                class="panel-empty"
                            >
                                <el-icon
                                    :size="40"
                                    color="#409eff"
                                    class="is-loading"
                                >
                                    <Loading />
                                </el-icon>
                                <span>加载图表数据...</span>
                            </div>
                            <div
                                v-else
                                class="panel-empty"
                            >
                                <el-icon
                                    :size="40"
                                    color="#d2d2d7"
                                >
                                    <Document />
                                </el-icon>
                                <span>图表数据不存在</span>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>

                <!-- 中栏: 应力曲线图 -->
                <el-splitter-panel
                    :size="30"
                    :min="15"
                >
                    <div class="panel-wrapper">
                        <div class="panel-title">应力曲线图</div>
                        <div class="panel-body panel-scroll">
                            <div class="image-group">
                                <div class="image-label">中文</div>
                                <img
                                    v-if="stressChartCnPath"
                                    :src="`local-file://${stressChartCnPath}?t=${imgCacheBuster}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressChartCnPath)"
                                >
                                <div
                                    v-else
                                    class="image-placeholder"
                                >图片不存在</div>
                            </div>
                            <div class="image-group">
                                <div class="image-label">英文</div>
                                <img
                                    v-if="stressChartEnPath"
                                    :src="`local-file://${stressChartEnPath}?t=${imgCacheBuster}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressChartEnPath)"
                                >
                                <div
                                    v-else
                                    class="image-placeholder"
                                >图片不存在</div>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>

                <!-- 右栏: 雷达图 -->
                <el-splitter-panel
                    :size="30"
                    :min="15"
                >
                    <div class="panel-wrapper">
                        <div class="panel-title">雷达图</div>
                        <div class="panel-body panel-scroll">
                            <div class="image-group">
                                <div class="image-label">载荷分布</div>
                                <img
                                    v-if="loadPolarPath"
                                    :src="`local-file://${loadPolarPath}?t=${imgCacheBuster}`"
                                    class="chart-img"
                                    @click="openImagePreview(loadPolarPath)"
                                >
                                <div
                                    v-else
                                    class="image-placeholder"
                                >图片不存在</div>
                            </div>
                            <div class="image-group">
                                <div class="image-label">应力分布</div>
                                <img
                                    v-if="stressPolarPath"
                                    :src="`local-file://${stressPolarPath}?t=${imgCacheBuster}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressPolarPath)"
                                >
                                <div
                                    v-else
                                    class="image-placeholder"
                                >图片不存在</div>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>
            </el-splitter>
        </div>

        <!-- 无数据状态 -->
        <div
            v-else
            class="empty-state"
        >
            <el-icon
                :size="64"
                color="#d2d2d7"
            >
                <Document />
            </el-icon>
            <div class="empty-text">无预览数据</div>
        </div>

        <!-- 图片放大预览 -->
        <el-dialog
            v-model="imagePreviewVisible"
            width="80%"
            :show-close="true"
            class="image-preview-dialog"
        >
            <img
                v-if="imagePreviewSrc"
                :src="`local-file://${imagePreviewSrc}`"
                class="preview-full-img"
            >
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { Document, Loading } from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'
import Plotly from 'plotly.js-dist-min'
import { usePlotlyDrag, DRAG_ICON_SVG, type DragEndInfo } from '@renderer/composables/usePlotlyDrag'

declare global {
    interface Window {
        previewAPI: {
            getSearchParams: () => Record<string, string>
        }
    }
}

interface ChartItem {
    label: string
    traces: Plotly.Data[]
    layout: Record<string, unknown>
}

const params = window.previewAPI.getSearchParams()

const fileStem = params.fileStem ?? ''
const outputDir = (params.outputDir ?? '').replace(/\\/g, '/')
const columns = (params.columns ?? '').split(',').filter(Boolean).map(Number)

const selectedCol = ref(columns[0] ?? 1)
const stressPosition = ref<'inner' | 'outer'>('inner')
const loadPolarMin = ref(0)
const pressPolarMin = ref(0)

function getGroupName(stem: string): string {
    const idx = stem.indexOf('(')
    return idx > 0 ? stem.substring(0, idx).trimEnd() : stem
}

const basePath = computed(() => {
    if (!outputDir || !fileStem) return ''
    const group = getGroupName(fileStem)
    return `${outputDir}/res-output/${group}`
})

const positionLabel = computed(() =>
    stressPosition.value === 'inner' ? '内滚道接触应力' : '外滚道接触应力'
)

const chartApiUrl = computed(() => {
    if (!fileStem || columns.length === 0) return ''
    const pos = stressPosition.value === 'inner' ? 'inner' : 'outer'
    const params = new URLSearchParams({
        file_stem: fileStem,
        col_index: String(selectedCol.value),
        position: pos,
    })
    return `http://localhost:8000/api/chart-data?${params}`
})

const stressChartCnPath = computed(() => {
    if (!basePath.value || columns.length === 0) return ''
    return `${basePath.value}/${fileStem}-${positionLabel.value}-第${selectedCol.value}列-中.png`
})

const stressChartEnPath = computed(() => {
    if (!basePath.value || columns.length === 0) return ''
    return `${basePath.value}/${fileStem}-${positionLabel.value}-第${selectedCol.value}列-英.png`
})

const loadPolarPath = computed(() => {
    if (!basePath.value || columns.length === 0) return ''
    return `${basePath.value}/${fileStem}-第${selectedCol.value}列-载荷雷达图.png`
})

const stressPolarPath = computed(() => {
    if (!basePath.value || columns.length === 0) return ''
    return `${basePath.value}/${fileStem}-第${selectedCol.value}列-应力雷达图.png`
})

const imgCacheBuster = ref(Date.now())

const imagePreviewVisible = ref(false)
const imagePreviewSrc = ref('')

const openImagePreview = (path: string) => {
    imagePreviewSrc.value = path
    imagePreviewVisible.value = true
}

// ========== Plotly 图表渲染 ==========

const chartData = ref<ChartItem[]>([])
const chartLoading = ref(false)
const plotRefs: (HTMLElement | null)[] = []

const setPlotRef = (el: unknown, idx: number) => {
    plotRefs[idx] = el as HTMLElement | null
}

const loadChartData = async (url: string) => {
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
            } catch { /* ignore parse error */ }
            ElNotification({ title: '错误', message: msg, type: 'error', duration: 5000 })
            chartData.value = []
            return
        }
        chartData.value = await resp.json()
    } catch {
        ElNotification({ title: '错误', message: '无法连接后端服务', type: 'error', duration: 5000 })
        chartData.value = []
    } finally {
        chartLoading.value = false
    }
}

// ========== 拖拽模式（composable）==========

const handleDragEnd = async (info: DragEndInfo) => {
    const payload = {
        file_stem: fileStem,
        col_index: selectedCol.value,
        position: stressPosition.value,
        trace_index: info.curveNumber,
        point_index: info.pointNumber,
        new_value: info.newY,
    }
    console.log('[DragEnd] syncing to backend:', payload)
    try {
        const resp = await fetch('http://localhost:8000/api/update-stress-point', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        if (!resp.ok) {
            const body = await resp.json().catch(() => ({}))
            console.error('[DragEnd] backend error:', body.detail || resp.statusText)
            ElNotification({ title: '同步失败', message: body.detail || '更新应力点失败', type: 'error', duration: 3000 })
            return
        }
        console.log('[DragEnd] synced successfully')
        imgCacheBuster.value = Date.now()
    } catch (e) {
        console.error('[DragEnd] network error:', e)
        ElNotification({ title: '同步失败', message: '无法连接后端服务', type: 'error', duration: 3000 })
    }
}

const { toggleDragMode, setupDragListeners, reset: resetDrag } = usePlotlyDrag(handleDragEnd)

// ========== 渲染 ==========

const renderPlots = async () => {
    resetDrag()

    await nextTick()
    for (let i = 0; i < chartData.value.length; i++) {
        const el = plotRefs[i]
        if (!el) continue
        const chart = chartData.value[i]
        const isDraggable = chart.label === '去峰后数据'
        const layout: Partial<Plotly.Layout> = {
            xaxis: { title: chart.layout.xaxis_title as string },
            yaxis: { title: chart.layout.yaxis_title as string },
            height: (chart.layout.height as number) || 500,
            margin: { l: 60, r: 20, t: 30, b: 50 },
            showlegend: true,
            legend: { orientation: 'v', x: 1.02, y: 0.5 },
        }

        const config: Partial<Plotly.Config> = {
            responsive: true,
            modeBarButtonsToRemove: ['zoom2d', 'zoomIn2d', 'zoomOut2d', 'select2d', 'lasso2d'],
        }

        if (isDraggable) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (config as any).modeBarButtonsToAdd = [{
                name: '拖拽编辑',
                title: '拖拽编辑',
                icon: DRAG_ICON_SVG,
                click: () => toggleDragMode(el),
            }]
        }

        await Plotly.newPlot(el, chart.traces, layout, config)

        if (isDraggable) {
            setupDragListeners(el)
        }
    }
}

watch(chartApiUrl, (url) => loadChartData(url), { immediate: true })
watch(chartData, () => renderPlots())

// ========== 雷达图最小值 → 重新生成 ==========

let polarDebounceTimer: ReturnType<typeof setTimeout> | null = null

const regeneratePolar = async () => {
    const payload = {
        file_stem: fileStem,
        col_index: selectedCol.value,
        load_polar_min: loadPolarMin.value,
        press_polar_min: pressPolarMin.value,
    }
    try {
        const resp = await fetch('http://localhost:8000/api/regenerate-polar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        if (!resp.ok) {
            const body = await resp.json().catch(() => ({}))
            ElNotification({ title: '雷达图生成失败', message: body.detail || '重新生成雷达图失败', type: 'error', duration: 3000 })
            return
        }
        imgCacheBuster.value = Date.now()
    } catch {
        ElNotification({ title: '雷达图生成失败', message: '无法连接后端服务', type: 'error', duration: 3000 })
    }
}

watch([loadPolarMin, pressPolarMin], () => {
    if (polarDebounceTimer) clearTimeout(polarDebounceTimer)
    polarDebounceTimer = setTimeout(regeneratePolar, 600)
})
</script>

<style scoped>
.preview-page {
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 12px 16px 16px;
    background-color: #f5f5f7;
}

.preview-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}

/* ========== 控制栏 ========== */
.control-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px 8px 16px;
    margin-bottom: 12px;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04);
    flex-shrink: 0;
}

.control-left {
    display: flex;
    align-items: center;
    min-width: 0;
}

.file-name-tag {
    font-size: 13px;
    font-weight: 600;
    color: #1d1d1f;
    max-width: 480px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.control-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}

.track-switch {
    display: flex;
    background: #f2f2f7;
    border-radius: 6px;
    padding: 2px;
    height: 24px;
    align-items: center;
}

.track-btn {
    padding: 2px 14px;
    border: none;
    background: transparent;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    color: #86868b;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    line-height: 1;
    height: 20px;
}

.track-btn.active {
    background: #fff;
    color: #1d1d1f;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.polar-settings {
    display: flex;
    align-items: center;
    gap: 6px;
}

.polar-label {
    font-size: 12px;
    color: #86868b;
    white-space: nowrap;
}

/* ========== 三栏布局 ========== */
.content-splitter {
    flex: 1;
    min-height: 0;
}

.panel-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0 8px;
}

.panel-title {
    font-size: 13px;
    font-weight: 600;
    color: #86868b;
    padding-bottom: 8px;
    border-bottom: 1px solid #f2f2f7;
    margin-bottom: 8px;
    flex-shrink: 0;
}

.panel-body {
    flex: 1;
    min-height: 0;
}

.panel-scroll {
    overflow-y: auto;
}

.panel-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 12px;
    color: #86868b;
    font-size: 13px;
}

/* ========== Plotly 图表 ========== */
.plotly-section {
    margin-bottom: 20px;
}

.plotly-label {
    font-size: 12px;
    color: #86868b;
    font-weight: 500;
    margin-bottom: 6px;
}

.plotly-container {
    width: 100%;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    overflow: hidden;
}

.plotly-container :deep(.nsewdrag) {
    cursor: crosshair;
}

/* ========== 图片 ========== */
.image-group {
    margin-bottom: 16px;
}

.image-label {
    font-size: 12px;
    color: #86868b;
    font-weight: 500;
    margin-bottom: 6px;
}

.chart-img {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #e5e5ea;
    cursor: pointer;
    transition: box-shadow 0.2s ease;
}

.chart-img:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 120px;
    border: 2px dashed #e5e5ea;
    border-radius: 8px;
    color: #86868b;
    font-size: 13px;
}

/* ========== 空状态 ========== */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: 16px;
}

.empty-text {
    font-size: 14px;
    color: #86868b;
}

/* ========== 图片预览弹窗 ========== */
.image-preview-dialog :deep(.el-dialog__body) {
    padding: 0;
    display: flex;
    justify-content: center;
}

.preview-full-img {
    max-width: 100%;
    max-height: 85vh;
    object-fit: contain;
}
</style>
