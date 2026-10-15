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
                    <div>存为历史记录「{{ store.historyLabel }}」？</div>
                    <div class="save-confirm-note">
                        按 Gear unit、Wind turbine、Load spectrum 三项存，你存过同样三项的会被覆盖
                    </div>
                </div>
            </n-popconfirm>
            <n-button size="small" @click="historyVisible = true">
                <template #icon><History :size="15" /></template>
                历史记录
            </n-button>
        </PageHeader>
        <div class="tool-body">
            <section class="param-pane">
                <div class="param-scroll">
                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">项目</span>
                            <span class="section-meta">历史记录按这三项存</span>
                        </div>
                        <div class="field wide-field">
                            <span class="field-label">Gear unit</span>
                            <n-input v-model:value="store.form.gearUnit" placeholder="" />
                        </div>
                        <div class="field wide-field">
                            <span class="field-label">Wind turbine</span>
                            <n-input v-model:value="store.form.windTurbine" placeholder="" />
                        </div>
                        <div class="field wide-field">
                            <span class="field-label">Load spectrum</span>
                            <n-input v-model:value="store.form.loadSpectrum" placeholder="" />
                        </div>
                    </div>

                    <div class="param-section">
                        <div class="section-head">
                            <span class="section-title">工况</span>
                        </div>
                        <n-button block @click="pasteVisible = true">
                            <template #icon><ClipboardPaste :size="16" /></template>
                            {{ store.conditions.length ? '重新粘贴工况' : '粘贴工况' }}
                        </n-button>
                        <div class="section-note num">{{ conditionNote }}</div>
                        <div class="field wide-field">
                            <span class="field-label">{{ InputParam.POWER }}</span>
                            <n-input-number
                                :value="power"
                                :show-button="false"
                                placeholder=""
                                @update:value="setPower"
                            />
                            <div class="field-hint">
                                不参与计算，原样传给后面各级；和网页版一样，不填不算
                            </div>
                        </div>
                    </div>

                    <GearLoadStageEditor />
                </div>

                <div class="param-footer">
                    <n-button
                        type="primary"
                        size="large"
                        block
                        :disabled="!!exportHint"
                        :loading="store.exporting"
                        @click="exportExcel"
                    >
                        <template #icon><FileSpreadsheet :size="16" /></template>
                        {{ store.exporting ? '导出中…' : '导出 Excel' }}
                    </n-button>
                    <p v-if="exportHint" class="action-hint">
                        <Info :size="13" />
                        {{ exportHint }}
                    </p>
                </div>
            </section>

            <section class="result-pane">
                <div class="result-toolbar">
                    <span class="toolbar-title">计算结果</span>
                    <span v-if="store.computedCount" class="count-pill">
                        {{ store.computedCount }} / {{ store.stageCount }} 级
                    </span>
                    <span class="toolbar-spacer" />
                    <span
                        v-if="store.pendingNote"
                        class="toolbar-note is-warning"
                        :title="store.pendingNote"
                    >
                        <TriangleAlert :size="13" />
                        {{ store.pendingNote }}
                    </span>
                    <n-select
                        v-if="store.conditions.length"
                        :value="store.selected"
                        :options="conditionOptions"
                        size="small"
                        class="condition-select"
                        @update:value="(value: number) => store.selectCondition(value)"
                    />
                </div>
                <div class="result-body">
                    <EmptyState
                        v-if="!store.conditions.length"
                        :icon="ClipboardPaste"
                        title="暂无工况"
                        desc="从 Excel 复制扭矩、转速两列，粘贴进来后，改哪个参数结果都跟着重算"
                        @click="pasteVisible = true"
                    >
                        <n-button @click="pasteVisible = true">
                            <template #icon><ClipboardPaste :size="16" /></template>
                            粘贴工况
                        </n-button>
                    </EmptyState>
                    <EmptyState
                        v-else-if="store.missing(0).length"
                        :icon="Cog"
                        title="Stage I 还有参数没填"
                        :desc="missingNote"
                        :clickable="false"
                    />
                    <EmptyState
                        v-else-if="store.error"
                        :icon="TriangleAlert"
                        title="没能算出来"
                        :desc="store.error"
                        :clickable="false"
                    />
                    <GearLoadResultTable v-else-if="store.computedCount" />
                    <EmptyState
                        v-else-if="store.calculating || waiting"
                        busy
                        title="正在计算…"
                        desc="从 Stage I 起逐级算到最后一级"
                    />
                    <EmptyState
                        v-else
                        :icon="Cog"
                        title="没算出结果"
                        desc="检查选中的这组工况：扭矩、转速都要有"
                        :clickable="false"
                    />
                </div>
            </section>
        </div>

        <GearLoadConditionDialog v-model:show="pasteVisible" />
        <GearLoadHistory v-model:show="historyVisible" @select="handleHistorySelect" />
    </div>
