<template>
    <div class="page">
        <PageHeader>
            <n-popconfirm
                :show="saveConfirmVisible"
                :show-icon="false"
                positive-text="保存"
                negative-text="取消"
                :positive-button-props="{ loading: saving }"
                @update:show="handleSaveConfirmShow"
                @positive-click="saveConfig"
            >
                <template #trigger>
                    <n-button size="small" :loading="saving">
                        <template #icon><Save :size="15" /></template>
                        保存配置
                    </n-button>
                </template>
                <div class="save-confirm">
                    <div>存为历史记录「{{ store.historyName }}」？</div>
                    <div class="save-confirm-note">
                        项目名取输出目录的文件夹名，你存过同名的会被覆盖
                    </div>
                </div>
            </n-popconfirm>
            <n-button size="small" :disabled="store.isBusy" @click="historyVisible = true">
                <template #icon><History :size="15" /></template>
                历史记录
            </n-button>
        </PageHeader>
        <div class="tool-body">
            <section class="param-pane">
                <div class="param-scroll">
                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">数据</span>
                            <n-popconfirm
                                v-if="store.loaded"
                                :show-icon="false"
                                positive-text="清空"
                                negative-text="取消"
                                @positive-click="clearData"
                            >
                                <template #trigger>
                                    <button class="link-btn is-danger" :disabled="store.isBusy">
                                        清空
                                    </button>
                                </template>
                                清空已加载的数据？参数和区间表保留，再缩减要重新加载。
                            </n-popconfirm>
                        </div>
                        <div class="field">
                            <span class="field-label">载荷文件夹</span>
                            <n-input-group>
                                <n-input
                                    v-model:value="store.loadDir"
                                    placeholder="选择或输入路径"
                                    clearable
                                    :title="store.loadDir"
                                    :disabled="store.isBusy"
                                    @change="handleLoadDirChange"
                                    @clear="handleLoadDirChange('')"
                                >
                                    <template #prefix
                                        ><Folder class="input-prefix" :size="15"
                                    /></template>
                                </n-input>
                                <n-button :disabled="store.isBusy" @click="browseLoadDir">
                                    浏览
                                </n-button>
                            </n-input-group>
                        </div>
                        <div class="field">
                            <span class="field-label">频次表</span>
                            <n-input-group>
                                <n-input
                                    v-model:value="store.freqTablePath"
                                    placeholder="选择或输入路径"
                                    clearable
                                    :title="store.freqTablePath"
                                    :disabled="store.isBusy"
                                    @change="handleFreqTableChange"
                                >
                                    <template #prefix
                                        ><FileSpreadsheet class="input-prefix" :size="15"
                                    /></template>
                                </n-input>
                                <n-button :disabled="store.isBusy" @click="browseFreqTable">
                                    浏览
                                </n-button>
                            </n-input-group>
                        </div>
                        <div class="field">
                            <span class="field-label">输出目录</span>
                            <n-input-group>
                                <n-input
                                    v-model:value="store.outputDir"
                                    placeholder="选择或输入路径"
                                    clearable
                                    :title="store.outputDir"
                                    :disabled="store.isBusy"
                                    @change="handleOutputDirChange"
                                >
                                    <template #prefix
                                        ><Folder class="input-prefix" :size="15"
                                    /></template>
                                </n-input>
                                <n-button :disabled="store.isBusy" @click="browseOutputDir">
                                    浏览
                                </n-button>
                            </n-input-group>
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">文件格式</span>
                            <button
                                class="link-btn"
                                :disabled="store.isBusy"
                                @click="formatVisible = true"
                            >
                                设置
                            </button>
                        </div>
                        <div class="summary-list">
                            <div class="field">
                                <span class="field-label">力转换系数</span>
                                <span
                                    class="summary-value num"
                                    :class="{ 'is-error': store.unitForce <= 0 }"
                                >
                                    {{ store.unitForce }}
                                </span>
                            </div>
                            <div class="field">
                                <span class="field-label">力矩转换系数</span>
                                <span
                                    class="summary-value num"
                                    :class="{ 'is-error': store.unitMoment <= 0 }"
                                >
                                    {{ store.unitMoment }}
                                </span>
                            </div>
                            <div class="field">
                                <span class="field-label">转速转换系数</span>
                                <span
                                    class="summary-value num"
                                    :class="{ 'is-error': store.unitSpeed <= 0 }"
                                >
                                    {{ store.unitSpeed }}
                                </span>
                            </div>
                            <div class="field">
                                <span class="field-label">列对应</span>
                                <span
                                    class="summary-value"
                                    :class="{ 'is-error': formatError }"
                                    :title="formatSummary"
                                >
                                    {{ formatSummary }}
                                </span>
                            </div>
                        </div>
                        <n-button
                            block
                            :disabled="!store.canLoad"
                            :loading="store.isLoading"
                            @click="store.startLoad()"
                        >
                            <template #icon><FolderInput :size="16" /></template>
                            {{ loadButtonText }}
                        </n-button>
                        <div class="section-note num" :class="{ 'is-warning': store.isStale }">
                            {{ loadNote }}
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">缩减参数</span>
                            <button
                                class="link-btn"
                                :disabled="store.isBusy"
                                @click="reduceVisible = true"
                            >
                                设置
                            </button>
                        </div>
                        <div class="summary-list">
                            <div class="field">
                                <span class="field-label">Romax 坐标</span>
                                <div class="axis-tags" :class="{ 'is-error': !!store.axisIssue }">
                                    <span
                                        v-for="mapping in store.axisMapping"
                                        :key="mapping.romax"
                                        class="axis-tag"
                                    >
                                        {{ mapping.romax }}
                                        <span class="axis-arrow">←</span>
                                        {{ mapping.origin }}
                                    </span>
                                </div>
                            </div>
                            <div class="field">
                                <span class="field-label">扭矩分量</span>
                                <span class="summary-value">{{ torqueSummary }}</span>
                            </div>
                            <div class="field">
                                <span class="field-label">转换系数</span>
                                <span class="summary-value num">{{ store.slope }}</span>
                            </div>
                            <div class="field">
                                <span class="field-label">温度</span>
                                <span class="summary-value num">{{ store.temperature }} °C</span>
                            </div>
                            <div class="field">
                                <span class="field-label">占比阈值</span>
                                <span class="summary-value num">{{ store.tol }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="param-footer">
                    <n-button
                        type="primary"
                        size="large"
                        block
                        :disabled="!store.canReduce"
                        :loading="store.isReducing"
                        @click="store.startReduce()"
                    >
                        <template #icon><Play :size="15" /></template>
                        {{ store.isReducing ? '缩减中…' : '载荷缩减' }}
                    </n-button>
                    <p v-if="store.reduceHint" class="action-hint">
                        <Info :size="13" />
                        {{ store.reduceHint }}
                    </p>
                </div>
            </section>

            <section class="result-pane">
                <div class="result-toolbar">
                    <span class="toolbar-title">区间划分</span>
                    <span v-if="store.loaded" class="count-pill">
                        {{ store.participating.length }} 个分量
                    </span>
                    <span class="toolbar-spacer" />
                    <span v-if="cellsNote" class="toolbar-note num">{{ cellsNote }}</span>
                </div>
                <StatusStrip
                    v-if="strip"
                    :status="strip.status"
                    :text="strip.text"
                    :meta="strip.meta"
                    :percent="store.percent"
                />
                <div class="result-body">
                    <EmptyState
                        v-if="store.isLoading"
                        busy
                        title="正在加载数据…"
                        desc="读取全部 txt 和频次表，统计各分量的时间占比分布"
                    />
                    <div v-else-if="store.loaded" class="interval-view">
                        <SimpleLoadIntervalTable />
                        <SimpleLoadHistogram />
                    </div>
                    <EmptyState
                        v-else-if="store.previewing"
                        busy
                        title="正在读取载荷文件夹…"
                        desc="看第一个 txt 的开头几行，认出每一列"
                    />
                    <EmptyState
                        v-else-if="!store.preview"
                        :icon="store.previewError ? TriangleAlert : FolderOpen"
                        :title="store.previewError ? '没能读取载荷文件夹' : '选择载荷文件夹'"
                        :desc="
                            store.previewError ||
                            '连同子文件夹里的 txt 一起读，先看第一个文件的开头，认出每一列是什么'
                        "
                        @click="browseLoadDir"
                    >
                        <n-button type="primary" @click="browseLoadDir">
                            <template #icon><FolderOpen :size="16" /></template>
                            选择文件夹
                        </n-button>
                    </EmptyState>
                    <EmptyState
                        v-else
                        :icon="ChartColumnBig"
                        title="加载数据后划分区间"
                        :desc="store.loadHint || '加载后在这里看各分量的时间占比分布，填区间边界'"
                        :clickable="store.canLoad"
                        @click="store.startLoad()"
                    >
                        <n-button
                            type="primary"
                            :disabled="!store.canLoad"
                            @click="store.startLoad()"
                        >
                            <template #icon><FolderInput :size="16" /></template>
                            加载数据
                        </n-button>
                        <n-button @click="formatVisible = true">文件格式</n-button>
                    </EmptyState>
                </div>
            </section>
        </div>

        <n-modal
            v-model:show="formatVisible"
            preset="card"
            title="文件格式"
            :style="{ width: '680px' }"
            :bordered="false"
            :mask-closable="false"
        >
            <!-- 单位换算只有一行，放在上面；列对应的表长，放下面 -->
            <div class="modal-scroll">
                <div class="modal-block">
                    <span class="section-title">单位换算</span>
                    <div class="unit-grid">
                        <div class="unit-item">
                            <span class="field-label">力转换系数</span>
                            <NumberInput v-model="store.unitForce" :min="0" prefix="÷" />
                        </div>
                        <div class="unit-item">
                            <span class="field-label">力矩转换系数</span>
                            <NumberInput v-model="store.unitMoment" :min="0" prefix="÷" />
                        </div>
                        <div class="unit-item">
                            <span class="field-label">转速转换系数</span>
                            <NumberInput
                                v-model="store.unitSpeed"
                                :step="0.1"
                                :min="0"
                                prefix="×"
                            />
                        </div>
                    </div>
                    <div class="section-note">
                        力、力矩除以它，转速乘以它，换成 KN、KNm、rpm；文件里是 N、N·m 时力和力矩填
                        1000，是 rad/s 时转速填 9.5493
                    </div>
                </div>
                <div class="modal-block">
                    <span class="section-title">列对应</span>
                    <SimpleLoadColumnMap />
                </div>
            </div>
            <template #footer>
                <div class="modal-actions">
                    <n-button type="primary" @click="formatVisible = false">完成</n-button>
                </div>
            </template>
        </n-modal>

        <n-modal
            v-model:show="reduceVisible"
            preset="card"
            title="缩减参数"
            :style="{ width: '560px' }"
            :bordered="false"
            :mask-closable="false"
        >
            <div class="modal-scroll modal-form">
                <div class="field">
                    <span class="field-label">Romax 坐标</span>
                    <div class="axis-grid">
                        <n-input-group
                            v-for="(mapping, index) in store.axisMapping"
                            :key="mapping.romax"
                        >
                            <n-input-group-label>{{ mapping.romax }} ←</n-input-group-label>
                            <n-select
                                :value="mapping.origin"
                                :options="AXIS_OPTIONS"
                                :status="store.axisIssue ? 'error' : undefined"
                                @update:value="(value: string) => setAxis(index, value)"
                            />
                        </n-input-group>
                    </div>
                    <div class="field-hint" :class="{ 'is-error': !!store.axisIssue }">
                        {{ store.axisIssue || 'Romax 的轴取载荷文件的哪个轴，带负号是取反' }}
                    </div>
                </div>
                <div class="field">
                    <span class="field-label">扭矩分量</span>
                    <n-checkbox v-model:checked="store.keepTorque">
                        {{ store.torqueComponent }} 也参与分组
                    </n-checkbox>
                    <div class="field-hint">
                        绕 Romax z 轴的力矩，默认不参与；打开后 Romax 载荷表多一行 Mz[KNm]
                    </div>
                </div>
                <div class="field">
                    <span class="field-label">转换系数</span>
                    <NumberInput v-model="store.slope" :step="0.01" :min="0" />
                    <div class="field-hint">S-N 曲线斜率，幂等效变换的指数</div>
                </div>
                <div class="field">
                    <span class="field-label">温度</span>
                    <NumberInput v-model="store.temperature" suffix="°C" />
                    <div class="field-hint">写进 Romax 的工况表</div>
                </div>
                <div class="field">
                    <span class="field-label">占比阈值</span>
                    <NumberInput v-model="store.tol" :step="0.0001" :min="0" />
                    <div class="field-hint">时间占比不超过它的格子丢掉</div>
                </div>
            </div>
            <template #footer>
                <div class="modal-actions">
                    <n-button type="primary" @click="reduceVisible = false">完成</n-button>
                </div>
            </template>
        </n-modal>

        <SimpleLoadHistory v-model:show="historyVisible" />
    </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
    NButton,
    NCheckbox,
    NInput,
    NInputGroup,
    NInputGroupLabel,
    NModal,
    NPopconfirm,
    NSelect,
    useMessage,
    type SelectOption
} from 'naive-ui'
import {
    ChartColumnBig,
    FileSpreadsheet,
    Folder,
    FolderInput,
    FolderOpen,
    History,
    Info,
    Play,
    Save,
    TriangleAlert
} from '@lucide/vue'
import { saveHistory } from '@renderer/api/simpleLoad'
import { SOURCE_AXES } from '@renderer/constants/simpleLoad'
import { useAccountStore } from '@renderer/stores/account'
import { useSimpleLoadStore } from '@renderer/stores/simpleLoad'
import PageHeader from '@renderer/components/PageHeader.vue'
import EmptyState from '@renderer/components/EmptyState.vue'
import StatusStrip from '@renderer/components/StatusStrip.vue'
import NumberInput from '@renderer/components/NumberInput.vue'
import SimpleLoadColumnMap from '@renderer/components/SimpleLoadColumnMap.vue'
import SimpleLoadIntervalTable from '@renderer/components/SimpleLoadIntervalTable.vue'
import SimpleLoadHistogram from '@renderer/components/SimpleLoadHistogram.vue'
import SimpleLoadHistory from '@renderer/components/SimpleLoadHistory.vue'

