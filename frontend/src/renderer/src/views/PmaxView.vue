<template>
    <div class="pmax-page">
        <el-row :gutter="20" class="page-row">
            <!-- 左侧参数面板 -->
            <el-col :span="10" class="left-col">
                <el-card class="page-card" shadow="never">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon :size="18" class="header-icon">
                                    <Setting />
                                </el-icon>
                                <span class="card-title">参数配置</span>
                            </div>
                        </div>
                    </template>

                    <div class="config-form">
                        <!-- 分箱参数 -->
                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <Histogram />
                                </el-icon>
                                <span>分箱参数</span>
                            </div>
                            <div class="bin-grid">
                                <div class="bin-grid-head">
                                    <span></span>
                                    <span class="bin-col-title">前轴承</span>
                                    <span class="bin-col-title">后轴承</span>
                                </div>
                                <div class="bin-grid-row">
                                    <span class="bin-label">Min</span>
                                    <el-input-number
                                        v-model="binConfig.front.min"
                                        :step="50"
                                        :min="0"
                                        :max="100000"
                                        controls-position="right"
                                    />
                                    <el-input-number
                                        v-model="binConfig.rear.min"
                                        :step="50"
                                        :min="0"
                                        :max="100000"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="bin-grid-row">
                                    <span class="bin-label">Max</span>
                                    <el-input-number
                                        v-model="binConfig.front.max"
                                        :step="50"
                                        :min="0"
                                        :max="100000"
                                        controls-position="right"
                                    />
                                    <el-input-number
                                        v-model="binConfig.rear.max"
                                        :step="50"
                                        :min="0"
                                        :max="100000"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="bin-grid-row">
                                    <span class="bin-label">Step</span>
                                    <el-input-number
                                        v-model="binConfig.front.step"
                                        :step="50"
                                        :min="1"
                                        :max="500"
                                        controls-position="right"
                                    />
                                    <el-input-number
                                        v-model="binConfig.rear.step"
                                        :step="50"
                                        :min="1"
                                        :max="500"
                                        controls-position="right"
                                    />
                                </div>
                            </div>
                        </div>

                        <!-- 字体参数 -->
                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <EditPen />
                                </el-icon>
                                <span>字体参数</span>
                            </div>
                            <div class="num-grid">
                                <div class="form-row">
                                    <span class="form-label">标题</span>
                                    <el-input-number
                                        v-model="chartConfig.titleFontSize"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">标签</span>
                                    <el-input-number
                                        v-model="chartConfig.labelFontSize"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">坐标轴</span>
                                    <el-input-number
                                        v-model="chartConfig.tickFontSize"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">标注</span>
                                    <el-input-number
                                        v-model="chartConfig.textFontSize"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                    />
                                </div>
                            </div>
                        </div>

                        <!-- 图形比例 -->
                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <PictureFilled />
                                </el-icon>
                                <span>图形比例</span>
                            </div>
                            <div class="num-grid">
                                <div class="form-row">
                                    <span class="form-label">长</span>
                                    <el-input-number
                                        v-model="chartConfig.width"
                                        :min="1"
                                        :max="20"
                                        controls-position="right"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">宽</span>
                                    <el-input-number
                                        v-model="chartConfig.height"
                                        :min="1"
                                        :max="20"
                                        controls-position="right"
                                    />
                                </div>
                            </div>
                        </div>

                        <!-- 图表语言 -->
                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <Operation />
                                </el-icon>
                                <span>图表语言</span>
                            </div>
                            <el-segmented
                                v-model="language"
                                :options="LANGUAGE_OPTIONS"
                                class="lang-segmented"
                            />
                        </div>
                    </div>

                    <!-- 操作区 -->
                    <div class="action-bar">
                        <el-button
                            type="primary"
                            size="large"
                            class="btn-generate"
                            :class="{ 'btn-generate--inactive': tableData.length === 0 }"
                            :disabled="tableData.length === 0"
                            :loading="generating"
                            @click="generateCharts"
                        >
                            <el-icon v-if="!generating" class="btn-icon">
                                <TrendCharts />
                            </el-icon>
                            {{ generating ? '生成中…' : '生成图表' }}
                        </el-button>
                        <el-button
                            plain
                            class="btn-clear-full"
                            :disabled="tableData.length === 0"
                            @click="clearAll"
                        >
                            <el-icon class="btn-icon">
                                <Delete />
                            </el-icon>
                            清空数据
                        </el-button>
                    </div>
                </el-card>
            </el-col>

            <!-- 右侧图表展示区 -->
            <el-col :span="14" class="right-col">
                <el-card class="page-card" shadow="never">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon :size="18" class="header-icon">
                                    <PictureFilled />
                                </el-icon>
                                <span class="card-title">图表预览</span>
                            </div>
                            <el-button class="btn-paste" @click="pasteDialogVisible = true">
                                <el-icon class="btn-icon">
                                    <DocumentCopy />
                                </el-icon>
                                粘贴数据
                                <el-tag
                                    v-if="tableData.length > 0"
                                    type="primary"
                                    size="small"
                                    round
                                    class="row-tag"
                                >
                                    {{ tableData.length }} 行
                                </el-tag>
                            </el-button>
                        </div>
                    </template>

                    <div class="chart-display-area">
                        <!-- 有图表时 -->
                        <template v-if="chartPaths.front || chartPaths.rear">
                            <!-- 统计摘要 -->
                            <div v-if="analyzeResult" class="stats-section">
                                <div class="section-label">
                                    <el-icon :size="14">
                                        <DataAnalysis />
                                    </el-icon>
                                    <span>数据统计 · 共 {{ tableData.length }} 行</span>
                                </div>
                                <el-table :data="statsTableData" size="small" border class="stats-table">
                                    <el-table-column prop="metric" label="" width="60" />
                                    <el-table-column prop="timeFront" label="时间-前" align="center" />
                                    <el-table-column prop="pmaxFront" label="Pmax-前" align="center" />
                                    <el-table-column prop="pmaxRear" label="Pmax-后" align="center" />
                                </el-table>
                            </div>
                            <div class="chart-images">
                                <div v-if="chartPaths.front" class="chart-item">
                                    <span class="chart-label">前轴承</span>
                                    <img
                                        :src="toLocalFileUrl(chartPaths.front, imgCacheBuster)"
                                        alt="前轴承"
                                        class="chart-img"
                                        draggable="true"
                                        @dragstart="handleDragStart($event, chartPaths.front)"
                                    />
                                </div>
                                <div v-if="chartPaths.rear" class="chart-item">
                                    <span class="chart-label">后轴承</span>
                                    <img
                                        :src="toLocalFileUrl(chartPaths.rear, imgCacheBuster)"
                                        alt="后轴承"
                                        class="chart-img"
                                        draggable="true"
                                        @dragstart="handleDragStart($event, chartPaths.rear)"
                                    />
                                </div>
                            </div>
                        </template>

                        <!-- 已导入数据但未生成图表 -->
                        <div
                            v-else-if="tableData.length > 0"
                            class="empty-state"
                            @click="generateCharts"
                        >
                            <el-icon :size="48" class="empty-icon">
                                <TrendCharts />
                            </el-icon>
                            <div class="empty-title">已导入 {{ tableData.length }} 行数据</div>
                            <div class="empty-desc">点击此处或左侧「生成图表」查看结果</div>
                        </div>

                        <!-- 初始空状态 -->
                        <div
                            v-else
                            class="empty-state"
                            @click="pasteDialogVisible = true"
                        >
                            <el-icon :size="48" class="empty-icon">
                                <DocumentCopy />
                            </el-icon>
                            <div class="empty-title">暂无数据</div>
                            <div class="empty-desc">点击此处粘贴 Excel 数据，再生成图表</div>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 粘贴数据 Dialog -->
        <el-dialog
            v-model="pasteDialogVisible"
            title="粘贴数据"
            width="640px"
            :close-on-click-modal="false"
            @opened="onPasteDialogOpen"
        >
            <div
                ref="pasteAreaRef"
                class="paste-dialog-area"
                tabindex="0"
                @paste="handlePaste"
            >
                <template v-if="pendingData.length > 0">
                    <el-table
                        :data="pendingData"
                        border
                        size="small"
                        max-height="400"
                        class="paste-preview-table"
                    >
                        <el-table-column type="index" label="#" width="50" align="center" />
                        <el-table-column prop="timeFront" label="持续时间 [h]" align="center" />
                        <el-table-column prop="pmaxFront" label="Pmax-前" align="center" />
                        <el-table-column prop="timeRear" label="持续时间 [h]" align="center" />
                        <el-table-column prop="pmaxRear" label="Pmax-后" align="center" />
                    </el-table>
                    <div class="paste-info">
                        已解析 <strong>{{ pendingData.length }}</strong> 行数据，点击确认导入
                    </div>
                </template>
                <template v-else>
                    <el-icon :size="40" color="#c0c4cc"><DocumentCopy /></el-icon>
                    <p class="empty-title">从 Excel 粘贴数据</p>
                    <p class="empty-desc">
                        点击此区域后按
                        <kbd>{{ isMac ? '⌘' : 'Ctrl' }}</kbd><kbd>V</kbd>
                        粘贴，支持 4 列数据
                    </p>
                    <p class="empty-hint">
                        持续时间 [h] | Pmax (MPa)-前 | 持续时间 [h] | Pmax (MPa)-后
                    </p>
                </template>
            </div>
            <template #footer>
                <el-button @click="cancelPaste">取消</el-button>
                <el-button type="primary" :disabled="pendingData.length === 0" @click="confirmPaste">
                    确认导入（{{ pendingData.length }} 行）
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
    Setting,
    EditPen,
    PictureFilled,
    TrendCharts,
    Delete,
    DocumentCopy,
    Operation,
    Histogram,
    DataAnalysis
} from '@element-plus/icons-vue'
import { Language, LANGUAGE_OPTIONS } from '@renderer/constants/language'
import { analyzePmax, type AnalyzeResponse } from '@renderer/api/pmax'
import { convertFileSrc } from '@tauri-apps/api/core'

