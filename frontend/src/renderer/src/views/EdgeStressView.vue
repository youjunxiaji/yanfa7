<template>
    <div class="page-container">
        <el-row :gutter="20" class="page-row">
            <el-col :span="14">
                <el-card class="equal-height-card">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon
                                    :size="18"
                                    color="#0071e3"
                                >
                                    <FolderOpened />
                                </el-icon>
                                <span class="card-title">数据文件</span>
                            </div>
                            <el-tag
                                v-if="store.hasFiles"
                                type="success"
                                size="default"
                                round
                                class="file-count-tag"
                            >
                                <el-icon :size="14" style="vertical-align: middle;">
                                    <CircleCheckFilled />
                                </el-icon>
                                <span style="vertical-align: middle;">已选 {{ store.files.length }} 个文件</span>
                            </el-tag>
                        </div>
                    </template>

                    <!-- 文件选择按钮 -->
                    <div class="file-select-buttons">
                        <el-button
                            type="primary"
                            style="flex: 2;"
                            :loading="scanning"
                            @click="triggerFolderSelect"
                        >
                            <el-icon v-if="!scanning" style="margin-right: 6px;">
                                <FolderOpened />
                            </el-icon>
                            {{ scanning ? '扫描中…' : '选择文件夹' }}
                        </el-button>
                        <el-popconfirm
                            title="确定清空所有文件吗？"
                            confirm-button-text="确定"
                            cancel-button-text="取消"
                            width="220"
                            @confirm="store.clearFiles()"
                        >
                            <template #reference>
                                <el-button
                                    type="danger"
                                    plain
                                    style="flex: 1;"
                                    :disabled="!store.hasFiles"
                                >
                                    <el-icon style="margin-right: 6px;">
                                        <Delete />
                                    </el-icon>
                                    一键清空
                                </el-button>
                            </template>
                        </el-popconfirm>
                    </div>

                    <!-- 文件列表 -->
                    <div
                        v-if="store.hasFiles"
                        class="file-list-container"
                    >
                        <div
                            v-for="(file, index) in store.files"
                            :key="index"
                            class="file-item"
                        >
                            <FileResultPopover
                                :file-name="file.name"
                                :preview-items="store.getPreviewItems(file.name)"
                            >
                                <div class="file-item-left">
                                    <el-icon
                                        color="#0071e3"
                                        :size="16"
                                    >
                                        <Document />
                                    </el-icon>
                                    <span class="file-name">{{ file.name }}</span>
                                </div>
                            </FileResultPopover>
                            <div class="file-item-right">
                                <el-button
                                    text
                                    size="small"
                                    @click="previewFile(index)"
                                >
                                    <el-icon color="#0071e3">
                                        <View />
                                    </el-icon>
                                </el-button>
                                <el-button
                                    text
                                    type="danger"
                                    size="small"
                                    @click="removeFile(index)"
                                >
                                    <el-icon>
                                        <Close />
                                    </el-icon>
                                </el-button>
                            </div>
                        </div>
                    </div>

                    <!-- 扫描中状态 -->
                    <div
                        v-else-if="scanning"
                        class="empty-state scanning-state"
                    >
                        <el-icon
                            :size="40"
                            color="#0071e3"
                            class="scanning-icon"
                        >
                            <Loading />
                        </el-icon>
                        <div class="scanning-title">正在扫描文件夹…</div>
                        <div class="scanning-desc">请稍候，正在查找 HTM 文件</div>
                    </div>

                    <!-- 空状态 -->
                    <div
                        v-else
                        class="empty-state"
                    >
                        <el-icon
                            :size="56"
                            color="#d2d2d7"
                        >
                            <Document />
                        </el-icon>
                        <div class="empty-text">
                            请选择数据文件开始分析
                        </div>
                    </div>

                    <!-- 进度条 -->
                    <div class="mt-12">
                        <el-progress
                            :percentage="store.progressPercent"
                            :color="progressColor"
                            :stroke-width="24"
                            :text-inside="true"
                        />
                        <div
                            v-if="store.stageMessage"
                            class="stage-message"
                        >
                            {{ store.stageMessage }}
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="10">
                <el-card class="equal-height-card">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon
                                    :size="18"
                                    color="#0071e3"
                                >
                                    <Setting />
                                </el-icon>
                                <span class="card-title">参数配置</span>
                            </div>
                        </div>
                    </template>

                    <el-form
                        label-position="left"
                        label-width="120px"
                    >
                        <!-- 保存路径 -->
                        <el-form-item label="保存路径">
                            <div style="display: flex; width: 100%;">
                                <el-tooltip
                                    :content="store.outputDir"
                                    :disabled="!store.outputDir"
                                    placement="top"
                                >
                                    <el-input
                                        v-model="store.outputDir"
                                        placeholder="请输入或选择文件保存路径"
                                        @blur="onOutputDirBlur"
                                    >
                                        <template #prefix>
                                            <el-icon :size="16">
                                                <Folder />
                                            </el-icon>
                                        </template>
                                    </el-input>
                                </el-tooltip>
                                <el-button style="margin-left: 8px;" @click="browseOutputDir">
                                    浏览
                                </el-button>
                            </div>
                        </el-form-item>

                        <!-- 数据处理 -->
                        <div class="section-label">
                            <el-icon :size="14">
                                <Operation />
                            </el-icon>
                            数据处理
                        </div>

                        <el-form-item label="峰值阈值判定">
                            <el-input-number
                                v-model="store.processConfig.peakThreshold"
                                :step="0.00001"
                                :min="0"
                                :max="4000"
                                style="width: 100%;"
                                controls-position="right"
                            />
                        </el-form-item>

                        <!-- 图片设置 -->
                        <div class="section-label">
                            <el-icon :size="14">
                                <PictureFilled />
                            </el-icon>
                            图片设置
                        </div>

                        <el-form-item label="宽度 (英寸)">
                            <el-input-number
                                v-model="store.reportConfig.picWidth"
                                :step="0.1"
                                :min="1"
                                :max="30"
                                style="width: 100%;"
                                controls-position="right"
                            />
                        </el-form-item>
                        <el-form-item label="高度 (英寸)">
                            <el-input-number
                                v-model="store.reportConfig.picHeight"
                                :step="0.1"
                                :min="1"
                                :max="30"
                                style="width: 100%;"
                                controls-position="right"
                            />
                        </el-form-item>
                        <!-- 开始解析按钮 -->
                        <div class="section-label">
                            <el-icon :size="14">
                                <VideoPlay />
                            </el-icon>
                            执行操作
                        </div>

                        <el-button
                            type="primary"
                            size="large"
                            style="width: 100%;"
                            :disabled="!canParse"
                            :loading="store.isProcessing"
                            @click="startParse"
                        >
                            <el-icon v-if="!store.isProcessing" style="margin-right: 6px;">
                                <CaretRight />
                            </el-icon>
                            {{ store.isProcessing ? '解析中...' : '开始解析' }}
                        </el-button>
                    </el-form>
                </el-card>

            </el-col>
        </el-row>

        <!-- 跳过文件 Dialog -->
        <el-dialog
            v-model="skippedDialogVisible"
            title="部分文件被跳过"
            width="560"
            align-center
        >
            <el-table :data="skippedTableData" stripe style="width: 100%;">
                <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
                <el-table-column prop="reason" label="跳过原因" min-width="260" show-overflow-tooltip />
            </el-table>
            <template #footer>
                <el-button type="primary" @click="skippedDialogVisible = false">知道了</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
    FolderOpened,
    Document,
    Close,
    View,
    Setting,
    Folder,
    Operation,
    PictureFilled,
    VideoPlay,
    CaretRight,
    CircleCheckFilled,
    Delete,
    Loading,
} from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useEdgeStressStore, type FileInfo } from '@renderer/stores/edgeStress'
import { parseWithProgress, type WsMessage, type SkippedFile } from '@renderer/api/edgeStress'
import FileResultPopover from '@renderer/components/FileResultPopover.vue'

