<template>
    <n-modal
        v-model:show="visible"
        preset="card"
        title="粘贴工况"
        :style="{ width: '600px' }"
        :bordered="false"
        :mask-closable="false"
        @after-enter="focusArea"
        @after-leave="pending = []"
    >
        <div
            ref="areaRef"
            class="paste-area"
            :class="{ 'has-data': pending.length > 0 }"
            tabindex="0"
            @paste="handlePaste"
        >
            <template v-if="pending.length > 0">
                <n-data-table
                    :columns="COLUMNS"
                    :data="pending"
                    size="small"
                    :bordered="false"
                    :max-height="300"
                    virtual-scroll
                />
                <div class="paste-info">
                    已解析 <b>{{ pending.length }}</b> 组，确认后替换现在的工况
                </div>
            </template>
            <template v-else>
                <div class="paste-icon"><ClipboardPaste :size="20" /></div>
                <div class="paste-title">从 Excel 粘贴工况</div>
                <div class="paste-desc">
                    点一下这里，再按 <kbd>{{ isMac ? '⌘' : 'Ctrl' }}</kbd> <kbd>V</kbd> 粘贴
                </div>
                <div class="paste-cols">
                    <span>{{ InputParam.TORQUE }}</span>
                    <span>{{ InputParam.SPEED }}</span>
                </div>
                <div class="paste-desc">相邻两列，扭矩在前；表头这类不是数字的行会跳过</div>
            </template>
        </div>
        <template #footer>
            <div class="modal-actions">
                <n-button @click="visible = false">取消</n-button>
                <n-button type="primary" :disabled="pending.length === 0" @click="confirm">
                    确认导入（{{ pending.length }} 组）
                </n-button>
            </div>
        </template>
    </n-modal>
</template>

<script setup lang="ts">
// 多工况：一次从 Excel 粘贴扭矩、转速两列，预览后导入，替换现在的工况
import { nextTick, ref } from 'vue'
import { NButton, NDataTable, NModal, useMessage, type DataTableColumns } from 'naive-ui'
import { ClipboardPaste } from '@lucide/vue'
import type { ConditionRow } from '@renderer/api/gearLoad'
import { InputParam } from '@renderer/constants/gearLoad'
import { useGearLoadStore } from '@renderer/stores/gearLoad'

const NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/

const COLUMNS: DataTableColumns<ConditionRow> = [
    { key: 'index', title: '#', width: 56, align: 'center', render: (_, index) => index + 1 },
    { key: 'torque', title: InputParam.TORQUE, align: 'right' },
    { key: 'rpm', title: InputParam.SPEED, align: 'right' }
]

const visible = defineModel<boolean>('show', { default: false })

const store = useGearLoadStore()
const message = useMessage()
const isMac = window.electron.process.platform === 'darwin'

const areaRef = ref<HTMLElement>()
const pending = ref<ConditionRow[]>([])

const focusArea = (): void => {
    nextTick(() => areaRef.value?.focus())
}

// 每行按 tab 切开取前两格，两格都是数才算一组；数字原样留着字符串，和网页版存的一样
const handlePaste = (event: ClipboardEvent): void => {
    const text = event.clipboardData?.getData('text/plain')
    if (!text) return
    event.preventDefault()
    const parsed: ConditionRow[] = []
    for (const line of text.split(/\r?\n/)) {
        const [torque = '', rpm = ''] = line.split('\t').map((cell) => cell.trim())
        if (NUMBER.test(torque) && NUMBER.test(rpm)) parsed.push({ torque, rpm })
    }
    if (parsed.length === 0) {
        message.warning('没找到扭矩、转速两列数字')
        return
    }
    pending.value = parsed
}

const confirm = (): void => {
    store.importConditions(pending.value)
    message.success(`已导入 ${pending.value.length} 组工况`)
    visible.value = false
}
</script>

<style scoped>
.paste-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    min-height: 300px;
    padding: 24px;
    text-align: center;
    border: 1.5px dashed var(--border-strong);
    border-radius: 10px;
    outline: none;
    transition:
        border-color 0.15s,
        background 0.15s;
}

.paste-area:focus {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.paste-area.has-data {
    align-items: stretch;
    justify-content: flex-start;
    padding: 0;
    text-align: left;
    background: transparent;
    border-style: solid;
    border-color: var(--border);
}

.paste-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    margin-bottom: 10px;
    color: var(--accent);
    background: var(--panel);
    border-radius: 12px;
    box-shadow: var(--shadow-sm);
}

.paste-title {
    font-size: 14px;
    font-weight: 600;
}

.paste-desc {
    font-size: 12.5px;
    color: var(--text-3);
}

.paste-desc kbd {
    margin: 0 1px;
}

.paste-cols {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
    margin: 12px 0 4px;
}

.paste-cols span {
    padding: 2px 8px;
    font-size: 12px;
    color: var(--text-2);
    background: var(--muted);
    border-radius: 5px;
}

.paste-info {
    padding: 10px 14px;
    font-size: 12.5px;
    color: var(--text-2);
    border-top: 1px solid var(--divider);
}

.paste-info b {
    color: var(--accent);
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