</template>

<script setup lang="ts">
// 齿轮载荷：左边填项目、工况和各级参数，右边是选中那组工况的各级结果，参数一改就重算；
// 主按钮把全部工况导出成 Excel。参数名、结果的名称照网页版的英文原名
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
    NButton,
    NInput,
    NInputNumber,
    NPopconfirm,
    NSelect,
    useMessage,
    type SelectOption
} from 'naive-ui'
import {
    ClipboardPaste,
    Cog,
    FileSpreadsheet,
    History,
    Info,
    Save,
    TriangleAlert
} from '@lucide/vue'
import { fetchHistory, saveHistory, type HistoryItem } from '@renderer/api/gearLoad'
import { InputParam } from '@renderer/constants/gearLoad'
import { useAccountStore } from '@renderer/stores/account'
import { useGearLoadStore } from '@renderer/stores/gearLoad'
import PageHeader from '@renderer/components/PageHeader.vue'
import EmptyState from '@renderer/components/EmptyState.vue'
import GearLoadStageEditor from '@renderer/components/GearLoadStageEditor.vue'
import GearLoadResultTable from '@renderer/components/GearLoadResultTable.vue'
import GearLoadConditionDialog from '@renderer/components/GearLoadConditionDialog.vue'
import GearLoadHistory from '@renderer/components/GearLoadHistory.vue'

// 参数停手 300 毫秒后再算，连着改只算最后一次
const CALC_DELAY_MS = 300