const store = useEdgeStressStore()

const skippedDialogVisible = ref(false)
const skippedTableData = ref<SkippedFile[]>([])

const progressColor = computed(() => {
    if (store.isDone) return '#34c759'
    if (store.processStatus === 'error') return '#ff3b30'
    return '#0071e3'
})

// ========== 文件选择 ==========
const scanning = ref(false)

const triggerFolderSelect = async () => {
    const { canceled, rootDir } = await window.electronAPI.openDir({
        title: '选择包含 HTM 文件的文件夹',
    })
    if (canceled || !rootDir) return

    scanning.value = true
    try {
        const { filePaths, fileSizes } = await window.electronAPI.scanDir({
            rootDir,
            extensions: ['htm'],
        })

        if (filePaths.length === 0) {
            ElMessage.info('所选文件夹中未找到 HTM 文件')
            return
        }

        const newFiles: FileInfo[] = filePaths.map((fp, i) => {
            const name = fp.split(/[\\/]/).pop() || fp
            return { name, path: fp, size: fileSizes[i] ?? 0 }
        })

        store.setFiles(newFiles, 'htm')
        ElNotification.success({
            title: '扫描完成',
            message: `已扫描到 ${newFiles.length} 个 HTM 文件`,
            duration: 3000,
        })
    } finally {
        scanning.value = false
    }
}

/** 预览文件：在独立窗口中打开报告预览 */
const previewFile = (index: number) => {
    if (!store.isDone) {
        ElMessage.info('请先完成解析后再预览报告')
        return
    }
    const name = store.files[index]?.name ?? ''
    const fileStem = name.replace(/\.[^.]+$/, '')
    const columns = (store.resultColumns[fileStem] ?? []).join(',')

    window.electronAPI.openPreviewWindow({
        fileStem,
        outputDir: store.outputDir,
        columns,
        title: `报告预览 - ${fileStem}`
    })
}

