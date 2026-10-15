<template>
    <div class="page">
        <PageHeader />
        <div class="gear-scroll">
            <section class="gear-card">
                <div class="card-head">
                    <span class="card-title">基础设置</span>
                    <span class="toolbar-spacer" />
                    <span class="shortcut">
                        <Save :size="13" />
                        <kbd>{{ modKey }}</kbd>
                        <kbd>S</kbd>
                        存储
                    </span>
                    <span class="shortcut">
                        <Search :size="13" />
                        <kbd>{{ modKey }}</kbd>
                        <kbd>F</kbd>
                        查找
                    </span>
                </div>
                <div class="basic-form">
                    <label class="basic-field">
                        <span class="field-label">Gear unit:</span>
                        <n-input v-model:value="formData.gearUnit" placeholder="" />
                    </label>
                    <label class="basic-field">
                        <span class="field-label">Wind turbine:</span>
                        <n-input v-model:value="formData.windTurbine" placeholder="" />
                    </label>
                    <label class="basic-field">
                        <span class="field-label">Load spectrum:</span>
                        <n-input v-model:value="formData.loadSpectrum" placeholder="" />
                    </label>
                </div>
            </section>

            <section class="gear-card">
                <div class="card-head">
                    <span class="card-title">Input data</span>
                    <span class="toolbar-spacer" />
                    <n-button size="small" :loading="exporting" @click="saveExcel">
                        <template #icon><FileSpreadsheet :size="15" /></template>
                        保存为Excel
                    </n-button>
                    <n-button
                        size="small"
                        type="primary"
                        :loading="calculating"
                        @click="sendDataToBackend"
                    >
                        <template #icon><Play :size="15" /></template>
                        计算结果
                    </n-button>
                </div>
                <div class="table-scroll">
                    <table class="input-table">
                        <thead>
                            <tr>
                                <th class="col-param" />
                                <th v-for="stage in GEAR_STAGES" :key="stage">
                                    {{ STAGE_TITLES[stage] }}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(row, rowIndex) in inputData" :key="rowIndex">
                                <td class="col-param">
                                    <button
                                        v-if="isConditionParam(row)"
                                        class="param-link"
                                        @click="showTable"
                                    >
                                        {{ row.parameter }}
                                    </button>
                                    <template v-else>{{ row.parameter }}</template>
                                </td>
                                <td v-for="stage in GEAR_STAGES" :key="stage">
                                    <n-select
                                        v-if="row.parameter === InputParam.ARRANGEMENT"
                                        :value="row[stage]"
                                        :options="ARRANGEMENT_OPTIONS"
                                        size="small"
                                        @update:value="
                                            (value: string) => changeArrangement(row, stage, value)
                                        "
                                    />
                                    <n-select
                                        v-else-if="row.parameter === InputParam.HELIX_HAND"
                                        :value="row[stage]"
                                        :options="HAND_OPTIONS"
                                        size="small"
                                        @update:value="
                                            (value: string) => changeHand(row, stage, value)
                                        "
                                    />
                                    <template v-else-if="stage === 'stageI'">
                                        <n-select
                                            v-if="row.parameter === InputParam.TORQUE"
                                            :value="conditionValue('torque', row.stageI)"
                                            :options="torqueOptions"
                                            size="small"
                                            @update:value="selectChanged"
                                        />
                                        <n-select
                                            v-else-if="row.parameter === InputParam.SPEED"
                                            :value="conditionValue('rpm', row.stageI)"
                                            :options="rpmOptions"
                                            size="small"
                                            @update:value="selectChanged"
                                        />
                                        <n-input
                                            v-else-if="
                                                row.parameter === InputParam.POWER || row.editable
                                            "
                                            v-model:value="row.stageI"
                                            size="small"
                                            placeholder=""
                                        />
                                    </template>
                                    <n-input
                                        v-else-if="isChained(row)"
                                        :value="row[stage]"
                                        size="small"
                                        placeholder=""
                                        readonly
                                    />
                                    <n-input
                                        v-else-if="row.editable"
                                        v-model:value="row[stage]"
                                        size="small"
                                        placeholder=""
                                    />
                                    <template v-else>{{ row[stage] }}</template>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="gear-card">
                <div class="card-head">
                    <span class="card-title">Gear loads</span>
                </div>
                <n-data-table
                    size="small"
                    :bordered="false"
                    :columns="gearLoadColumns"
                    :data="gearLoadRows"
                    :row-key="rowKey"
                    :scroll-x="TABLE_WIDTH"
                />
            </section>

            <section class="gear-card">
                <div class="card-head">
                    <span class="card-title">Speed of components</span>
                </div>
                <n-data-table
                    size="small"
                    :bordered="false"
                    :columns="speedColumns"
                    :data="speedRows"
                    :row-key="rowKey"
                    :scroll-x="TABLE_WIDTH"
                />
            </section>

            <section class="gear-card" :class="{ 'is-collapsed': !show }">
                <div class="card-head">
                    <span class="card-title">
                        Equivalent diameter - Input data for modelling planet wheel and pinions
                    </span>
                    <span class="toolbar-spacer" />
                    <button class="icon-btn" :class="{ 'is-open': show }" @click="show = !show">
                        <ChevronRight :size="16" />
                    </button>
                </div>
                <n-collapse-transition :show="show">
                    <n-data-table
                        size="small"
                        :bordered="false"
                        :columns="diameterColumns"
                        :data="diameterRows"
                        :row-key="rowKey"
                        :scroll-x="TABLE_WIDTH"
                    />
                </n-collapse-transition>
            </section>
        </div>

        <n-modal
            v-model:show="dialogVisible"
            preset="card"
            title="编辑多内容"
            :style="{ width: '560px' }"
            :bordered="false"
            :mask-closable="false"
        >
            <div class="condition-head">
                <span>扭矩T(kNm)</span>
                <span>转速n(RPM)</span>
            </div>
            <div class="condition-list">
                <div v-for="(row, index) in dialogTableData" :key="index" class="condition-row">
                    <n-input
                        :ref="(el) => setInputRef(`torque_${index}`, el)"
                        v-model:value="row.torque"
                        size="small"
                        placeholder=""
                        :input-props="{ onPaste: (event) => handlePaste(event, 'torque') }"
                        @keydown.enter.prevent="handleEnterKey(index, 'torque')"
                    />
                    <n-input
                        :ref="(el) => setInputRef(`rpm_${index}`, el)"
                        v-model:value="row.rpm"
                        size="small"
                        placeholder=""
                        :input-props="{ onPaste: (event) => handlePaste(event, 'rpm') }"
                        @keydown.enter.prevent="handleEnterKey(index, 'rpm')"
                    />
                </div>
            </div>
            <p class="condition-note">
                从 Excel
                复制一列，点进扭矩或转速的任一格粘贴，整列从第一行填起；回车跳到下一行，最后一行回车加一行
            </p>
            <template #footer>
                <div class="modal-actions">
                    <n-button @click="resetDialogData">重置</n-button>
                    <n-button type="primary" @click="checkDialogData">确定</n-button>
                </div>
            </template>
        </n-modal>

        <GearLoadHistory v-model:show="historyVisible" @select="handleHistorySelect" />
    </div>
