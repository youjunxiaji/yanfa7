<template>
    <div class="page-container">
        <!-- 上半部分：参数 + 表格 -->
        <el-row :gutter="20" class="page-row">
            <!-- 左侧参数面板 -->
            <el-col :span="10">
                <div class="param-panel">
                    <!-- 分箱参数 -->
                    <el-card class="param-card">
                        <template #header>
                            <div class="card-header">
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

                        <!-- 统计摘要 -->
                        <div v-if="statsData" class="stats-section">
                            <div class="stats-label">数据统计（共 {{ tableData.length }} 行）</div>
                            <el-table :data="statsTableData" size="small" border class="stats-table">
                                <el-table-column prop="metric" label="" width="60" />
                                <el-table-column prop="timeFront" label="时间-前" align="center" />
                                <el-table-column prop="pmaxFront" label="Pmax-前" align="center" />
                                <el-table-column prop="pmaxRear" label="Pmax-后" align="center" />
                            </el-table>
                        </div>
                    </el-card>

                    <!-- 字体参数 -->
                    <el-card class="param-card">
                        <template #header>
                            <div class="card-header">
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
                    </el-card>

                    <!-- 图形比例 + 操作按钮 -->
                    <el-card class="param-card">
                        <template #header>
                            <div class="card-header">
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
                    </el-card>

                    <!-- 语言 + 操作按钮 -->
                    <el-card class="param-card">
                        <template #header>
                            <div class="card-header">
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
                                plain
                                class="action-btn-full"
                                @click="parseData"
                            >
                                解析数据
                            </el-button>
                            <el-button
                                type="primary"
                                class="action-btn-full"
                                :disabled="!statsData"
                                @click="generateCharts"
                            >
                                <el-icon style="margin-right: 6px;"><TrendCharts /></el-icon>
                                生成图表
                            </el-button>
                            <el-button
                                plain
                                class="action-btn-full"
                                :disabled="tableData.length === 0"
                                @click="clearTable"
                            >
                                <el-icon style="margin-right: 6px;"><Delete /></el-icon>
                                清空表格
                            </el-button>
                        </div>
                    </el-card>
                </div>
            </el-col>

            <!-- 右侧数据表格 -->
            <el-col :span="14">
                <el-card class="table-card">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon :size="16" color="#0071e3"><Grid /></el-icon>
                                <span class="card-title">数据表格</span>
                            </div>
                            <el-tag v-if="tableData.length > 0" type="info" size="small" round>
                                {{ tableData.length }} 行
                            </el-tag>
                        </div>
                    </template>

                    <div
                        class="paste-table-wrapper"
                        @paste="handlePaste"
                        tabindex="0"
                    >
                        <el-table
                            v-if="tableData.length > 0"
                            :data="tableData"
                            border
                            size="small"
                            max-height="520"
                            class="data-table"
                        >
                            <el-table-column type="index" label="#" width="50" align="center" />
                            <el-table-column prop="timeFront" label="持续时间 [h]" align="center" min-width="120">
                                <template #default="{ row, $index }">
                                    <el-input
                                        v-model="row.timeFront"
                                        size="small"
                                        class="cell-input"
                                        @change="onCellChange($index)"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="pmaxFront" label="Pmax (MPa)-前" align="center" min-width="130">
                                <template #default="{ row, $index }">
                                    <el-input
                                        v-model="row.pmaxFront"
                                        size="small"
                                        class="cell-input"
                                        @change="onCellChange($index)"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="timeRear" label="持续时间 [h]" align="center" min-width="120">
                                <template #default="{ row, $index }">
                                    <el-input
                                        v-model="row.timeRear"
                                        size="small"
                                        class="cell-input"
                                        @change="onCellChange($index)"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="pmaxRear" label="Pmax (MPa)-后" align="center" min-width="130">
                                <template #default="{ row, $index }">
                                    <el-input
                                        v-model="row.pmaxRear"
                                        size="small"
                                        class="cell-input"
                                        @change="onCellChange($index)"
                                    />
                                </template>
                            </el-table-column>
                        </el-table>

                        <!-- 空状态 -->
                        <div v-else class="empty-paste-area">
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
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 下半部分：图表预览 -->
        <div v-if="chartImages.front || chartImages.rear" class="chart-preview-section">
            <el-card class="chart-card">
                <template #header>
                    <div class="card-header">
                        <div class="card-header-left">
                            <el-icon :size="16" color="#0071e3"><TrendCharts /></el-icon>
                            <span class="card-title">图表预览</span>
                        </div>
                        <el-button size="small" text type="primary" @click="clearCharts">
                            清除预览
                        </el-button>
                    </div>
                </template>
                <div class="chart-images">
                    <div v-if="chartImages.front" class="chart-item">
                        <img :src="chartImages.front" alt="前轴承" class="chart-img" />
                        <span class="chart-label">前轴承</span>
                    </div>
                    <div v-if="chartImages.rear" class="chart-item">
                        <img :src="chartImages.rear" alt="后轴承" class="chart-img" />
                        <span class="chart-label">后轴承</span>
                    </div>
                </div>
            </el-card>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
    Setting,
    EditPen,
    PictureFilled,
    TrendCharts,
    Delete,
    Grid,
    DocumentCopy,
    Operation
} from '@element-plus/icons-vue'
import { Language, LANGUAGE_OPTIONS } from '@renderer/constants/language'

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