/** 删除单个文件 */
function removeFile(index: number) {
    store.files.splice(index, 1)
    if (store.files.length === 0) {
        store.clearFiles()
    }
}

// ========== 保存位置 ==========

function onOutputDirBlur() {
    // 后续可以校验路径是否存在
}

async function browseOutputDir() {
    const result = await window.electronAPI.openDirectoryDialog({
        title: '选择保存路径',
    })

    if (!result.canceled && result.filePaths.length > 0) {
        store.outputDir = result.filePaths[0]!
    }
}

// ========== 开始解析 ==========

const canParse = computed(() => store.hasFiles && !store.isProcessing)

function startParse() {
    if (!store.outputDir) {
        ElMessage.warning('请先设置保存路径')
        return
    }
    if (store.files.length === 0) {
        ElMessage.warning('请先选择文件')
        return
    }

    store.setProcessStatus('processing')
    store.updateProgress(0, store.files.length)
    store.stageMessage = '正在连接解析服务…'

    const filePaths = store.files.map((f) => f.path)
    parseWithProgress(
        filePaths,
        store.fileType,
        store.processConfig.peakThreshold,
        store.outputDir,
        {
            picWidth: store.reportConfig.picWidth,
            picHeight: store.reportConfig.picHeight,
            loadPolarMin: store.reportConfig.loadPolarMin,
            pressPolarMin: store.reportConfig.pressPolarMin,
        },
        (msg: WsMessage) => {
            if (msg.type === 'progress') {
                store.updateProgress(msg.current, msg.total)
                store.stageMessage = `正在处理: ${msg.filename} (${msg.current + 1}/${msg.total})`
            } else if (msg.type === 'done') {
                store.updateProgress(store.progressTotal, store.progressTotal)
                store.setProcessStatus('done')
                store.stageMessage = ''
                if (msg.previewMap) {
                    store.setPreviewMap(msg.previewMap)
                }
                if (msg.columns) {
                    store.setResultColumns(msg.columns)
                }
                const skipped = msg.skippedFiles ?? []
                if (skipped.length > 0) {
                    skippedTableData.value = skipped
                    skippedDialogVisible.value = true
                }
                ElMessage.success(`解析完成！已生成 ${msg.generatedFiles.length} 个文件`)
            } else if (msg.type === 'error') {
                store.setProcessStatus('error', msg.message)
                store.stageMessage = ''
                ElMessage.error(`解析失败: ${msg.message}`)
            }
        }
    )
}


</script>

<style scoped>
.page-container {
    height: 470px;
}

.page-row {
    height: 100%;
}

.page-row :deep(.el-col) {
    height: 100%;
}

.equal-height-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    overflow: hidden;
}

.equal-height-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.equal-height-card :deep(.el-card__body) > .empty-state {
    flex: 1;
}

.mt-12 {
    margin-top: 12px;
}

.stage-message {
    margin-top: 6px;
    font-size: 12px;
    color: #888;
    text-align: center;
}

.mt-16 {
    margin-top: 16px;
}

/* ========== 卡片头部 ========== */
.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 32px;
}

.card-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.card-title {
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
}

/* ========== 文件计数标签 ========== */
.file-count-tag {
    padding: 14px 14px !important;
}

.file-count-tag :deep(.el-tag__content) {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* ========== 文件选择按钮 ========== */
.file-select-buttons {
    display: flex;
    gap: 12px;
}

/* ========== 文件列表 ========== */
.file-list-container {
    border: 1px solid #e5e5ea;
    border-radius: 10px;
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    margin-top: 12px;
}

.file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    transition: background-color 0.15s ease;
}

.file-item:hover {
    background-color: #f5f5f7;
}

.file-item+.file-item {
    border-top: 1px solid #f2f2f7;
}

.file-item-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.file-name {
    font-size: 13px;
    color: #1d1d1f;
}

.file-item-right {
    display: flex;
    align-items: center;
    gap: 4px;
}

.file-item-right :deep(.el-button+.el-button) {
    margin-left: 0;
}

/* ========== 空状态 ========== */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 0;
    border: 2px dashed #e5e5ea;
    border-radius: 12px;
    margin-top: 16px;
}

.empty-text {
    font-size: 13px;
    color: #86868b;
    margin-top: 12px;
}

/* ========== 扫描中状态 ========== */
.scanning-state {
    border-color: #0071e3;
    border-style: dashed;
    background: rgba(0, 113, 227, 0.03);
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.scanning-icon {
    animation: spin 1.2s linear infinite;
}

.scanning-title {
    font-size: 15px;
    font-weight: 600;
    color: #0071e3;
    margin-top: 12px;
}

.scanning-desc {
    font-size: 13px;
    color: #86868b;
    margin-top: 4px;
}

/* ========== 分区标签 ========== */
.section-label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    color: #86868b;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin: 20px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f2f2f7;
}

/* ========== 表单项间距 ========== */
:deep(.el-form-item) {
    margin-bottom: 16px;
}
</style>