</template>

<script setup lang="ts">
// 齿轮载荷：照搬网页版（tmb_web_v1 的 gearLoadsView.vue）的页面和交互，输入表、多工况、计算、
// 保存为 Excel、Ctrl+S 存 / Ctrl+F 查历史记录都和网页版一样；网页版下载的 Excel 这边改成选位置保存
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import {
    NButton,
    NCollapseTransition,
    NDataTable,
    NInput,
    NModal,
    NSelect,
    useMessage,
    type DataTableColumns,
    type InputInst,
    type SelectOption
} from 'naive-ui'
import { ChevronRight, FileSpreadsheet, Play, Save, Search } from '@lucide/vue'
import {
    calculateGearLoads,
    exportGearLoads,
    fetchHistory,
    saveHistory,
    type ConditionRow,
    type HistoryForm,
    type HistoryItem,
    type InputRow,
    type StageResult,
    type StageValue
} from '@renderer/api/gearLoad'
import {
    CHAINED_PARAMS,
    DIAMETER_ROWS,
    GEAR_LOAD_ROWS,
    GEAR_STAGES,
    GearArrangement,
    HelixHand,
    InputParam,
    NEXT_STAGE,
    SPEED_ROWS,
    STAGE_TITLES,
    type GearStage
} from '@renderer/constants/gearLoad'
import { useAccountStore } from '@renderer/stores/account'
import PageHeader from '@renderer/components/PageHeader.vue'
import GearLoadHistory from '@renderer/components/GearLoadHistory.vue'