const AXIS_OPTIONS: SelectOption[] = SOURCE_AXES.map((axis) => ({ label: axis, value: axis }))

const store = useSimpleLoadStore()
const account = useAccountStore()
const message = useMessage()

const formatVisible = ref(false)
const reduceVisible = ref(false)
const historyVisible = ref(false)

// ========== 保存配置：存成网页版的一条历史记录 ==========
const saving = ref(false)
const saveConfirmVisible = ref(false)
// 点「保存配置」时还没登录：登录完接着弹确认框，登录框关掉还没登录就算了
let saveAfterLogin = false

// 没选输出目录先提示，没登录先登录，都齐了才弹确认框
const handleSaveConfirmShow = (show: boolean): void => {
    if (!show || saving.value) {
        saveConfirmVisible.value = false
    } else if (store.saveHint) {
        message.warning(store.saveHint)
    } else if (!account.user) {
        saveAfterLogin = true
        account.loginVisible = true
    } else {
        saveConfirmVisible.value = true
    }
}

watch(
    () => account.loginVisible,
    (visible) => {
        if (visible || !saveAfterLogin) return
        saveAfterLogin = false
        if (account.user) handleSaveConfirmShow(true)
    }
)

// 确认框等存完再关，存的时候「保存」按钮转圈
const saveConfig = async (): Promise<void> => {
    if (saving.value) return
    const config = store.historyConfig
    saving.value = true
    try {
        const { projName } = await account.withAccess((access) => saveHistory(access, config))
        message.success(`已存为历史记录「${projName}」`)
    } catch (err) {
        message.error(`保存失败：${(err as Error).message}`, { duration: 5000 })
    } finally {
        saving.value = false
    }
}

