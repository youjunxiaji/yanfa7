<template>
    <div class="page">
        <PageHeader />
        <div class="tool-body">
            <section class="param-pane">
                <div class="param-scroll">
                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">数据文件</span>
                            <n-popconfirm
                                v-if="store.hasFiles"
                                :show-icon="false"
                                positive-text="清空"
                                negative-text="取消"
                                @positive-click="store.clearFiles()"
                            >
                                <template #trigger>
                                    <button
                                        class="link-btn is-danger"
                                        :disabled="store.isProcessing"
                                    >
                                        清空
                                    </button>
                                </template>
                                确定清空所有文件吗？
                            </n-popconfirm>
                        </div>
                        <n-button
                            block
                            :loading="scanning"
                            :disabled="store.isProcessing"
                            @click="triggerFolderSelect"
                        >
                            <template #icon><FolderOpen :size="16" /></template>
                            {{ selectButtonText }}
                        </n-button>
                        <div v-if="store.hasFiles" class="section-note num">
                            已选 {{ store.files.length }} 个文件，共 {{ formatBytes(totalSize) }}
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">输出目录</span>
                        </div>
                        <n-input-group>
                            <n-input
                                v-model:value="store.outputDir"
                                placeholder="选择或输入保存路径"
                                clearable
                                :title="store.outputDir"
                            >
                                <template #prefix
                                    ><Folder class="input-prefix" :size="15"
                                /></template>
                            </n-input>
                            <n-button @click="browseOutputDir">浏览</n-button>
                        </n-input-group>
                        <div class="section-note">报告写入这个目录下的 res-output 文件夹</div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">处理参数</span>
                        </div>
                        <div class="field">
                            <span class="field-label">峰值阈值</span>
                            <div class="field-control">
                                <NumberInput
                                    v-model="store.processConfig.peakThreshold"
                                    :step="0.00001"
                                    :min="0"
                                    :max="4000"
                                />
                            </div>
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">报告图片</span>
                        </div>
                        <div class="field">
                            <span class="field-label">图片尺寸</span>
                            <div class="field-control">
                                <NumberInput
                                    v-model="store.reportConfig.picWidth"
                                    :step="0.1"
                                    :min="1"
                                    :max="30"
                                    suffix="in"
                                />
                                <span class="pair-sep">×</span>
                                <NumberInput
                                    v-model="store.reportConfig.picHeight"
                                    :step="0.1"
                                    :min="1"
                                    :max="30"
                                    suffix="in"
                                />
                            </div>
                        </div>
                        <div class="field">
                            <span class="field-label">雷达图最小值</span>
                            <div class="field-control">
                                <NumberInput
                                    v-model="store.reportConfig.loadPolarMin"
                                    :step="100"
                                    :min="0"
                                    prefix="载荷"
                                />
                                <NumberInput
                                    v-model="store.reportConfig.pressPolarMin"
                                    :step="100"
                                    :min="0"
                                    prefix="应力"
                                />
                            </div>
                            <div class="field-hint">0 表示自动</div>
                        </div>
                    </div>
                </div>

                <div class="param-footer">
                    <n-button
                        type="primary"
                        size="large"
                        block
                        :disabled="!canParse"
                        :loading="store.isProcessing"
                        @click="startParse"
                    >
                        <template #icon><Play :size="15" /></template>
                        {{ parseButtonText }}
                    </n-button>
                    <p v-if="parseHint" class="action-hint">
                        <Info :size="13" />
                        {{ parseHint }}
                    </p>
                </div>
            </section>

            <section class="result-pane">
                <div class="result-toolbar">
                    <span class="toolbar-title">文件列表</span>
                    <span v-if="store.hasFiles" class="count-pill">{{ store.files.length }}</span>
                    <span class="toolbar-spacer" />
                    <span v-if="store.isDone" class="toolbar-note">悬停文件名查看缩略图</span>
                </div>
                <StatusStrip
                    v-if="strip"
                    :status="strip.status"
                    :text="strip.text"
                    :meta="strip.meta"
                    :percent="store.progressPercent"
                />
                <div class="result-body">
                    <EmptyState
                        v-if="scanning && !store.hasFiles"
                        busy
                        title="正在扫描文件夹…"
                        desc="查找 HTM 文件"
                    />
                    <EmptyState
                        v-else-if="!store.hasFiles"
                        :icon="FolderOpen"
                        title="选择数据文件夹"
                        desc="递归扫描子目录中的 HTM 文件，可以多次添加，重复的文件会自动去掉"
                        @click="triggerFolderSelect"
                    >
                        <n-button type="primary" @click="triggerFolderSelect">
                            <template #icon><FolderOpen :size="16" /></template>
                            选择文件夹
                        </n-button>
                    </EmptyState>
                    <div v-else class="table-wrap">
                        <n-data-table
                            :columns="columns"
                            :data="rows"
                            :row-key="rowKey"
                            size="small"
                            :bordered="false"
                            flex-height
                        />
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, h, ref, type Component, type VNode } from 'vue'
import {
    NButton,
    NDataTable,
    NEllipsis,
    NInput,
    NInputGroup,
    NPopconfirm,
    NTooltip,
    useMessage,
    type DataTableColumns
} from 'naive-ui'
import {
    CircleAlert,
    CircleCheck,
    CircleX,
    Clock,
    Eye,
    FileText,
    Folder,
    FolderOpen,
    Info,
    LoaderCircle,
    Play,
    X
} from '@lucide/vue'
import { useEdgeStressStore, type FileInfo, type FileResult } from '@renderer/stores/edgeStress'
import { parseWithProgress, type WsMessage } from '@renderer/api/edgeStress'
import PageHeader from '@renderer/components/PageHeader.vue'
import EmptyState from '@renderer/components/EmptyState.vue'
import StatusStrip from '@renderer/components/StatusStrip.vue'
import NumberInput from '@renderer/components/NumberInput.vue'
import FileResultPopover from '@renderer/components/FileResultPopover.vue'
import { FileStatus } from '@renderer/constants/ui'