type ConditionField = keyof ConditionRow
// 结果表的一行带上行号：按行号取后端结果里的那一格，也当表格的 row-key
type GearLoadRow = (typeof GEAR_LOAD_ROWS)[number] & { index: number }
type SymbolRow = (typeof SPEED_ROWS)[number] & { index: number }

const ARRANGEMENT_OPTIONS: SelectOption[] = Object.values(GearArrangement).map((value) => ({
    label: value,
    value
}))
const HAND_OPTIONS: SelectOption[] = Object.values(HelixHand).map((value) => ({
    label: value,
    value
}))

// 同网页版：Stage I、II 改布置，Stage I 改旋向，马上重算；其他级改了要点「计算结果」
const RECALC_ON_ARRANGEMENT: GearStage[] = ['stageI', 'stageII']
const RECALC_ON_HAND: GearStage[] = ['stageI']

// 结果表撑开的宽度，窗口窄时表格自己横向滚动
const TABLE_WIDTH = 820

const gearLoadRows: GearLoadRow[] = GEAR_LOAD_ROWS.map((row, index) => ({ ...row, index }))
const speedRows: SymbolRow[] = SPEED_ROWS.map((row, index) => ({ ...row, index }))
const diameterRows: SymbolRow[] = DIAMETER_ROWS.map((row, index) => ({ ...row, index }))

const rowKey = (row: { index: number }): number => row.index

const message = useMessage()
const account = useAccountStore()
const modKey = window.electron.process.platform === 'darwin' ? '⌘' : 'Ctrl'

// 同网页版：数值转成字符串，空串、没算的格子留空
const display = (value: StageValue | undefined): string => value?.toString() || ''

// ========== 基础设置与输入表 ==========
const formData = ref<HistoryForm>({ gearUnit: '', windTurbine: '', loadSpectrum: '' })

const defaultValue = (parameter: InputParam): string => {
    if (parameter === InputParam.ARRANGEMENT) return GearArrangement.PLANETARY
    if (parameter === InputParam.HELIX_HAND) return HelixHand.LEFT
    return ''
}

// 输入表初始的样子同网页版：布置默认 Planetary、旋向默认 L，其余空着
const createInputData = (): InputRow[] =>
    Object.values(InputParam).map((parameter) => {
        const value = defaultValue(parameter)
        return {
            parameter,
            stageI: value,
            stageII: value,
            stageIII: value,
            stageIIII: value,
            // 布置和旋向是下拉框，其余是输入框
            editable: parameter !== InputParam.ARRANGEMENT && parameter !== InputParam.HELIX_HAND
        }
    })

const inputData = ref<InputRow[]>(createInputData())

// 各级最近一次算出的结果；这次没算到的级留着上次的，同网页版
const results = ref<Partial<Record<GearStage, StageResult>>>({})

// 多工况点了「确定」后的扭矩、转速，Stage I 的扭矩、转速从这里选
const selectedData = ref<ConditionRow[]>([])

const findRow = (parameter: InputParam): InputRow | undefined =>
    inputData.value.find((row) => row.parameter === parameter)

