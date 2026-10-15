<template>
    <div class="page">
        <PageHeader>
            <n-button size="small" :disabled="!filtered.length" @click="copyLogs">
                <template #icon><Copy :size="15" /></template>
                复制
            </n-button>
            <n-tooltip :disabled="!isDev" :delay="300">
                <template #trigger>
                    <!-- 按钮禁用时收不到悬停，外面包一层给 tooltip -->
                    <span class="tooltip-anchor">
                        <n-button size="small" :disabled="isDev" @click="openLogDir">
                            <template #icon><FolderOpen :size="15" /></template>
                            打开日志目录
                        </n-button>
                    </span>
                </template>
                开发版不写日志文件，后端的输出在运行 uv run main.py 的终端里
            </n-tooltip>
        </PageHeader>
        <div class="result-toolbar">
            <n-tabs
                :value="minLevel"
                type="segment"
                size="small"
                :animated="false"
                class="level-tabs"
                @update:value="setMinLevel"
            >
                <n-tab v-for="option in LEVEL_OPTIONS" :key="option.value" :name="option.value">
                    {{ option.label }}
                </n-tab>
            </n-tabs>
            <n-input
                v-model:value="query"
                size="small"
                clearable
                placeholder="搜索日志"
                class="log-search"
            >
                <template #prefix><Search class="input-prefix" :size="15" /></template>
            </n-input>
            <span class="count-pill">{{ filtered.length }} 条</span>
            <span class="toolbar-spacer" />
            <button class="link-btn" :disabled="!logs.shown.length" @click="logs.clear()">
                清屏
            </button>
        </div>
        <StatusStrip v-if="strip" status="error" :text="strip" />
        <div ref="bodyRef" class="log-body" @scroll="handleScroll">
            <EmptyState
                v-if="emptyState"
                :icon="ScrollText"
                :title="emptyState.title"
                :desc="emptyState.desc"
                :busy="emptyState.busy"
                :clickable="false"
            />
            <div
                v-for="entry in filtered"
                :key="entry.seq"
                class="log-entry"
                :class="`is-${entry.level.toLowerCase()}`"
            >
                <div
                    class="log-line"
                    :class="{ 'has-detail': !!entry.detail }"
                    @click="toggle(entry)"
                >
                    <span class="log-toggle">
                        <ChevronRight
                            v-if="entry.detail"
                            :size="13"
                            :class="{ 'is-open': expanded.has(entry.seq) }"
                        />
                    </span>
                    <span class="log-time" :title="entry.time">{{ entry.time.slice(11, 23) }}</span>
                    <span class="log-level">{{ LOG_LEVEL_LABEL[entry.level] }}</span>
                    <span class="log-source">{{ entry.source }}</span>
                    <span class="log-message">{{ entry.message }}</span>
                </div>
                <pre v-if="entry.detail && expanded.has(entry.seq)" class="log-detail">{{
                    entry.detail
                }}</pre>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
// 日志页：这次运行的后端日志和界面报错，开着时每秒取新的；数据在 stores/logs.ts，切走再回来还在
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { NButton, NInput, NTab, NTabs, NTooltip, useMessage } from 'naive-ui'
import { ChevronRight, Copy, FolderOpen, ScrollText, Search } from '@lucide/vue'
import type { LogEntry } from '@renderer/api/logs'
import { LOG_LEVEL_LABEL, LOG_LEVEL_RANK, LogLevel } from '@renderer/constants/log'
import { useLogStore } from '@renderer/stores/logs'
import PageHeader from '@renderer/components/PageHeader.vue'
import EmptyState from '@renderer/components/EmptyState.vue'
import StatusStrip from '@renderer/components/StatusStrip.vue'

interface EmptyInfo {
    title: string
    desc: string
    busy: boolean
}

// 按级别筛：选「警告」时警告和错误都显示
const LEVEL_OPTIONS: { value: LogLevel; label: string }[] = [
    { value: LogLevel.INFO, label: '全部' },
    { value: LogLevel.WARNING, label: '警告' },
    { value: LogLevel.ERROR, label: '错误' }
]

const logs = useLogStore()
const message = useMessage()
const isDev = import.meta.env.DEV

const minLevel = ref<LogLevel>(LogLevel.INFO)
const query = ref('')
const expanded = ref(new Set<number>())
const bodyRef = ref<HTMLElement | null>(null)

const setMinLevel = (value: string | number): void => {
    const level = Object.values(LogLevel).find((item) => item === value)
    if (level) minLevel.value = level
}

const filtered = computed(() => {
    const rank = LOG_LEVEL_RANK[minLevel.value]
    const keyword = query.value.trim().toLowerCase()
    return logs.shown.filter(
        (entry) =>
            LOG_LEVEL_RANK[entry.level] >= rank &&
            (!keyword ||
                `${entry.source} ${entry.message}\n${entry.detail}`.toLowerCase().includes(keyword))
    )
})

