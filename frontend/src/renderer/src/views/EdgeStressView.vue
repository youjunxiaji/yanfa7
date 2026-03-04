<template>
    <div>
        <el-row :gutter="20">
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
                            @click="triggerFileSelect('htm')"
                        >
                            <el-icon style="margin-right: 6px;">
                                <FolderOpened />
                            </el-icon>
                            选择 HTM 文件
                        </el-button>
                        <el-button
                            type="primary"
                            plain
                            disabled
                            style="flex: 1;"
                            @click="triggerFileSelect('xlsx')"
                        >
                            <el-icon style="margin-right: 6px;">
                                <FolderOpened />
                            </el-icon>
                            选择 Excel 文件
                        </el-button>
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

        
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
} from '@element-plus/icons-vue'
import { ElMessage} from 'element-plus'
import { useEdgeStressStore, type FileInfo } from '@renderer/stores/edgeStress'
import { parseWithProgress, type WsMessage } from '@renderer/api/edgeStress'
import FileResultPopover from '@renderer/components/FileResultPopover.vue'

const store = useEdgeStressStore()

const progressColor = computed(() => {
    if (store.isDone) return '#34c759'
    if (store.processStatus === 'error') return '#ff3b30'
    return '#0071e3'
})

// ========== 文件选择 ==========
const triggerFileSelect = async (type: 'htm' | 'xlsx') => {
    const filters = type === 'htm'
        ? [{ name: 'HTM 文件', extensions: ['htm', 'html'] }]
        : [{ name: 'Excel 文件', extensions: ['xlsx', 'xls'] }]

    const result = await window.electronAPI.openFileDialog({
        filters,
        title: `选择${type === 'htm' ? 'HTM' : 'Excel'}文件`,
    })

    if (result.canceled || result.filePaths.length === 0) return

    const newFiles: FileInfo[] = result.filePaths.map((fp, i) => {
        const name = fp.split(/[\\/]/).pop() || fp
        return { name, path: fp, size: result.fileSizes?.[i] ?? 0 }
    })

    store.setFiles(newFiles, type)
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
.equal-height-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}

.equal-height-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
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