interface StatsInfo {
    timeFront: { min: number; max: number }
    pmaxFront: { min: number; max: number }
    pmaxRear: { min: number; max: number }
}

const statsData = ref<StatsInfo | null>(null)

const statsTableData = computed(() => {
    if (!statsData.value) return []
    const s = statsData.value
    return [
        {
            metric: 'Min',
            timeFront: s.timeFront.min.toFixed(2),
            pmaxFront: s.pmaxFront.min.toFixed(2),
            pmaxRear: s.pmaxRear.min.toFixed(2)
        },
        {
            metric: 'Max',
            timeFront: s.timeFront.max.toFixed(2),
            pmaxFront: s.pmaxFront.max.toFixed(2),
            pmaxRear: s.pmaxRear.max.toFixed(2)
        }
    ]
})

// ========== 图表 ==========
const chartImages = reactive({
    front: '',
    rear: ''
})

// ========== 粘贴处理 ==========
function handlePaste(event: ClipboardEvent): void {
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

    tableData.value = parsed
    ElMessage.success(`已粘贴 ${parsed.length} 行数据`)
    parseData()
}

function onCellChange(_index: number): void {
    statsData.value = null
}

// ========== 解析数据 ==========
function parseData(): void {
    if (tableData.value.length === 0) {
        ElMessage.warning('请先粘贴或输入数据')
        return
    }

    const timeFrontValues: number[] = []
    const pmaxFrontValues: number[] = []
    const pmaxRearValues: number[] = []

    for (const row of tableData.value) {
        const tf = parseFloat(row.timeFront)
        const pf = parseFloat(row.pmaxFront)
        const pr = parseFloat(row.pmaxRear)

        if (!isNaN(tf)) timeFrontValues.push(tf)
        if (!isNaN(pf)) pmaxFrontValues.push(pf)
        if (!isNaN(pr)) pmaxRearValues.push(pr)
    }

    if (pmaxFrontValues.length === 0 && pmaxRearValues.length === 0) {
        ElMessage.warning('未找到有效的数值数据')
        return
    }

    statsData.value = {
        timeFront: {
            min: timeFrontValues.length ? Math.min(...timeFrontValues) : 0,
            max: timeFrontValues.length ? Math.max(...timeFrontValues) : 0
        },
        pmaxFront: {
            min: pmaxFrontValues.length ? Math.min(...pmaxFrontValues) : 0,
            max: pmaxFrontValues.length ? Math.max(...pmaxFrontValues) : 0
        },
        pmaxRear: {
            min: pmaxRearValues.length ? Math.min(...pmaxRearValues) : 0,
            max: pmaxRearValues.length ? Math.max(...pmaxRearValues) : 0
        }
    }

    ElMessage.success('数据解析完成')
}

// ========== 生成图表（暂未联后端） ==========
function generateCharts(): void {
    ElMessage.info('图表生成功能将在后端接入后启用')
}

// ========== 清空 ==========
function clearTable(): void {
    tableData.value = []
    statsData.value = null
    chartImages.front = ''
    chartImages.rear = ''
}

function clearCharts(): void {
    chartImages.front = ''
    chartImages.rear = ''
}
</script>

<style scoped>
.page-container {
    padding: 20px;
    height: 100%;
    overflow-y: auto;

}

.page-row {
    margin-bottom: 20px;
}

/* ========== 参数面板 ========== */
.param-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.param-card {
    border-radius: 12px;
}

.param-card :deep(.el-card__header) {
    padding: 12px 16px;
}

.param-card :deep(.el-card__body) {
    padding: 12px 16px;
}

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
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
}

.stats-label {
    font-size: 12px;
    color: #86868b;
    margin-bottom: 8px;
}

.stats-table {
    width: 100%;
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

/* ========== 数据表格 ========== */
.table-card {
    border-radius: 12px;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.table-card :deep(.el-card__header) {
    padding: 12px 16px;
    flex-shrink: 0;
}

.table-card :deep(.el-card__body) {
    padding: 12px 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.paste-table-wrapper {
    outline: none;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.paste-table-wrapper:focus-within {
    outline: none;
}

.data-table {
    width: 100%;
}

.cell-input :deep(.el-input__wrapper) {
    box-shadow: none;
    padding: 0 4px;
}

.cell-input :deep(.el-input__inner) {
    text-align: center;
    font-size: 13px;
}

/* ========== 空状态 ========== */
.empty-paste-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 200px;
    border: 2px dashed #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: border-color 0.2s;
}

.empty-paste-area:hover {
    border-color: var(--el-color-primary);
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

.empty-desc kbd {
    font-size: 11px;
    background: #f0f0f0;
    border-radius: 3px;
    padding: 1px 5px;
    font-family: inherit;
    margin: 0 1px;
    border: 1px solid #d9d9d9;
}

.empty-hint {
    font-size: 12px;
    color: #c0c4cc;
    margin-top: 12px;
}

/* ========== 图表预览 ========== */
.chart-preview-section {
    margin-top: 20px;
}

.chart-card {
    border-radius: 12px;
}

.chart-card :deep(.el-card__header) {
    padding: 12px 16px;
}

.chart-images {
    display: flex;
    gap: 20px;
    justify-content: center;
}

.chart-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.chart-img {
    width: 100%;
    max-width: 600px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    transition: box-shadow 0.2s;
}

.chart-img:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-label {
    font-size: 13px;
    font-weight: 500;
    color: #86868b;
}
</style>