const formatRows = (n: number): string => (n >= 10000 ? `${Math.round(n / 10000)} 万` : String(n))

const formatCount = (n: number): string => n.toLocaleString('en-US')

// Windows 资源管理器「复制为路径」带双引号，粘贴进来先去掉
const trimPath = (value: string): string => value.trim().replace(/^"(.*)"$/, '$1')

// ========== 数据来源与输出 ==========
const browseLoadDir = async (): Promise<void> => {
    if (store.isBusy) return
    const { canceled, rootDir } = await window.electronAPI.openDir({ title: '选择载荷文件夹' })
    if (canceled || !rootDir) return
    store.loadDir = rootDir
    store.previewFolder()
}

const handleLoadDirChange = (value: string): void => {
    store.loadDir = trimPath(value)
    store.previewFolder()
}

const browseFreqTable = async (): Promise<void> => {
    const result = await window.electronAPI.openFileDialog({
        title: '选择频次表',
        filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }]
    })
    if (!result.canceled && result.filePaths.length > 0) {
        store.freqTablePath = result.filePaths[0]!
    }
}

const handleFreqTableChange = (value: string): void => {
    store.freqTablePath = trimPath(value)
}

const browseOutputDir = async (): Promise<void> => {
    const result = await window.electronAPI.openDirectoryDialog({ title: '选择输出目录' })
    if (!result.canceled && result.filePaths.length > 0) {
        store.outputDir = result.filePaths[0]!
    }
}