const isMac = window.electron.process.platform === 'darwin'

// ========== 参数配置 ==========
const binConfig = reactive({
    front: { min: 800, max: 1700, step: 100 },
    rear: { min: 400, max: 1200, step: 50 }
})

const chartConfig = reactive({
    titleFontSize: 25,
    labelFontSize: 20,
    tickFontSize: 20,
    textFontSize: 25,
    width: 20,
    height: 15
})

const language = ref<Language>(Language.ZH)

// ========== 表格数据 ==========
interface TableRow {
    timeFront: string
    pmaxFront: string
    timeRear: string
    pmaxRear: string
}

const tableData = ref<TableRow[]>([])

const analyzeResult = ref<AnalyzeResponse | null>(null)

const statsTableData = computed(() => {
    if (!analyzeResult.value) return []
    const f = analyzeResult.value.front.stats
    const r = analyzeResult.value.rear.stats
    return [
        {
            metric: 'Min',
            timeFront: f.timeMin.toFixed(2),
            pmaxFront: f.pmaxMin.toFixed(2),
            pmaxRear: r.pmaxMin.toFixed(2)
        },
        {
            metric: 'Max',
            timeFront: f.timeMax.toFixed(2),
            pmaxFront: f.pmaxMax.toFixed(2),
            pmaxRear: r.pmaxMax.toFixed(2)
        }
    ]
})