// 连不上后端时，已经取到的接着显示，上面一条条带说明；一条都没有时直接用空状态说
const strip = computed(() => (logs.error && logs.entries.length ? logs.error : ''))

const emptyState = computed((): EmptyInfo | null => {
    if (filtered.value.length) return null
    if (logs.error && !logs.entries.length) {
        return { title: '连不上后端', desc: logs.error, busy: false }
    }
    if (!logs.connected) {
        return { title: '正在连接后端…', desc: '应用刚打开时后端要等一会儿', busy: true }
    }
    if (logs.shown.length) {
        return { title: '没有对得上的日志', desc: '换个级别或搜索词试试', busy: false }
    }
    if (logs.entries.length) {
        return { title: '清屏以后还没有新日志', desc: '有新的记录时会出现在这里', busy: false }
    }
    return { title: '还没有日志', desc: '后端和界面有记录时会出现在这里', busy: false }
})

// 有详情（多行、报错堆栈）的点开看
const toggle = (entry: LogEntry): void => {
    if (!entry.detail) return
    if (expanded.value.has(entry.seq)) expanded.value.delete(entry.seq)
    else expanded.value.add(entry.seq)
}

// 停在最底下时，新日志进来跟着滚到底；往上翻着看的时候不动
let stickToBottom = true

const handleScroll = (): void => {
    const body = bodyRef.value
    if (body) stickToBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 24
}

watch(
    () => filtered.value.length,
    async () => {
        if (!stickToBottom) return
        await nextTick()
        const body = bodyRef.value
        if (body) body.scrollTop = body.scrollHeight
    },
    { immediate: true }
)

// 复制现在筛出来的，详情跟在各自那一行下面
const copyLogs = async (): Promise<void> => {
    const text = filtered.value
        .map((entry) => {
            const line = `${entry.time} ${LOG_LEVEL_LABEL[entry.level]} ${entry.source} ${entry.message}`
            return entry.detail ? `${line}\n${entry.detail}` : line
        })
        .join('\n')
    try {
        await navigator.clipboard.writeText(text)
        message.success(`已复制 ${filtered.value.length} 条日志`)
    } catch (err) {
        message.error(`复制失败：${(err as Error).message}`, { duration: 5000 })
    }
}

const openLogDir = async (): Promise<void> => {
    try {
        await window.electronAPI.openLogDir()
    } catch (err) {
        // Tauri 的报错是字符串，不是 Error
        const reason = err instanceof Error ? err.message : String(err)
        message.error(`打开日志目录失败：${reason}`, { duration: 5000 })
    }
}

onMounted(() => logs.start())
onBeforeUnmount(() => logs.stop())
</script>

<style scoped>
.level-tabs {
    flex-shrink: 0;
    width: 168px;
}

.log-search {
    width: 220px;
}

.input-prefix {
    color: var(--text-3);
}

.tooltip-anchor {
    display: inline-flex;
}

/* 日志列表：等宽字，时间、级别、来源各占一列对齐，内容放不下就折行 */
.log-body {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
    padding: 6px 0 12px;
    overflow-y: auto;
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.6;
}

.log-line {
    display: grid;
    grid-template-columns: 13px 88px 26px 26px minmax(0, 1fr);
    column-gap: 10px;
    align-items: start;
    padding: 1px 20px 1px 12px;
}

.log-line:hover {
    background: var(--hover);
}

.log-line.has-detail {
    cursor: pointer;
}

.log-toggle {
    display: flex;
    align-items: center;
    height: 19px;
    color: var(--text-3);
}

.log-toggle .lucide {
    transition: transform 0.15s;
}

.log-toggle .is-open {
    transform: rotate(90deg);
}

.log-time {
    color: var(--text-3);
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}

.log-level {
    color: var(--text-3);
    white-space: nowrap;
}

.log-source {
    color: var(--text-2);
    white-space: nowrap;
}

.log-message {
    color: var(--text-1);
    white-space: pre-wrap;
    word-break: break-all;
}

.log-entry.is-warning .log-level {
    color: var(--warning);
}

.log-entry.is-error .log-level,
.log-entry.is-error .log-message {
    color: var(--danger);
}

/* 详情（报错堆栈）缩进到时间那一列 */
.log-detail {
    margin: 2px 20px 6px 35px;
    padding: 8px 12px;
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.55;
    color: var(--text-2);
    white-space: pre-wrap;
    word-break: break-all;
    background: var(--subtle);
    border: 1px solid var(--border);
    border-radius: 8px;
}
</style>