const handleOutputDirChange = (value: string): void => {
    store.outputDir = trimPath(value)
}

const clearData = async (): Promise<void> => {
    try {
        await store.clearData()
    } catch (err) {
        message.error(`清空失败：${(err as Error).message}`, { duration: 5000 })
    }
}

// ========== 摘要：详细设置在两个弹窗里 ==========
const formatError = computed(
    () =>
        !store.previewing &&
        (!!store.previewError ||
            (!!store.preview && (!store.columns.length || !!store.columnIssue)))
)

const formatSummary = computed(() => {
    if (store.previewing) return '正在读取…'
    if (store.previewError) return store.previewError
    if (!store.preview) return '先选载荷文件夹'
    if (!store.columns.length) return '没找到数据行，检查跳过的行数'
    if (store.columnIssue) return store.columnIssue
    const mapped = store.columns.filter((column) => column !== null).length
    return `跳过 ${store.skipRows} 行 · 对上 ${mapped} 列`
})

const torqueSummary = computed(
    () => `${store.torqueComponent} ${store.keepTorque ? '参与分组' : '不参与分组'}`
)

const setAxis = (index: number, value: string): void => {
    const origin = SOURCE_AXES.find((axis) => axis === value)
    const mapping = store.axisMapping[index]
    if (origin && mapping) mapping.origin = origin
}

