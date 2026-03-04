<template>
    <el-dialog
        v-model="visible"
        :title="fileName"
        fullscreen
        :close-on-click-modal="true"
        :close-on-press-escape="true"
        class="preview-dialog"
    >
        <div v-if="columns.length > 0" class="preview-wrapper">
            <!-- 顶部控制栏 -->
            <div class="control-bar">
                <div class="control-group">
                    <span class="control-label">列号</span>
                    <el-select
                        v-model="selectedCol"
                        style="width: 120px;"
                        size="default"
                    >
                        <el-option
                            v-for="col in columns"
                            :key="col"
                            :label="`第 ${col} 列`"
                            :value="col"
                        />
                    </el-select>
                </div>
                <div class="control-group">
                    <span class="control-label">滚道</span>
                    <el-radio-group v-model="stressPosition" size="default">
                        <el-radio-button value="inner">内滚道</el-radio-button>
                        <el-radio-button value="outer">外滚道</el-radio-button>
                    </el-radio-group>
                </div>
            </div>

            <!-- 三栏内容 -->
            <el-splitter class="content-splitter">
                <!-- 左栏: HTML 报告 -->
                <el-splitter-panel :size="40" :min="20">
                    <div class="panel-wrapper">
                        <div class="panel-title">HTML 报告</div>
                        <div class="panel-body">
                            <iframe
                                v-if="htmlReportPath"
                                :src="`local-file://${htmlReportPath}`"
                                class="report-iframe"
                            />
                            <div v-else class="panel-empty">
                                <el-icon :size="40" color="#d2d2d7"><Document /></el-icon>
                                <span>报告文件不存在</span>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>

                <!-- 中栏: 应力曲线图 -->
                <el-splitter-panel :size="30" :min="15">
                    <div class="panel-wrapper">
                        <div class="panel-title">应力曲线图</div>
                        <div class="panel-body panel-scroll">
                            <div class="image-group">
                                <div class="image-label">中文</div>
                                <img
                                    v-if="stressChartCnPath"
                                    :src="`local-file://${stressChartCnPath}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressChartCnPath)"
                                >
                                <div v-else class="image-placeholder">图片不存在</div>
                            </div>
                            <div class="image-group">
                                <div class="image-label">英文</div>
                                <img
                                    v-if="stressChartEnPath"
                                    :src="`local-file://${stressChartEnPath}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressChartEnPath)"
                                >
                                <div v-else class="image-placeholder">图片不存在</div>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>

                <!-- 右栏: 雷达图 -->
                <el-splitter-panel :size="30" :min="15">
                    <div class="panel-wrapper">
                        <div class="panel-title">雷达图</div>
                        <div class="panel-body panel-scroll">
                            <div class="image-group">
                                <div class="image-label">载荷分布</div>
                                <img
                                    v-if="loadPolarPath"
                                    :src="`local-file://${loadPolarPath}`"
                                    class="chart-img"
                                    @click="openImagePreview(loadPolarPath)"
                                >
                                <div v-else class="image-placeholder">图片不存在</div>
                            </div>
                            <div class="image-group">
                                <div class="image-label">应力分布</div>
                                <img
                                    v-if="stressPolarPath"
                                    :src="`local-file://${stressPolarPath}`"
                                    class="chart-img"
                                    @click="openImagePreview(stressPolarPath)"
                                >
                                <div v-else class="image-placeholder">图片不存在</div>
                            </div>
                        </div>
                    </div>
                </el-splitter-panel>
            </el-splitter>
        </div>

        <!-- 未解析 / 无数据状态 -->
        <div v-else class="empty-state">
            <el-icon :size="64" color="#d2d2d7"><Document /></el-icon>
            <div class="empty-text">请先完成解析以查看报告</div>
        </div>
    </el-dialog>

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
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Document } from '@element-plus/icons-vue'
import { useEdgeStressStore } from '@renderer/stores/edgeStress'

const props = defineProps<{
    show: boolean
    fileName: string
    fileStem: string
}>()

const emit = defineEmits<{
    (e: 'update:show', value: boolean): void
}>()

const store = useEdgeStressStore()

const visible = computed({
    get: () => props.show,
    set: (val) => emit('update:show', val),
})

const selectedCol = ref(1)
const stressPosition = ref<'inner' | 'outer'>('inner')

const columns = computed(() => store.getColumnsByFile(props.fileName))

watch(columns, (cols) => {
    if (cols.length > 0 && !cols.includes(selectedCol.value)) {
        selectedCol.value = cols[0]!
    }
}, { immediate: true })

const basePath = computed(() => store.getReportBasePath(props.fileName))

const positionLabel = computed(() =>
    stressPosition.value === 'inner' ? '内滚道接触应力' : '外滚道接触应力'
)

const htmlReportPath = computed(() => {
    if (!basePath.value || columns.value.length === 0) return ''
    return `${basePath.value}/${props.fileStem}-${positionLabel.value}-第${selectedCol.value}列.html`
})

const stressChartCnPath = computed(() => {
    if (!basePath.value || columns.value.length === 0) return ''
    return `${basePath.value}/${props.fileStem}-${positionLabel.value}-第${selectedCol.value}列-中.png`
})

const stressChartEnPath = computed(() => {
    if (!basePath.value || columns.value.length === 0) return ''
    return `${basePath.value}/${props.fileStem}-${positionLabel.value}-第${selectedCol.value}列-英.png`
})

const loadPolarPath = computed(() => {
    if (!basePath.value || columns.value.length === 0) return ''
    return `${basePath.value}/${props.fileStem}-第${selectedCol.value}列-载荷雷达图.png`
})

const stressPolarPath = computed(() => {
    if (!basePath.value || columns.value.length === 0) return ''
    return `${basePath.value}/${props.fileStem}-第${selectedCol.value}列-应力雷达图.png`
})

const imagePreviewVisible = ref(false)
const imagePreviewSrc = ref('')

function openImagePreview(path: string) {
    imagePreviewSrc.value = path
    imagePreviewVisible.value = true
}
</script>

<style scoped>
.preview-dialog :deep(.el-dialog__body) {
    padding: 0 16px 16px;
    height: calc(100vh - 56px);
    display: flex;
    flex-direction: column;
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
    gap: 24px;
    padding: 8px 0 12px;
    flex-shrink: 0;
}

.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.control-label {
    font-size: 13px;
    font-weight: 600;
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

/* ========== iframe ========== */
.report-iframe {
    width: 100%;
    height: 100%;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
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
    height: 60vh;
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