const setStageI = (parameter: InputParam, value: string): void => {
    const row = findRow(parameter)
    if (row) row.stageI = value
}

const isConditionParam = (row: InputRow): boolean =>
    row.parameter === InputParam.TORQUE || row.parameter === InputParam.SPEED

// 二级以后的功率、扭矩、转速只读，由上一级的结果填
const isChained = (row: InputRow): boolean =>
    CHAINED_PARAMS.some((parameter) => parameter === row.parameter)

// ========== 计算 ==========
const calculating = ref(false)

const sendDataToBackend = async (): Promise<void> => {
    calculating.value = true
    try {
        const response = await calculateGearLoads(inputData.value)
        for (const stage of GEAR_STAGES) {
            const result = response[stage]
            if (!result) continue
            results.value[stage] = result
            const next = NEXT_STAGE[stage]
            if (!next) continue
            for (const row of inputData.value) {
                const index = CHAINED_PARAMS.findIndex((parameter) => parameter === row.parameter)
                if (index >= 0) row[next] = display(result.input_data[index])
            }
        }
    } catch (err) {
        message.error(`计算失败：${(err as Error).message}`, { duration: 5000 })
    } finally {
        calculating.value = false
    }
}

const changeArrangement = (row: InputRow, stage: GearStage, value: string): void => {
    row[stage] = value
    if (RECALC_ON_ARRANGEMENT.includes(stage)) sendDataToBackend()
}

const changeHand = (row: InputRow, stage: GearStage, value: string): void => {
    row[stage] = value
    if (RECALC_ON_HAND.includes(stage)) sendDataToBackend()
}

// ========== Stage I 的扭矩、转速：从多工况里选一组 ==========
// 网页版的下拉框绑扭矩、转速的值；这里绑工况的序号（#0、#1……），值相同的工况也分得开
const conditionOptions = (field: ConditionField): SelectOption[] =>
    selectedData.value.map((item, index) => ({ label: item[field], value: `#${index}` }))

const torqueOptions = computed(() => conditionOptions('torque'))
const rpmOptions = computed(() => conditionOptions('rpm'))

// 显示第一个值对得上的工况；对不上的值（如历史记录里多工况是空的）照样显示，n-select 没有这个选项时显示值本身
const conditionValue = (field: ConditionField, value: string): string | null => {
    const index = selectedData.value.findIndex((item) => item[field] === value)
    return index >= 0 ? `#${index}` : value || null
}

// 选了哪一组，扭矩、转速都换成这一组的，再重算
const selectChanged = (value: string): void => {
    const item = selectedData.value[Number(value.slice(1))]
    if (!item) return
    setStageI(InputParam.TORQUE, item.torque)
    setStageI(InputParam.SPEED, item.rpm)
    sendDataToBackend()
}

// ========== 多工况弹窗 ==========
const dialogVisible = ref(false)
const dialogTableData = ref<ConditionRow[]>([{ torque: '', rpm: '' }])
const inputRefs: Record<string, InputInst | null> = {}

const setInputRef = (key: string, el: unknown): void => {
    inputRefs[key] = el as InputInst | null
}

const showTable = (): void => {
    dialogVisible.value = true
}

// 回车跳到下一行的同一列；已经是最后一行就加一行
const handleEnterKey = (currentIndex: number, currentField: ConditionField): void => {
    const nextKey = `${currentField}_${currentIndex + 1}`
    if (currentIndex >= dialogTableData.value.length - 1) {
        dialogTableData.value.push({ torque: '', rpm: '' })
    }
    nextTick(() => inputRefs[nextKey]?.focus())
}

// 同网页版：只收一列，从第一行起填，行数跟着粘贴的走；不带数字的行跳过
const handlePaste = (event: ClipboardEvent, column: ConditionField): void => {
    event.preventDefault()
    const pastedText = event.clipboardData?.getData('text')
    if (!pastedText) return
    const rows = pastedText.split('\n').filter((row) => /\d/.test(row))
    if (pastedText.split('\t').length !== 1) {
        message.error('粘贴的数据格式不正确，请按列粘贴')
        return
    }
    dialogTableData.value = rows.map((value, index) => ({
        ...(dialogTableData.value[index] ?? { torque: '', rpm: '' }),
        [column]: value.trim().replace(/\r$/, '')
    }))
}