interface FileRow extends FileInfo, FileResult {
    status: FileStatus
}

const STATUS_META: Record<FileStatus, { icon: Component; tip: string }> = {
    [FileStatus.IDLE]: { icon: FileText, tip: '未解析' },
    [FileStatus.QUEUED]: { icon: Clock, tip: '排队中' },
    [FileStatus.PROCESSING]: { icon: LoaderCircle, tip: '处理中' },
    [FileStatus.DONE]: { icon: CircleCheck, tip: '已完成' },
    [FileStatus.SKIPPED]: { icon: CircleAlert, tip: '已跳过' },
    [FileStatus.ERROR]: { icon: CircleX, tip: '处理时出错' }
}

const store = useEdgeStressStore()
const message = useMessage()

const scanning = ref(false)

const fileStemOf = (name: string): string => name.replace(/\.[^.]+$/, '')

const formatBytes = (n: number): string =>
    n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`

const totalSize = computed(() => store.files.reduce((sum, f) => sum + f.size, 0))

const selectButtonText = computed(() => {
    if (scanning.value) return '扫描中…'
    return store.hasFiles ? '继续添加文件夹' : '选择文件夹'
})

// ========== 单文件状态：由最近一次解析的进度和逐个推来的文件结果推出来 ==========
const NO_RESULT: FileResult = { columns: [], previewItems: [], reason: '' }

const statusOf = (file: FileInfo, result?: FileResult): FileStatus => {
    if (result) return result.reason ? FileStatus.SKIPPED : FileStatus.DONE
    const index = store.runPaths.indexOf(file.path)
    if (index < 0) return FileStatus.IDLE
    // 还没结果的文件：后端正在处理的那个标处理中，其余排队；整批中途出错时，正在处理的那个标出错
    const isCurrent = store.processingName !== '' && index === store.progressCurrent
    if (store.processStatus === 'processing') {
        return isCurrent ? FileStatus.PROCESSING : FileStatus.QUEUED
    }
    return store.processStatus === 'error' && isCurrent ? FileStatus.ERROR : FileStatus.IDLE
}

const rows = computed<FileRow[]>(() =>
    store.files.map((file) => {
        const result = store.fileResults[file.path]
        return { ...file, ...(result ?? NO_RESULT), status: statusOf(file, result) }
    })
)

const rowKey = (row: FileRow): string => row.path

// ========== 文件表 ==========
const renderStatus = (row: FileRow): VNode => {
    const meta = STATUS_META[row.status]
    return h(
        NTooltip,
        { delay: 200 },
        {
            trigger: () =>
                h('span', { class: ['status-cell', `st-${row.status}`] }, [
                    h(meta.icon, {
                        size: 15,
                        class: row.status === FileStatus.PROCESSING ? 'spin' : undefined
                    })
                ]),
            default: () => meta.tip
        }
    )
}

// 跳过原因写在文件名下面一行：报错可能很长，一行放不下就截断，截断了才悬停出全文
const renderName = (row: FileRow): VNode =>
    h(
        FileResultPopover,
        { fileName: row.name, previewItems: row.previewItems },
        {
            default: () =>
                h('div', { class: 'file-cell' }, [
                    h('span', { class: 'file-name', title: row.path }, row.name),
                    row.reason
                        ? h(
                              NEllipsis,
                              {
                                  class: 'file-reason',
                                  tooltip: { delay: 200, contentClass: 'long-tip' }
                              },
                              { default: () => row.reason }
                          )
                        : null
                ])
        }
    )

const iconButton = (
    icon: Component,
    tip: string,
    options: { disabled: boolean; danger?: boolean; onClick: () => void }
): VNode =>
    h(
        NTooltip,
        { delay: 300, disabled: options.disabled },
        {
            trigger: () =>
                h(
                    'button',
                    {
                        class: ['icon-btn', { 'is-danger': options.danger }],
                        disabled: options.disabled,
                        onClick: options.onClick
                    },
                    [h(icon, { size: 15 })]
                ),
            default: () => tip
        }
    )

const columns: DataTableColumns<FileRow> = [
    { key: 'status', title: '', width: 44, align: 'center', render: renderStatus },
    { key: 'name', title: '文件名', render: renderName },
    {
        key: 'size',
        title: '大小',
        width: 96,
        align: 'right',
        render: (row) => h('span', { class: 'num cell-muted' }, formatBytes(row.size))
    },
    {
        key: 'columnCount',
        title: '列数',
        width: 72,
        align: 'center',
        render: (row) =>
            row.status === FileStatus.DONE
                ? h('span', { class: 'num' }, String(row.columns.length))
                : h('span', { class: 'cell-muted' }, '—')
    },
    {
        key: 'actions',
        title: '',
        width: 84,
        align: 'right',
        render: (row) =>
            h('div', { class: 'row-actions' }, [
                // 预览读后端的数据集缓存，整批处理完才写入，所以要等整批完成
                iconButton(Eye, '预览报告', {
                    disabled: !store.isDone || row.status !== FileStatus.DONE,
                    onClick: () => previewFile(row)
                }),
                iconButton(X, '移除', {
                    disabled: store.isProcessing,
                    danger: true,
                    onClick: () => removeFile(row)
                })
            ])
    }
]

// ========== 数据来源与输出 ==========
const triggerFolderSelect = async (): Promise<void> => {
    if (scanning.value || store.isProcessing) return
    const { canceled, rootDir } = await window.electronAPI.openDir({
        title: '选择包含 HTM 文件的文件夹'
    })
    if (canceled || !rootDir) return

    scanning.value = true
    try {
        const { filePaths, fileSizes } = await window.electronAPI.scanDir({
            rootDir,
            extensions: ['htm']
        })

        if (filePaths.length === 0) {
            message.info('所选文件夹中未找到 HTM 文件')
            return
        }

        const newFiles: FileInfo[] = filePaths.map((fp, i) => {
            const name = fp.split(/[\\/]/).pop() || fp
            return { name, path: fp, size: fileSizes[i] ?? 0 }
        })

        store.setFiles(newFiles, 'htm')
        message.success(`已扫描到 ${newFiles.length} 个 HTM 文件`)
    } finally {
        scanning.value = false
    }
}

const browseOutputDir = async (): Promise<void> => {
    const result = await window.electronAPI.openDirectoryDialog({
        title: '选择保存路径'
    })

    if (!result.canceled && result.filePaths.length > 0) {
        store.outputDir = result.filePaths[0]!
    }
}

const previewFile = (row: FileRow): void => {
    const fileStem = fileStemOf(row.name)
    window.electronAPI.openPreviewWindow({
        fileStem,
        outputDir: store.outputDir,
        columns: row.columns.join(','),
        title: `报告预览 - ${fileStem}`
    })
}

const removeFile = (row: FileRow): void => {
    const index = store.files.findIndex((f) => f.path === row.path)
    if (index >= 0) store.files.splice(index, 1)
    if (store.files.length === 0) store.clearFiles()
}

// ========== 解析 ==========
const canParse = computed(() => store.hasFiles && !!store.outputDir && !store.isProcessing)

const parseHint = computed(() => {
    if (store.isProcessing || store.isDone) return ''
    if (!store.hasFiles) return '请先选择数据文件'
    if (!store.outputDir) return '请先设置保存路径'
    return ''
})

const parseButtonText = computed(() => {
    if (store.isProcessing) return '解析中…'
    if (store.isDone) return '重新解析'
    return '开始解析'
})

const strip = computed(() => {
    if (store.processStatus === 'processing') {
        const started = store.processingName !== ''
        return {
            status: 'processing' as const,
            text: started ? `正在处理 ${store.processingName}` : store.stageMessage,
            meta: started
                ? `${store.progressCurrent + 1} / ${store.progressTotal} · ${store.progressPercent}%`
                : undefined
        }
    }
    if (store.processStatus === 'done') {
        const skipped = Object.values(store.fileResults).filter((r) => r.reason).length
        const skippedText = skipped ? `，跳过 ${skipped} 个` : ''
        return {
            status: 'done' as const,
            text: `解析完成，已生成 ${store.generatedCount} 个文件${skippedText}`,
            meta: undefined
        }
    }
    if (store.processStatus === 'error') {
        return {
            status: 'error' as const,
            text: `解析失败：${store.processError}`,
            meta: undefined
        }
    }
    return null
})

const startParse = (): void => {
    if (!canParse.value) return

    const filePaths = store.files.map((f) => f.path)
    store.runPaths = filePaths
    store.processingName = ''
    store.generatedCount = 0
    store.fileResults = {}
    store.setProcessStatus('processing')
    store.updateProgress(0, filePaths.length)
    store.stageMessage = '正在连接解析服务…'

    parseWithProgress(
        filePaths,
        store.fileType,
        store.processConfig.peakThreshold,
        store.outputDir,
        {
            picWidth: store.reportConfig.picWidth,
            picHeight: store.reportConfig.picHeight,
            loadPolarMin: store.reportConfig.loadPolarMin,
            pressPolarMin: store.reportConfig.pressPolarMin
        },
        (msg: WsMessage) => {
            if (msg.type === 'progress') {
                store.updateProgress(msg.current, msg.total)
                store.processingName = msg.filename
            } else if (msg.type === 'fileDone') {
                store.setFileResult(msg.index, {
                    columns: msg.columns,
                    previewItems: msg.previewItems,
                    reason: ''
                })
            } else if (msg.type === 'fileSkipped') {
                store.setFileResult(msg.index, {
                    columns: [],
                    previewItems: [],
                    reason: msg.reason
                })
            } else if (msg.type === 'done') {
                store.updateProgress(store.progressTotal, store.progressTotal)
                store.setProcessStatus('done')
                store.stageMessage = ''
                store.generatedCount = msg.generatedFiles.length
                message.success(`解析完成！已生成 ${msg.generatedFiles.length} 个文件`)
            } else if (msg.type === 'error') {
                store.setProcessStatus('error', msg.message)
                store.stageMessage = ''
                message.error(`解析失败：${msg.message}`, { duration: 5000 })
            }
        }
    )
}
</script>

<style scoped>
.input-prefix {
    color: var(--text-3);
}

/* 文件表的单元格由 render 函数生成，不带本组件的 scoped 标记，要用 :deep */
.result-body :deep(.status-cell) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    vertical-align: middle;
}

.result-body :deep(.st-idle),
.result-body :deep(.st-queued) {
    color: var(--text-3);
}

.result-body :deep(.st-processing) {
    color: var(--accent);
}

.result-body :deep(.st-done) {
    color: var(--success);
}

.result-body :deep(.st-skipped) {
    color: var(--warning);
}

.result-body :deep(.st-error) {
    color: var(--danger);
}

/* 有跳过原因时分两行：文件名在上，原因在下，各自一行放不下就截断 */
.result-body :deep(.file-cell) {
    display: flex;
    flex-direction: column;
}

.result-body :deep(.file-name) {
    overflow: hidden;
    color: var(--text-1);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.result-body :deep(.file-reason) {
    font-size: 12px;
    color: var(--warning);
}

.result-body :deep(.cell-muted) {
    color: var(--text-3);
}

.result-body :deep(.row-actions) {
    display: flex;
    justify-content: flex-end;
    gap: 2px;
}
</style>
