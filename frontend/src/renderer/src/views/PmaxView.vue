<template>
    <div class="page-container">
        <el-row :gutter="20" class="page-row">
            <!-- 左侧参数面板 -->
            <el-col :span="10">
                <el-collapse v-model="expandedPanels" class="param-collapse">
                    <!-- 分箱参数 -->
                    <el-collapse-item name="bin">
                        <template #title>
                            <div class="collapse-title">
                                <el-icon :size="16" color="#0071e3"><Setting /></el-icon>
                                <span class="card-title">分箱参数</span>
                            </div>
                        </template>
                        <div class="bin-param-grid">
                            <div class="bin-header">
                                <span class="bin-label-placeholder"></span>
                                <span class="bin-col-title">前轴承</span>
                                <span class="bin-col-title">后轴承</span>
                            </div>
                            <div class="bin-row">
                                <span class="bin-label">Min</span>
                                <el-input-number
                                    v-model="binConfig.front.min"
                                    :step="50"
                                    :min="0"
                                    :max="100000"
                                    size="small"
                                    controls-position="right"
                                />
                                <el-input-number
                                    v-model="binConfig.rear.min"
                                    :step="50"
                                    :min="0"
                                    :max="100000"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="bin-row">
                                <span class="bin-label">Max</span>
                                <el-input-number
                                    v-model="binConfig.front.max"
                                    :step="50"
                                    :min="0"
                                    :max="100000"
                                    size="small"
                                    controls-position="right"
                                />
                                <el-input-number
                                    v-model="binConfig.rear.max"
                                    :step="50"
                                    :min="0"
                                    :max="100000"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="bin-row">
                                <span class="bin-label">Step</span>
                                <el-input-number
                                    v-model="binConfig.front.step"
                                    :step="50"
                                    :min="1"
                                    :max="500"
                                    size="small"
                                    controls-position="right"
                                />
                                <el-input-number
                                    v-model="binConfig.rear.step"
                                    :step="50"
                                    :min="1"
                                    :max="500"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                        </div>
                    </el-collapse-item>

                    <!-- 字体参数 -->
                    <el-collapse-item name="font">
                        <template #title>
                            <div class="collapse-title">
                                <el-icon :size="16" color="#0071e3"><EditPen /></el-icon>
                                <span class="card-title">字体参数</span>
                            </div>
                        </template>
                        <div class="font-param-list">
                            <div class="font-row">
                                <span class="font-label">标题</span>
                                <el-input-number
                                    v-model="chartConfig.titleFontSize"
                                    :min="1"
                                    :max="30"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="font-row">
                                <span class="font-label">标签</span>
                                <el-input-number
                                    v-model="chartConfig.labelFontSize"
                                    :min="1"
                                    :max="30"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="font-row">
                                <span class="font-label">坐标轴</span>
                                <el-input-number
                                    v-model="chartConfig.tickFontSize"
                                    :min="1"
                                    :max="30"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="font-row">
                                <span class="font-label">标注</span>
                                <el-input-number
                                    v-model="chartConfig.textFontSize"
                                    :min="1"
                                    :max="30"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                        </div>
                    </el-collapse-item>

                    <!-- 图形比例 -->
                    <el-collapse-item name="size">
                        <template #title>
                            <div class="collapse-title">
                                <el-icon :size="16" color="#0071e3"><PictureFilled /></el-icon>
                                <span class="card-title">图形比例</span>
                            </div>
                        </template>
                        <div class="size-row">
                            <div class="size-item">
                                <span class="font-label">长</span>
                                <el-input-number
                                    v-model="chartConfig.width"
                                    :min="1"
                                    :max="20"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                            <div class="size-item">
                                <span class="font-label">宽</span>
                                <el-input-number
                                    v-model="chartConfig.height"
                                    :min="1"
                                    :max="20"
                                    size="small"
                                    controls-position="right"
                                />
                            </div>
                        </div>
                    </el-collapse-item>

                    <!-- 操作 -->
                    <el-collapse-item name="action">
                        <template #title>
                            <div class="collapse-title">
                                <el-icon :size="16" color="#0071e3"><Operation /></el-icon>
                                <span class="card-title">操作</span>
                            </div>
                        </template>
                        <div class="action-area">
                            <div class="lang-row">
                                <span class="lang-label">图表语言</span>
                                <el-segmented
                                    v-model="language"
                                    :options="LANGUAGE_OPTIONS"
                                    size="small"
                                />
                            </div>
                            <el-button
                                type="primary"
                                class="action-btn-full"
                                :disabled="tableData.length === 0"
                                :loading="generating"
                                @click="generateCharts"
                            >
                                <el-icon v-if="!generating" style="margin-right: 6px;"><TrendCharts /></el-icon>
                                {{ generating ? '生成中...' : '生成图表' }}
                            </el-button>
                            <el-button
                                plain
                                class="action-btn-full"
                                :disabled="tableData.length === 0"
                                @click="clearAll"
                            >
                                <el-icon style="margin-right: 6px;"><Delete /></el-icon>
                                清空数据
                            </el-button>
                        </div>
                    </el-collapse-item>
                </el-collapse>
            </el-col>

            <!-- 右侧图表展示区 -->
            <el-col :span="14">
                <el-card class="chart-card">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon :size="16" color="#0071e3"><PictureFilled /></el-icon>
                                <span class="card-title">图表预览</span>
                            </div>
                            <el-button size="small" text @click="pasteDialogVisible = true">
                                <el-icon style="margin-right: 4px;"><DocumentCopy /></el-icon>
                                粘贴数据
                                <el-tag v-if="tableData.length > 0" type="info" size="small" round style="margin-left: 6px;">
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
                                <div class="stats-label">数据统计（共 {{ tableData.length }} 行）</div>
                                <el-table :data="statsTableData" size="small" border class="stats-table">
                                    <el-table-column prop="metric" label="" width="60" />
                                    <el-table-column prop="timeFront" label="时间-前" align="center" />
                                    <el-table-column prop="pmaxFront" label="Pmax-前" align="center" />
                                    <el-table-column prop="pmaxRear" label="Pmax-后" align="center" />
                                </el-table>
                            </div>
                            <div class="chart-images">
                                <div v-if="chartPaths.front" class="chart-item">
                                    <img
                                        :src="toLocalFileUrl(chartPaths.front, imgCacheBuster)"
                                        alt="前轴承"
                                        class="chart-img"
                                        draggable="true"
                                        @dragstart="handleDragStart($event, chartPaths.front)"
                                    />
                                </div>
                                <div v-if="chartPaths.rear" class="chart-item">
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
                        <div v-else-if="tableData.length > 0" class="empty-chart-area">
                            <el-icon :size="48" color="#c0c4cc"><TrendCharts /></el-icon>
                            <p class="empty-title">已导入 {{ tableData.length }} 行数据</p>
                            <p class="empty-desc">设置参数后点击「生成图表」查看结果</p>
                        </div>

                        <!-- 初始空状态 -->
                        <div v-else class="empty-chart-area">
                            <el-icon :size="48" color="#c0c4cc"><PictureFilled /></el-icon>
                            <p class="empty-title">暂无图表</p>
                            <p class="empty-desc">请先粘贴数据，再生成图表</p>
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
    Operation
} from '@element-plus/icons-vue'
import { Language, LANGUAGE_OPTIONS } from '@renderer/constants/language'
import { analyzePmax, type AnalyzeResponse } from '@renderer/api/pmax'

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

