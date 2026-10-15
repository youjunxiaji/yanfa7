<template>
    <n-modal
        v-model:show="visible"
        preset="card"
        title="历史记录"
        :style="{ width: '680px' }"
        :bordered="false"
        @after-enter="handleOpen"
    >
        <div v-if="account.user" class="history">
            <n-input
                ref="queryRef"
                v-model:value="query"
                placeholder="按齿轮单元、风机或载荷谱搜索"
                clearable
                @update:value="scheduleSearch"
            >
                <template #prefix><Search class="input-prefix" :size="15" /></template>
            </n-input>
            <n-data-table
                size="small"
                :bordered="false"
                :columns="columns"
                :data="records"
                :loading="searching"
                :row-key="(row: HistoryItem) => row.id"
                :row-props="rowProps"
                :max-height="320"
                class="history-table"
            >
                <template #empty>
                    <span class="table-empty" :class="{ 'is-error': !!error }">
                        {{ error || (query.trim() ? '没有对得上的记录' : '服务器上还没有记录') }}
                    </span>
                </template>
            </n-data-table>
            <p class="history-note">
                网页版和这边存的都在，只查得到自己的；点一行，把基础设置、输入表和多工况填回页面
            </p>
        </div>
        <EmptyState
            v-else
            :icon="CircleUserRound"
            title="登录后查历史记录"
            desc="历史记录存在 TMB 服务器上，用网页版的工号和密码登录"
            @click="account.loginVisible = true"
        >
            <n-button type="primary" @click.stop="account.loginVisible = true">登录</n-button>
        </EmptyState>
    </n-modal>
</template>

<script setup lang="ts">
// 齿轮载荷的历史记录：查 TMB 服务器上存的（网页版和这边 Ctrl+S 存的都在），点一行交给页面回填；没登录时先登录
import { h, ref, watch, type HTMLAttributes } from 'vue'
import { NButton, NDataTable, NEllipsis, NInput, NModal, type DataTableColumns } from 'naive-ui'
import { CircleUserRound, Search } from '@lucide/vue'
import { fetchHistories, type HistoryItem } from '@renderer/api/gearLoad'
import { useAccountStore } from '@renderer/stores/account'
import EmptyState from '@renderer/components/EmptyState.vue'

const visible = defineModel<boolean>('show', { default: false })

const emit = defineEmits<{ select: [item: HistoryItem] }>()

const account = useAccountStore()

const query = ref('')
const records = ref<HistoryItem[]>([])
const searching = ref(false)
const error = ref('')
const queryRef = ref<InstanceType<typeof NInput> | null>(null)

const columns: DataTableColumns<HistoryItem> = [
    {
        title: '齿轮单元 / 风机 / 载荷谱',
        key: 'label',
        render: (row) =>
            h(NEllipsis, { tooltip: { contentClass: 'long-tip' } }, { default: () => row.label })
    }
]

// 搜索边打边查，只认最后一次的结果
let seq = 0
let timer: ReturnType<typeof setTimeout> | undefined

const search = async (): Promise<void> => {
    clearTimeout(timer)
    if (!account.user) return
    const current = ++seq
    searching.value = true
    error.value = ''
    try {
        const result = await account.withAccess((access) =>
            fetchHistories(access, query.value.trim())
        )
        if (current === seq) records.value = result
    } catch (err) {
        if (current === seq) {
            records.value = []
            error.value = (err as Error).message
        }
    } finally {
        if (current === seq) searching.value = false
    }
}

const scheduleSearch = (): void => {
    clearTimeout(timer)
    timer = setTimeout(search, 300)
}

const handleOpen = (): void => {
    queryRef.value?.focus()
    search()
}

// 在这里登录完，接着查
watch(
    () => account.user,
    (user) => {
        if (user && visible.value) search()
    }
)

const rowProps = (row: HistoryItem): HTMLAttributes => ({
    class: 'history-row',
    onClick: () => {
        emit('select', row)
        visible.value = false
    }
})
</script>

<style scoped>
.history {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.input-prefix {
    color: var(--text-3);
}

.history-table :deep(.history-row) {
    cursor: pointer;
}

.table-empty {
    font-size: 12.5px;
    color: var(--text-3);
}

.table-empty.is-error {
    color: var(--danger);
}

.history-note {
    margin: 0;
    font-size: 12px;
    color: var(--text-3);
}
</style>