// 扭矩、转速都填了的行才算一组；Stage I 先取第一组
const checkDialogData = (): void => {
    const filteredData = dialogTableData.value.filter((row) => row.torque !== '' && row.rpm !== '')
    selectedData.value = filteredData
    const first = filteredData[0]
    if (!first) {
        message.error('数据格式不正确，请检查')
        return
    }
    setStageI(InputParam.TORQUE, first.torque)
    setStageI(InputParam.SPEED, first.rpm)
    dialogVisible.value = false
}

const resetDialogData = (): void => {
    dialogTableData.value = [{ torque: '', rpm: '' }]
}

// ========== 结果表 ==========
const show = ref(false)

const isPlanetaryStageI = computed(
    () => findRow(InputParam.ARRANGEMENT)?.stageI === GearArrangement.PLANETARY
)

// 4 级的结果列：第 index 行取这一级结果里的第 index 格，没算的级留空
const stageColumns = <T extends { index: number }>(
    pick: (result: StageResult) => StageValue[]
): DataTableColumns<T> =>
    GEAR_STAGES.map((stage) => ({
        key: stage,
        title: STAGE_TITLES[stage],
        render: (row: T): string => {
            const result = results.value[stage]
            return result ? display(pick(result)[row.index]) : ''
        }
    }))

// 同网页版：符号按 Stage I 是行星级还是平行级取
const symbolColumn: DataTableColumns<SymbolRow>[number] = {
    key: 'symbol',
    title: '',
    width: 100,
    render: (row) => (isPlanetaryStageI.value ? row.symbol[0] : row.symbol[1]) ?? ''
}

const gearLoadColumns: DataTableColumns<GearLoadRow> = [
    { key: 'parameter', title: '', width: 260 },
    { key: 'symbol', title: '', width: 100 },
    { key: 'unit', title: '', width: 80 },
    ...stageColumns<GearLoadRow>((result) => result.gear_loads)
]

const speedColumns: DataTableColumns<SymbolRow> = [
    { key: 'parameter', title: '', width: 340 },
    symbolColumn,
    ...stageColumns<SymbolRow>((result) => result.speed_of_components)
]

const diameterColumns: DataTableColumns<SymbolRow> = [
    { key: 'parameter', title: '', width: 340 },
    symbolColumn,
    ...stageColumns<SymbolRow>((result) => result.equivalent_diameter)
]

// ========== 保存为 Excel ==========
const exporting = ref(false)

// 网页版在浏览器里生成后下载；这边先选保存位置，后端按多工况逐个算、写文件
const saveExcel = async (): Promise<void> => {
    if (exporting.value) return
    const { canceled, filePath } = await window.electronAPI.saveFileDialog({
        title: '保存为 Excel',
        defaultPath: '齿轮载荷.xlsx',
        filters: [{ name: 'Excel', extensions: ['xlsx'] }]
    })
    if (canceled || !filePath) return
    const path = /\.xlsx$/i.test(filePath) ? filePath : `${filePath}.xlsx`
    exporting.value = true
    try {
        await exportGearLoads({
            inputData: inputData.value,
            selectedData: selectedData.value,
            path
        })
        message.success(`Excel 文件已保存：${path}`)
    } catch (err) {
        message.error(`导出失败：${(err as Error).message}`, { duration: 5000 })
    } finally {
        exporting.value = false
    }
}

// ========== 历史记录：Ctrl+S 存、Ctrl+F 查 ==========
const saving = ref(false)
// 按 Ctrl+S 时还没登录：登录完接着存，登录框关掉还没登录就算了
let saveAfterLogin = false