const expandedPanels = ref<string[]>(['bin', 'action'])

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
    const base = `local-file://localhost?path=${encodeURIComponent(filePath)}`
    return cacheBuster != null ? `${base}&t=${cacheBuster}` : base
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
.page-container {
    padding: 20px;
    height: 100%;
    overflow-y: auto;
}

.page-row {
    height: 100%;
}

/* ========== 卡片通用 ========== */
.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.card-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.card-title {
    font-size: 14px;
    font-weight: 600;
    color: #1d1d1f;
}

/* ========== 分箱参数网格 ========== */
.bin-param-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.bin-header {
    display: grid;
    grid-template-columns: 50px 1fr 1fr;
    gap: 8px;
    align-items: center;
}

.bin-col-title {
    font-size: 12px;
    font-weight: 600;
    color: #86868b;
    text-align: center;
}

.bin-label-placeholder {
    width: 50px;
}

.bin-row {
    display: grid;
    grid-template-columns: 50px 1fr 1fr;
    gap: 8px;
    align-items: center;
}

.bin-label {
    font-size: 13px;
    font-weight: 500;
    color: #636366;
}

.bin-row :deep(.el-input-number) {
    width: 100%;
}

/* ========== 统计摘要 ========== */
.stats-section {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
}

.stats-label {
    font-size: 12px;
    color: #86868b;
    margin-bottom: 8px;
}