// ========== 图表 ==========
const chartPaths = reactive({ front: '', rear: '' })
const imgCacheBuster = ref(Date.now())

const toLocalFileUrl = (filePath: string, cacheBuster?: number): string => {
    const base = convertFileSrc(filePath)
    return cacheBuster != null ? `${base}?t=${cacheBuster}` : base
}

const handleDragStart = (event: DragEvent, filePath: string): void => {
    event.preventDefault()
    window.electronAPI.startDrag(filePath)
}

// ========== 粘贴数据 Dialog ==========
const pasteDialogVisible = ref(false)
const pasteAreaRef = ref<HTMLElement>()
const pendingData = ref<TableRow[]>([])

const handlePaste = (event: ClipboardEvent): void => {
    const text = event.clipboardData?.getData('text/plain')
    if (!text) return
    event.preventDefault()

    const rows = text.trim().split('\n')
    const parsed: TableRow[] = []

    for (const row of rows) {
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
        ElMessage.warning('未检测到有效数据')
        return
    }

    pendingData.value = parsed
}

const confirmPaste = (): void => {
    tableData.value = pendingData.value
    analyzeResult.value = null
    chartPaths.front = ''
    chartPaths.rear = ''
    ElMessage.success(`已导入 ${pendingData.value.length} 行数据`)
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
    if (tableData.value.length === 0) {
        ElMessage.warning('请先粘贴数据')
        return
    }

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
        ElMessage.success('图表生成完成')
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : '图表生成失败'
        ElMessage.error(msg)
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

// Dialog 打开时自动聚焦粘贴区域
const onPasteDialogOpen = (): void => {
    nextTick(() => pasteAreaRef.value?.focus())
}
</script>

<style scoped>
/* ========== 页面骨架（与边缘应力页一致） ========== */
.pmax-page {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

.page-row {
    flex: 1;
    min-height: 0;
    align-items: stretch;
}

.page-row :deep(.el-col) {
    display: flex;
    flex-direction: column;
}

.left-col,
.right-col {
    height: 100%;
}

/* 卡片外壳 / 卡片头 / 参数分区 / section-label 通用样式 → 见 main.css「工具页通用样式」段 */

/* ========== 分箱参数网格 ========== */
.bin-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.bin-grid-head,
.bin-grid-row {
    display: grid;
    grid-template-columns: 44px 1fr 1fr;
    gap: 8px;
    align-items: center;
}

.bin-col-title {
    font-size: 12px;
    font-weight: 600;
    color: #86868b;
    text-align: center;
}

.bin-label {
    font-size: 13px;
    font-weight: 500;
    color: #636366;
}

.bin-grid-row :deep(.el-input-number) {
    width: 100%;
}

/* ========== 数值网格（字体 / 图形比例） ========== */
.num-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 10px;
}

.num-grid .form-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.form-label {
    flex-shrink: 0;
    width: 42px;
    font-size: 13px;
    color: #424245;
}

.num-grid :deep(.el-input-number) {
    flex: 1;
    width: auto !important;
}

/* ========== 图表语言 ========== */
.lang-segmented {
    width: 100%;
}

.lang-segmented :deep(.el-segmented__item) {
    flex: 1;
}

/* ========== 操作区（基础样式见 main.css，此处仅排布两个按钮）========== */
.action-bar {
    display: flex;
    flex-direction: row;
    gap: 10px;
}

.btn-generate {
    flex: 2;
    height: 44px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 12px;
    cursor: pointer;
    background: linear-gradient(135deg, #0071e3 0%, #2997ff 100%);
    border: none;
    box-shadow: 0 1px 3px rgba(0, 113, 227, 0.25);
    transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.btn-generate:hover:not(:disabled) {
    box-shadow: 0 6px 16px rgba(0, 113, 227, 0.35);
    transform: translateY(-1px);
}

.btn-generate:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 6px rgba(0, 113, 227, 0.3);
}

.btn-generate--inactive {
    opacity: 0.55;
    box-shadow: none;
}

.btn-generate--inactive:hover {
    opacity: 0.72;
    box-shadow: none !important;
    transform: none !important;
}

.btn-clear-full {
    flex: 1;
    height: 44px;
    border-radius: 12px;
    margin-left: 0;
    cursor: pointer;
}

.btn-icon {
    margin-right: 6px;
}

/* ========== 图表预览：粘贴按钮 ========== */
.btn-paste {
    height: 32px;
    border-radius: 8px;
    font-weight: 500;
}

.row-tag {
    margin-left: 6px;
}

/* ========== 图表展示区 ========== */
.chart-display-area {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

/* ========== 统计摘要 ========== */
.stats-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    flex-shrink: 0;
}

.stats-table {
    width: 100%;
}

/* ========== 图表图片 ========== */
.chart-images {
    display: flex;
    flex-direction: column;
    gap: 24px;
    align-items: center;
}

.chart-item {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.chart-label {
    align-self: flex-start;
    font-size: 12px;
    font-weight: 600;
    color: #86868b;
    letter-spacing: 0.3px;
}

.chart-img {
    width: 100%;
    max-width: 720px;
    border: 1px solid #ececef;
    border-radius: 10px;
    transition: box-shadow 0.2s ease;
    cursor: grab;
}

.chart-img:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* ========== 空状态（与边缘应力页一致） ========== */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 300px;
    border: 2px dashed #e4e4e7;
    border-radius: 12px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.empty-state:hover {
    border-color: #0071e3;
    background: rgba(0, 113, 227, 0.03);
}

.empty-state:hover .empty-icon {
    color: #0071e3;
    transform: translateY(-2px);
}

.empty-icon {
    color: #c7c7cc;
    transition: transform 0.2s ease, color 0.2s ease;
}

.empty-title {
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
    margin-top: 14px;
}

.empty-desc {
    font-size: 13px;
    color: #86868b;
    margin-top: 6px;
}

/* ========== 粘贴数据 Dialog ========== */
.paste-dialog-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 50vh;
    border: 2px dashed #e4e7ed;
    border-radius: 8px;
    padding: 20px;
    outline: none;
    transition: border-color 0.2s;
    overflow: hidden;
}

.paste-dialog-area:focus,
.paste-dialog-area:focus-within {
    border-color: var(--el-color-primary);
}

.paste-dialog-area .empty-desc kbd {
    font-size: 11px;
    background: #f0f0f0;
    border-radius: 3px;
    padding: 1px 5px;
    font-family: inherit;
    margin: 0 1px;
    border: 1px solid #d9d9d9;
}

.paste-dialog-area .empty-hint {
    font-size: 12px;
    color: #c0c4cc;
    margin-top: 12px;
}

.paste-preview-table {
    width: 100%;
    flex: 1;
    min-height: 0;
}

.paste-info {
    margin-top: 12px;
    font-size: 13px;
    color: #909399;
    text-align: center;
}

.paste-info strong {
    color: var(--el-color-primary);
}

/* 输入框 / el-input-number 通用样式 → 见 main.css「工具页通用样式」段 */
</style>