// Windows 文件名里不能有的字符
const UNSAFE_FILENAME = /[\\/:*?"<>|]/g

const store = useGearLoadStore()
const account = useAccountStore()
const message = useMessage()

const pasteVisible = ref(false)
const historyVisible = ref(false)

// ========== 工况与功率 ==========
const conditionNote = computed(() => {
    const count = store.conditions.length
    if (!count) return '从 Excel 复制扭矩、转速两列后粘贴'
    const torques = store.conditions.map((item) => Number(item.torque))
    return `${count} 组 · 扭矩 ${Math.min(...torques)} ～ ${Math.max(...torques)} kNm`
})

const conditionOptions = computed<SelectOption[]>(() =>
    store.conditions.map((item, index) => ({
        label: `#${index + 1} · T ${item.torque} kNm · n ${item.rpm} rpm`,
        value: index
    }))
)

const power = computed(() => {
    const text = store.cell(InputParam.POWER, 'stageI').trim()
    const value = Number(text)
    return text && Number.isFinite(value) ? value : null
})

const setPower = (value: number | null): void => {
    store.setCell(InputParam.POWER, 'stageI', value === null ? '' : String(value))
}

// ========== 计算：参数一改就重算 ==========
let calcTimer: ReturnType<typeof setTimeout> | undefined
// 改了参数、还没开始算：结果区先显示「正在计算」
const waiting = ref(false)

watch(
    () => store.calcKey,
    () => {
        clearTimeout(calcTimer)
        waiting.value = true
        calcTimer = setTimeout(() => {
            waiting.value = false
            store.calculate()
        }, CALC_DELAY_MS)
    },
    { immediate: true }
)

const missingNote = computed(() => {
    const missing = store.missing(0)
    const names = missing.slice(0, 3).join('、')
    return missing.length > 3 ? `还差 ${names} 等 ${missing.length} 项` : `还差 ${names}`
})

// ========== 导出 Excel ==========
const exportHint = computed(() => {
    if (store.calcHint) return store.calcHint
    return store.error ? '计算出错了，原因见右边' : ''
})

const defaultFileName = (): string => {
    const parts = [store.form.gearUnit, store.form.windTurbine, store.form.loadSpectrum]
        .map((part) => part.trim().replace(UNSAFE_FILENAME, '_'))
        .filter(Boolean)
    return `${parts.length ? parts.join('-') : '齿轮载荷'}.xlsx`
}

const exportExcel = async (): Promise<void> => {
    if (exportHint.value || store.exporting) return
    const { canceled, filePath } = await window.electronAPI.saveFileDialog({
        title: '导出 Excel',
        defaultPath: defaultFileName(),
        filters: [{ name: 'Excel', extensions: ['xlsx'] }]
    })
    if (canceled || !filePath) return
    const path = /\.xlsx$/i.test(filePath) ? filePath : `${filePath}.xlsx`
    try {
        await store.exportExcel(path)
        message.success(`已导出：${path}`)
    } catch (err) {
        message.error(`导出失败：${(err as Error).message}`, { duration: 5000 })
    }
}

// ========== 保存配置：存成网页版的一条历史记录 ==========
const saving = ref(false)
const saveConfirmVisible = ref(false)
// 点「保存配置」时还没登录：登录完接着弹确认框，登录框关掉还没登录就算了
let saveAfterLogin = false

// 三项没填全先提示，没登录先登录，都齐了才弹确认框
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
    const params = store.historyParams
    saving.value = true
    try {
        const { created } = await account.withAccess((access) => saveHistory(access, params))
        const label = `「${store.historyLabel}」`
        message.success(created ? `已存为历史记录${label}` : `已覆盖历史记录${label}`)
    } catch (err) {
        message.error(`保存失败：${(err as Error).message}`, { duration: 5000 })
    } finally {
        saving.value = false
        saveConfirmVisible.value = false
    }
}

// ========== 历史记录 ==========
const handleHistorySelect = async (item: HistoryItem): Promise<void> => {
    try {
        const detail = await account.withAccess((access) => fetchHistory(access, item.id))
        store.applyHistory(detail)
        message.success(`已回填「${item.label}」`)
    } catch (err) {
        message.error(`获取历史记录失败：${(err as Error).message}`, { duration: 5000 })
    }
}

// 同网页版：Ctrl+S 存、Ctrl+F 查历史记录
const handleKeydown = (event: KeyboardEvent): void => {
    if (!event.ctrlKey && !event.metaKey) return
    if (event.key === 's') {
        event.preventDefault()
        handleSaveConfirmShow(true)
    } else if (event.key === 'f') {
        event.preventDefault()
        historyVisible.value = true
    }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
    clearTimeout(calcTimer)
})
</script>

<style scoped>
/* 项目、功率的英文标签比默认的标签列宽 */
.wide-field {
    grid-template-columns: 104px minmax(0, 1fr);
}

.toolbar-note.is-warning {
    min-width: 0;
    overflow: hidden;
    color: var(--warning);
    text-overflow: ellipsis;
}

.condition-select {
    flex-shrink: 0;
    width: 250px;
}

/* 保存配置的确认框：三项很长时折行，不把弹层撑宽 */
.save-confirm {
    max-width: 300px;
    overflow-wrap: anywhere;
}

.save-confirm-note {
    margin-top: 2px;
    font-size: 12px;
    color: var(--text-3);
}
</style>