.stats-table {
    width: 100%;
}

/* ========== 折叠面板 ========== */
.param-collapse {
    border: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.param-collapse :deep(.el-collapse-item__header) {
    height: 44px;
    line-height: 44px;
    padding: 0 16px;
    background: var(--el-bg-color-overlay);
    border-radius: 12px;
    border: 1px solid var(--el-border-color-light);
    font-size: 14px;
}

.param-collapse :deep(.el-collapse-item__wrap) {
    border: 1px solid var(--el-border-color-light);
    border-top: none;
    border-radius: 0 0 12px 12px;
}

.param-collapse :deep(.el-collapse-item__content) {
    padding: 12px 16px;
}

.param-collapse :deep(.el-collapse-item.is-active .el-collapse-item__header) {
    border-radius: 12px 12px 0 0;
}

.param-collapse :deep(.el-collapse-item__header) {
    border-bottom: none;
}

.param-collapse :deep(.el-collapse-item.is-active .el-collapse-item__header) {
    border-bottom: 1px solid var(--el-border-color-light);
}

.collapse-title {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ========== 字体参数 ========== */
.font-param-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.font-row {
    display: grid;
    grid-template-columns: 60px 1fr;
    gap: 8px;
    align-items: center;
}

.font-label {
    font-size: 13px;
    font-weight: 500;
    color: #636366;
}

.font-row :deep(.el-input-number) {
    width: 100%;
}

/* ========== 图形比例 ========== */
.size-row {
    display: flex;
    gap: 16px;
}

.size-item {
    flex: 1;
    display: grid;
    grid-template-columns: 30px 1fr;
    gap: 8px;
    align-items: center;
}

.size-item :deep(.el-input-number) {
    width: 100%;
}

/* ========== 操作区 ========== */
.action-area {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.lang-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: var(--el-fill-color-light);
    border-radius: 8px;
    margin-bottom: 2px;
}

.lang-label {
    font-size: 13px;
    color: #636366;
}

.action-btn-full {
    width: 100%;
    margin-left: 0;
}

/* ========== 右侧图表展示卡片 ========== */
.chart-card {
    border-radius: 12px;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.chart-card :deep(.el-card__header) {
    padding: 12px 16px;
    flex-shrink: 0;
}

.chart-card :deep(.el-card__body) {
    padding: 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow-y: auto;
}

.chart-display-area {
    flex: 1;
    display: flex;
    flex-direction: column;
}

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

.chart-img {
    width: 100%;
    max-width: 700px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    transition: box-shadow 0.2s;
    cursor: grab;
}

.chart-img:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-label {
    font-size: 13px;
    font-weight: 500;
    color: #86868b;
}

/* ========== 空状态 ========== */
.empty-chart-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 300px;
}

.empty-title {
    font-size: 15px;
    font-weight: 600;
    color: #606266;
    margin-top: 16px;
    margin-bottom: 8px;
}

.empty-desc {
    font-size: 13px;
    color: #909399;
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
</style>
