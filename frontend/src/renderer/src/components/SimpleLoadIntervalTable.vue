<template>
    <div class="interval-wrap">
        <table class="interval-table">
            <thead>
                <tr>
                    <th class="col-component">分量</th>
                    <th
                        v-for="slot in SLOTS"
                        :key="slot"
                        :class="{ 'is-edge': isEdge(slot) }"
                        :title="slotHint(slot)"
                    >
                        {{ slotLabel(slot) }}
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr
                    v-for="component in store.participating"
                    :key="component"
                    :class="{ 'is-active': component === store.activeComponent }"
                    @click="store.selectedComponent = component"
                >
                    <td class="col-component">
                        <div class="component-name">{{ component }}</div>
                        <div
                            class="component-state"
                            :class="`is-${stateOf(component).kind}`"
                            :title="stateOf(component).hint"
                        >
                            {{ stateOf(component).text }}
                        </div>
                    </td>
                    <td v-for="slot in SLOTS" :key="slot" :class="{ 'is-edge': isEdge(slot) }">
                        <n-input-number
                            class="edge-input"
                            :value="store.intervals[component]?.[slot] ?? null"
                            size="small"
                            :show-button="false"
                            placeholder=""
                            :theme-overrides="CELL_THEME"
                            :disabled="store.isBusy"
                            @update:value="
                                (value: number | null) => store.setEdge(component, slot, value)
                            "
                        />
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup lang="ts">
// 区间表：每行一个参与分组的分量，下界、上界加载后自动填数据的最值，中间 9 格是手填的分段点。
// 点哪一行，下面的分布图就切到哪个分量。
import { NInputNumber, type GlobalThemeOverrides } from 'naive-ui'
import { INTERVAL_SLOTS, LoadColumn } from '@renderer/constants/simpleLoad'
import { useSimpleLoadStore } from '@renderer/stores/simpleLoad'

type RowKind = 'empty' | 'valid' | 'invalid'

const SLOTS = Array.from({ length: INTERVAL_SLOTS }, (_, slot) => slot)

// 格子窄，数值框左右留白收小，六七位数字放得下
const CELL_THEME: GlobalThemeOverrides['InputNumber'] = {
    peers: { Input: { paddingSmall: '0 6px' } }
}

const store = useSimpleLoadStore()

const isEdge = (slot: number): boolean => slot === 0 || slot === INTERVAL_SLOTS - 1

const slotLabel = (slot: number): string => {
    if (slot === 0) return '下界'
    if (slot === INTERVAL_SLOTS - 1) return '上界'
    return `点 ${slot}`
}

const slotHint = (slot: number): string => {
    if (slot === 0) return '区间下界，加载数据后自动填最小值'
    if (slot === INTERVAL_SLOTS - 1) return '区间上界，加载数据后自动填最大值'
    return `第 ${slot} 个分段点，从小到大填，留空就不切这一刀`
}

// 分量名下面一行：分了几段，颜色表示边界是否从小到大
const stateOf = (component: LoadColumn): { kind: RowKind; text: string; hint: string } => {
    const state = store.intervalStates[component]
    if (!state || state.segments < 1) {
        return { kind: 'empty', text: '未分段', hint: '至少填下界和上界' }
    }
    const text = `${state.segments} 段`
    return state.valid
        ? { kind: 'valid', text, hint: `${text}，边界从小到大` }
        : { kind: 'invalid', text, hint: `${text}，边界没有从小到大，检查填写顺序` }
}
</script>

<style scoped>
/* 和网页版一样，窗口窄时表格自己横向滚动，分量列固定在左边 */
.interval-wrap {
    flex-shrink: 0;
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
}

.interval-table {
    width: 100%;
    min-width: max-content;
    border-collapse: separate;
    border-spacing: 0;
}

.interval-table th,
.interval-table td {
    padding: 6px 3px;
    border-bottom: 1px solid var(--divider);
}

.interval-table th {
    height: 34px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-3);
    white-space: nowrap;
}

.interval-table tbody tr {
    cursor: pointer;
}

.interval-table tbody tr:last-child td {
    border-bottom: 0;
}

.interval-table .is-edge {
    background: var(--subtle);
}

.interval-table .col-component {
    position: sticky;
    left: 0;
    z-index: 1;
    min-width: 104px;
    padding: 6px 12px;
    text-align: left;
    background: var(--panel);
    border-right: 1px solid var(--divider);
}

.interval-table tbody tr.is-active td {
    background: var(--accent-soft);
}

/* 选中底是半透明的，固定列先垫一层面板色，横向滚动时下面的格子才不会透上来 */
.interval-table tbody tr.is-active td.col-component {
    background: linear-gradient(var(--accent-soft), var(--accent-soft)), var(--panel);
}

.interval-table tbody tr.is-active .component-name {
    color: var(--accent);
}

.edge-input {
    width: 64px;
}

.component-name {
    font-weight: 500;
    white-space: nowrap;
}

.component-state {
    font-size: 12px;
    white-space: nowrap;
}

.component-state.is-empty {
    color: var(--text-3);
}

.component-state.is-valid {
    color: var(--success);
}

.component-state.is-invalid {
    color: var(--danger);
}
</style>
