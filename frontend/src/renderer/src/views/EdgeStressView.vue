<template>
    <div class="edge-stress-page">
        <el-row :gutter="20" class="page-row">
            <el-col :span="14" class="left-col">
                <el-card class="page-card" shadow="never">
                    <template #header>
                        <div class="card-header">
                            <div class="card-header-left">
                                <el-icon :size="18" class="header-icon">
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
                                <el-icon :size="14">
                                    <CircleCheckFilled />
                                </el-icon>
                                <span>已选 {{ store.files.length }} 个文件</span>
                            </el-tag>
                        </div>
                    </template>

                    <div class="file-select-buttons">
                        <el-button
                            type="primary"
                            class="btn-select"
                            :loading="scanning"
                            @click="triggerFolderSelect"
                        >
                            <el-icon v-if="!scanning" class="btn-icon">
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
                                    class="btn-clear"
                                    :disabled="!store.hasFiles"
                                >
                                    <el-icon class="btn-icon">
                                        <Delete />
                                    </el-icon>
                                    一键清空
                                </el-button>
                            </template>
                        </el-popconfirm>
                    </div>

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
                                    <el-icon class="file-icon" :size="16">
                                        <Document />
                                    </el-icon>
                                    <span class="file-name">{{ file.name }}</span>
                                </div>
                            </FileResultPopover>
                            <div class="file-item-right">
                                <el-tooltip content="预览报告" placement="top" :show-after="400">
                                    <el-button
                                        text
                                        size="small"
                                        :disabled="!store.isDone"
                                        @click="previewFile(index)"
                                    >
                                        <el-icon class="action-icon">
                                            <View />
                                        </el-icon>
                                    </el-button>
                                </el-tooltip>
                                <el-tooltip content="移除" placement="top" :show-after="400">
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
                                </el-tooltip>
                            </div>
                        </div>
                    </div>

                    <div
                        v-else-if="scanning"
                        class="empty-state scanning-state"
                    >
                        <el-icon
                            :size="40"
                            class="scanning-icon header-icon"
                        >
                            <Loading />
                        </el-icon>
                        <div class="scanning-title">正在扫描文件夹…</div>
                        <div class="scanning-desc">请稍候，正在查找 HTM 文件</div>
                    </div>

                    <div
                        v-else
                        class="empty-state"
                        @click="triggerFolderSelect"
                    >
                        <el-icon :size="48" class="empty-icon">
                            <FolderOpened />
                        </el-icon>
                        <div class="empty-title">点击选择数据文件夹</div>
                        <div class="empty-desc">支持递归扫描子目录中的 HTM 文件</div>
                    </div>

                    <div v-if="showProgress" class="progress-block">
                        <el-progress
                            :percentage="store.progressPercent"
                            :color="progressColor"
                            :stroke-width="14"
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
            <el-col :span="10" class="right-col">
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
                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <Folder />
                                </el-icon>
                                <span>保存路径</span>
                            </div>
                            <el-tooltip
                                :content="store.outputDir"
                                :disabled="!store.outputDir"
                                placement="top"
                                :show-after="500"
                            >
                                <el-input
                                    v-model="store.outputDir"
                                    placeholder="选择或输入保存路径"
                                    clearable
                                    @blur="onOutputDirBlur"
                                >
                                    <template #prefix>
                                        <el-icon :size="14">
                                            <Folder />
                                        </el-icon>
                                    </template>
                                    <template #append>
                                        <el-button @click="browseOutputDir">
                                            <el-icon class="btn-icon">
                                                <FolderOpened />
                                            </el-icon>
                                            浏览
                                        </el-button>
                                    </template>
                                </el-input>
                            </el-tooltip>
                        </div>

                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <Operation />
                                </el-icon>
                                <span>数据处理</span>
                            </div>
                            <div class="form-row">
                                <span class="form-label">峰值阈值</span>
                                <el-input-number
                                    v-model="store.processConfig.peakThreshold"
                                    :step="0.00001"
                                    :min="0"
                                    :max="4000"
                                    controls-position="right"
                                    class="form-input-number"
                                />
                            </div>
                        </div>

                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <PictureFilled />
                                </el-icon>
                                <span>图片设置</span>
                            </div>
                            <div class="form-grid">
                                <div class="form-row">
                                    <span class="form-label">宽度 (英寸)</span>
                                    <el-input-number
                                        v-model="store.reportConfig.picWidth"
                                        :step="0.1"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                        class="form-input-number"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">高度 (英寸)</span>
                                    <el-input-number
                                        v-model="store.reportConfig.picHeight"
                                        :step="0.1"
                                        :min="1"
                                        :max="30"
                                        controls-position="right"
                                        class="form-input-number"
                                    />
                                </div>
                            </div>
                        </div>

                        <div class="config-section">
                            <div class="section-label">
                                <el-icon :size="14">
                                    <Aim />
                                </el-icon>
                                <span>雷达图最小值</span>
                            </div>
                            <div class="form-grid">
                                <div class="form-row">
                                    <span class="form-label">载荷</span>
                                    <el-input-number
                                        v-model="store.reportConfig.loadPolarMin"
                                        :step="100"
                                        :min="0"
                                        controls-position="right"
                                        class="form-input-number"
                                    />
                                </div>
                                <div class="form-row">
                                    <span class="form-label">应力</span>
                                    <el-input-number
                                        v-model="store.reportConfig.pressPolarMin"
                                        :step="100"
                                        :min="0"
                                        controls-position="right"
                                        class="form-input-number"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="action-bar">
                        <el-button
                            type="primary"
                            size="large"
                            class="btn-parse"
                            :class="{ 'btn-parse--inactive': !canParse }"
                            :disabled="store.isProcessing"
                            :loading="store.isProcessing"
                            @click="startParse"
                        >
                            <el-icon v-if="!store.isProcessing" class="btn-icon">
                                <CaretRight />
                            </el-icon>
                            {{ parseButtonText }}
                        </el-button>
                    </div>
                </el-card>

            </el-col>
        </el-row>

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
    CaretRight,
    CircleCheckFilled,
    Delete,
    Loading,
    Aim,
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