const saveAsHistory = async (): Promise<void> => {
    const form = formData.value
    if (!form.gearUnit || !form.windTurbine || !form.loadSpectrum) {
        message.error('请填写完整的基本信息')
        return
    }
    if (!account.user) {
        saveAfterLogin = true
        account.loginVisible = true
        return
    }
    if (saving.value) return
    saving.value = true
    try {
        const { created } = await account.withAccess((access) =>
            saveHistory(access, {
                formData: { ...form },
                inputData: inputData.value,
                selectedData: selectedData.value
            })
        )
        message.success(created ? '保存成功' : '保存成功，覆盖了之前存的同一条')
    } catch (err) {
        message.error(`保存失败：${(err as Error).message}`, { duration: 5000 })
    } finally {
        saving.value = false
    }
}

watch(
    () => account.loginVisible,
    (visible) => {
        if (visible || !saveAfterLogin) return
        saveAfterLogin = false
        if (account.user) saveAsHistory()
    }
)

const historyVisible = ref(false)

// 同网页版：基础设置、输入表、多工况换成记录里的，结果表不动，要再点「计算结果」
const handleHistorySelect = async (item: HistoryItem): Promise<void> => {
    try {
        const detail = await account.withAccess((access) => fetchHistory(access, item.id))
        formData.value = { ...detail.formData }
        inputData.value = detail.inputData ?? inputData.value
        dialogTableData.value = detail.selectedData ?? dialogTableData.value
        selectedData.value = detail.selectedData ?? selectedData.value
        message.success(`已回填「${item.label}」`)
    } catch (err) {
        message.error(`获取历史记录失败：${(err as Error).message}`, { duration: 5000 })
    }
}

const handleKeydown = (event: KeyboardEvent): void => {
    if (!event.ctrlKey && !event.metaKey) return
    if (event.key === 's') {
        event.preventDefault()
        saveAsHistory()
    } else if (event.key === 'f') {
        event.preventDefault()
        historyVisible.value = true
    }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.gear-scroll {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    padding: 16px 20px 24px;
    overflow-y: auto;
}

.gear-card {
    flex-shrink: 0;
    overflow: hidden;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.card-head {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 44px;
    padding: 6px 12px 6px 16px;
    border-bottom: 1px solid var(--divider);
}

.gear-card.is-collapsed .card-head {
    border-bottom-color: transparent;
}

.card-title {
    min-width: 0;
    overflow: hidden;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.shortcut {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    gap: 3px;
    font-size: 12px;
    color: var(--text-3);
}

.shortcut + .shortcut {
    margin-left: 6px;
}

.basic-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 640px;
    padding: 16px;
}

.basic-field {
    display: grid;
    grid-template-columns: 120px minmax(0, 1fr);
    align-items: center;
    column-gap: 12px;
}

/* 窗口窄时输入表自己横向滚动 */
.table-scroll {
    overflow-x: auto;
}

.input-table {
    width: 100%;
    min-width: 820px;
    border-collapse: collapse;
}

.input-table th,
.input-table td {
    padding: 5px 8px;
    text-align: left;
    border-bottom: 1px solid var(--divider);
}

.input-table th {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-3);
}

.input-table tbody tr:last-child td {
    border-bottom: 0;
}

.input-table .col-param {
    width: 340px;
    padding-left: 16px;
    color: var(--text-2);
}

.param-link {
    padding: 0;
    color: var(--accent);
    text-align: left;
    background: none;
    border: 0;
    cursor: pointer;
}

.param-link:hover {
    text-decoration: underline;
}

.icon-btn .lucide {
    transition: transform 0.15s;
}

.icon-btn.is-open .lucide {
    transform: rotate(90deg);
}

/* ========== 多工况弹窗 ========== */
.condition-head,
.condition-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
}

.condition-head {
    padding-bottom: 6px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-3);
}

.condition-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: calc(100vh - 320px);
    overflow-y: auto;
}

.condition-note {
    margin: 12px 0 0;
    font-size: 12px;
    color: var(--text-3);
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