// ========== 加载 ==========
const loadButtonText = computed(() => {
    if (store.isLoading) return '加载中…'
    return store.loaded ? '重新加载' : '加载数据'
})

const loadNote = computed(() => {
    if (store.isLoading) return '读取全部 txt 和频次表，进度见右侧'
    if (store.loaded && store.isStale) return '载荷文件夹、频次表或文件格式改过，要重新加载'
    if (store.loaded) {
        return `已加载 ${store.loaded.fileCount} 个文件 · ${formatRows(store.loaded.rowCount)} 行`
    }
    return store.loadHint || '加载后在右侧划分区间'
})

// ========== 结果区 ==========
const cellsNote = computed(() => {
    if (!store.loaded) return ''
    const total = `总格子数 ${formatCount(store.totalCells)}`
    const result = store.currentReduceResult
    if (!result) return total
    return `${total} · 空格子数 ${formatCount(Math.max(store.totalCells - result.cellCount, 0))}`
})

const strip = computed(() => {
    if (store.status === 'processing') {
        return {
            status: 'processing' as const,
            text: store.stage,
            meta: `${Math.round(store.percent)}%`
        }
    }
    if (store.status === 'done') {
        if (store.task === 'load' && store.loaded) {
            return {
                status: 'done' as const,
                text: `加载完成：${store.loaded.fileCount} 个文件，${formatRows(store.loaded.rowCount)} 行`,
                meta: undefined
            }
        }
        if (store.task === 'reduce' && store.reduceResult) {
            return {
                status: 'done' as const,
                text: `缩减完成：非空格子 ${formatCount(store.reduceResult.cellCount)} 个，结果写入 ${store.outputDir}`,
                meta: undefined
            }
        }
    }
    if (store.status === 'error') {
        return {
            status: 'error' as const,
            text: `${store.task === 'load' ? '加载' : '缩减'}失败：${store.error}`,
            meta: undefined
        }
    }
    return null
})

// 加载、缩减跑完时弹一句；离开页面期间跑完的，回来看进度条带
watch(
    () => store.status,
    (now, before) => {
        if (before !== 'processing') return
        if (now === 'done') {
            message.success(store.task === 'load' ? '加载完成' : '载荷缩减完成')
        } else if (now === 'error') {
            const action = store.task === 'load' ? '加载' : '缩减'
            message.error(`${action}失败：${store.error}`, { duration: 5000 })
        }
    }
)
</script>

<style scoped>
.input-prefix {
    color: var(--text-3);
}

/* 保存配置的确认框：文件夹名很长时折行，不把弹层撑宽 */
.save-confirm {
    max-width: 300px;
    overflow-wrap: anywhere;
}

.save-confirm-note {
    margin-top: 2px;
    font-size: 12px;
    color: var(--text-3);
}

.section-note.is-warning {
    color: var(--warning);
}

/* 参数栏里只放摘要，详细设置在弹窗里 */
.summary-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.summary-value {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.summary-value.is-error,
.field-hint.is-error {
    color: var(--danger);
}

/* 坐标映射一对一个小标签，箭头淡一些，三对之间分得开 */
.axis-tags {
    display: flex;
    gap: 6px;
    min-width: 0;
}

.axis-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 22px;
    padding: 0 7px;
    font-size: 12px;
    color: var(--text-1);
    white-space: nowrap;
    background: var(--muted);
    border-radius: 4px;
}

.axis-arrow {
    color: var(--text-3);
}

.axis-tags.is-error .axis-tag {
    color: var(--danger);
    background: var(--danger-soft);
}

.interval-view {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    padding: 16px 20px 20px;
    overflow-y: auto;
}

/* ========== 弹窗 ========== */
/* 内容区限高，窗口矮时在里面滚，弹窗不超出窗口 */
.modal-scroll {
    max-height: calc(100vh - 220px);
    overflow-y: auto;
}

.modal-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.modal-block {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.modal-block + .modal-block {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--divider);
}

.axis-grid,
.unit-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
}

.unit-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