const showProgress = computed(() => store.processStatus !== 'idle')

const scanning = ref(false)

const triggerFolderSelect = async (): Promise<void> => {
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

const previewFile = (index: number): void => {
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

function removeFile(index: number): void {
    store.files.splice(index, 1)
    if (store.files.length === 0) {
        store.clearFiles()
    }
}

function onOutputDirBlur(): void {
    // 后续可以校验路径是否存在
}

async function browseOutputDir(): Promise<void> {
    const result = await window.electronAPI.openDirectoryDialog({
        title: '选择保存路径',
    })

    if (!result.canceled && result.filePaths.length > 0) {
        store.outputDir = result.filePaths[0]!
    }
}

const canParse = computed(() => store.hasFiles && !!store.outputDir && !store.isProcessing)

const parseButtonText = computed(() => {
    if (store.isProcessing) return '解析中…'
    if (store.isDone) return '重新解析'
    return '开始解析'
})

function startParse(): void {
    if (store.files.length === 0) {
        ElMessage.warning('请先选择数据文件')
        return
    }
    if (!store.outputDir) {
        ElMessage.warning('请先设置保存路径')
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
.edge-stress-page {
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

.left-col {
    height: 100%;
}

.right-col {
    height: 100%;
}

.page-card {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    border-radius: 14px;
    border: 1px solid #ececef;
    box-shadow:
        0 1px 2px rgba(0, 0, 0, 0.04),
        0 4px 12px rgba(0, 0, 0, 0.04);
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.page-card:hover {
    box-shadow:
        0 1px 3px rgba(0, 0, 0, 0.06),
        0 8px 24px rgba(0, 0, 0, 0.06);
}

.page-card:hover {
    border-color: #dcdce0;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.page-card :deep(.el-card__header) {
    padding: 14px 18px;
    border-bottom: 1px solid #f0f0f3;
}

.page-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding: 16px 18px;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 28px;
}

.card-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.header-icon {
    color: #0071e3;
}

.card-title {
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
    letter-spacing: 0.2px;
}

.file-count-tag {
    padding: 0 12px !important;
    height: 26px;
}

.file-count-tag :deep(.el-tag__content) {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.file-select-buttons {
    display: flex;
    gap: 10px;
}

.btn-select {
    flex: 2;
    height: 38px;
    font-weight: 500;
    border-radius: 8px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    cursor: pointer;
}

.btn-select:hover:not(:disabled) {
    box-shadow: 0 2px 6px rgba(0, 113, 227, 0.25);
}

.btn-clear {
    flex: 1;
    height: 38px;
    border-radius: 8px;
    cursor: pointer;
}

.btn-icon {
    margin-right: 6px;
}

.file-list-container {
    border: 1px solid #ececef;
    border-radius: 10px;
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    margin-top: 14px;
    background: #fafafc;
}

.file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    transition: background-color 0.15s ease;
    cursor: pointer;
}

.file-item:hover {
    background-color: #f5f5f7;
}

.file-item + .file-item {
    border-top: 1px solid #f0f0f3;
}

.file-item-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
}

.file-icon {
    color: #0071e3;
    flex-shrink: 0;
}

.file-name {
    font-size: 13px;
    color: #1d1d1f;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.file-item-right {
    display: flex;
    align-items: center;
    gap: 0;
}

.file-item-right :deep(.el-button + .el-button) {
    margin-left: 0;
}

.action-icon {
    color: #0071e3;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 36px 16px;
    border: 2px dashed #e4e4e7;
    border-radius: 12px;
    margin-top: 14px;
    flex: 1;
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
    font-size: 14px;
    font-weight: 600;
    color: #1d1d1f;
    margin-top: 14px;
}

.empty-desc {
    font-size: 12px;
    color: #86868b;
    margin-top: 6px;
}

.scanning-state {
    border-color: #0071e3;
    border-style: dashed;
    background: rgba(0, 113, 227, 0.04);
    cursor: default;
}

.scanning-state:hover {
    background: rgba(0, 113, 227, 0.04);
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.scanning-icon {
    animation: spin 1.2s linear infinite;
}

.scanning-title {
    font-size: 14px;
    font-weight: 600;
    color: #0071e3;
    margin-top: 12px;
}

.scanning-desc {
    font-size: 12px;
    color: #86868b;
    margin-top: 4px;
}

.progress-block {
    margin-top: 14px;
    flex-shrink: 0;
}

.stage-message {
    margin-top: 6px;
    font-size: 12px;
    color: #86868b;
    text-align: center;
}

.config-form {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding-right: 2px;
}

.config-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px 14px;
    background: #f8f8fa;
    border: 1px solid #efeff2;
    border-radius: 10px;
    transition: border-color 0.2s ease, background 0.2s ease;
}

.config-section:hover {
    border-color: #e2e2e7;
    background: #f5f5f8;
}

.config-section:focus-within {
    border-color: #0071e3;
    background: #fff;
    box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.08);
}

.section-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 700;
    color: #6e6e73;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}

.section-label .el-icon {
    color: #0071e3;
}

.form-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.form-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.form-grid .form-row {
    gap: 10px;
}

.form-label {
    flex-shrink: 0;
    width: 80px;
    font-size: 13px;
    color: #424245;
}

.form-input-number {
    flex: 1;
    width: auto !important;
}

.action-bar {
    margin-top: 14px;
    flex-shrink: 0;
    padding-top: 14px;
    border-top: 1px dashed #ececef;
}

.btn-parse {
    width: 100%;
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

.btn-parse:hover:not(:disabled) {
    box-shadow: 0 6px 16px rgba(0, 113, 227, 0.35);
    transform: translateY(-1px);
}

.btn-parse:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 6px rgba(0, 113, 227, 0.3);
}

.btn-parse--inactive {
    opacity: 0.55;
    box-shadow: none;
}

.btn-parse--inactive:hover {
    opacity: 0.72;
    box-shadow: none !important;
    transform: none !important;
}

:deep(.el-input__wrapper) {
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 0 0 1px #e5e5ea inset, 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    transition: box-shadow 0.2s ease, background 0.2s ease;
}

:deep(.el-input__wrapper:hover) {
    box-shadow: 0 0 0 1px #c7c7cc inset, 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}

:deep(.el-input.is-focus .el-input__wrapper),
:deep(.el-input__wrapper:focus-within) {
    box-shadow:
        0 0 0 1px var(--el-color-primary) inset,
        0 0 0 3px rgba(0, 113, 227, 0.15) !important;
}

/* 让带 append 的输入框看起来是一个整体（无割裂） */
:deep(.el-input-group--append .el-input__wrapper) {
    border-top-right-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    box-shadow: 0 0 0 1px #e5e5ea inset !important;
}

:deep(.el-input-group--append .el-input__wrapper:hover) {
    box-shadow: 0 0 0 1px #c7c7cc inset !important;
}

:deep(.el-input-group--append.is-focus .el-input__wrapper),
:deep(.el-input-group--append .el-input__wrapper:focus-within) {
    box-shadow:
        0 0 0 1px var(--el-color-primary) inset,
        0 0 0 3px rgba(0, 113, 227, 0.15) !important;
}

:deep(.el-input-group__append) {
    background: #ffffff !important;
    border-top-right-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
    box-shadow: 0 0 0 1px #e5e5ea inset !important;
    border-left: 1px solid #ececef !important;
    color: #424245 !important;
    padding: 0 !important;
    overflow: hidden;
    transition: box-shadow 0.2s ease, background 0.2s ease;
}

:deep(.el-input-group__append .el-button) {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 100% !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    color: inherit !important;
    padding: 0 14px !important;
    font-size: 13px;
    font-weight: 500;
    line-height: 1;
    transition: background 0.15s ease, color 0.15s ease;
}

:deep(.el-input-group__append .el-button .btn-icon) {
    margin-right: 0;
}

:deep(.el-input-group__append .el-button:hover) {
    background: rgba(0, 113, 227, 0.08) !important;
    color: var(--el-color-primary) !important;
}

:deep(.el-input-group__append .el-button:active) {
    background: rgba(0, 113, 227, 0.16) !important;
}

:deep(.el-input-number) {
    line-height: normal;
}

:deep(.el-input-number .el-input__inner) {
    text-align: left;
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
}

:deep(.el-input-number.is-controls-right .el-input-number__increase),
:deep(.el-input-number.is-controls-right .el-input-number__decrease) {
    background: transparent;
    border-color: transparent;
    color: #86868b;
    transition: color 0.15s ease, background 0.15s ease;
}

:deep(.el-input-number.is-controls-right .el-input-number__increase:hover),
:deep(.el-input-number.is-controls-right .el-input-number__decrease:hover) {
    color: var(--el-color-primary);
    background: rgba(0, 113, 227, 0.08);
}

:deep(.el-input-number.is-controls-right .el-input-number__increase:active),
:deep(.el-input-number.is-controls-right .el-input-number__decrease:active) {
    background: rgba(0, 113, 227, 0.16);
}
</style>
