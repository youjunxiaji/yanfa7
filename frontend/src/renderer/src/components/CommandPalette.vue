<template>
    <Teleport to="body">
        <Transition name="palette">
            <div v-if="visible" class="palette-overlay" @click.self="close">
                <div class="palette-panel">
                    <div class="palette-input-wrapper">
                        <el-icon :size="16" class="palette-search-icon"><Search /></el-icon>
                        <input
                            ref="inputRef"
                            v-model="query"
                            class="palette-input"
                            placeholder="搜索页面跳转…"
                            @keydown.up.prevent="moveSelection(-1)"
                            @keydown.down.prevent="moveSelection(1)"
                            @keydown.enter.prevent="confirmSelection"
                            @keydown.esc="close"
                        />
                        <kbd class="palette-kbd">ESC</kbd>
                    </div>
                    <div v-if="filteredRoutes.length" class="palette-list">
                        <div
                            v-for="(item, idx) in filteredRoutes"
                            :key="item.path"
                            class="palette-item"
                            :class="{ 'is-active': idx === activeIndex }"
                            @mouseenter="activeIndex = idx"
                            @click="navigate(item.path)"
                        >
                            <el-icon :size="18" class="palette-item-icon">
                                <component :is="iconMap[item.icon]" />
                            </el-icon>
                            <span class="palette-item-title">{{ item.title }}</span>
                            <span class="palette-item-path">{{ item.path }}</span>
                        </div>
                    </div>
                    <div v-else class="palette-empty">无匹配结果</div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, type Component, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { Search, HomeFilled, Histogram } from '@element-plus/icons-vue'

const iconMap: Record<string, Component> = {
    HomeFilled: markRaw(HomeFilled),
    Histogram: markRaw(Histogram)
}

const visible = defineModel<boolean>('visible', { default: false })

const router = useRouter()
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

interface RouteItem {
    path: string
    title: string
    icon: string
}

const allRoutes = computed<RouteItem[]>(() =>
    router.options.routes
        .filter((r) => r.meta?.title && r.meta?.icon)
        .map((r) => ({
            path: r.path,
            title: r.meta!.title as string,
            icon: r.meta!.icon as string
        }))
)

const filteredRoutes = computed(() => {
    if (!query.value.trim()) return allRoutes.value
    const q = query.value.toLowerCase()
    return allRoutes.value.filter(
        (r) => r.title.toLowerCase().includes(q) || r.path.toLowerCase().includes(q)
    )
})

watch(
    () => visible.value,
    (val) => {
        if (val) {
            query.value = ''
            activeIndex.value = 0
            nextTick(() => inputRef.value?.focus())
        }
    }
)

watch(filteredRoutes, () => {
    activeIndex.value = 0
})

function moveSelection(delta: number): void {
    const len = filteredRoutes.value.length
    if (!len) return
    activeIndex.value = (activeIndex.value + delta + len) % len
}

function confirmSelection(): void {
    const item = filteredRoutes.value[activeIndex.value]
    if (item) navigate(item.path)
}

function navigate(path: string): void {
    router.push(path)
    close()
}

function close(): void {
    visible.value = false
}
</script>

<style scoped>
.palette-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    justify-content: center;
    padding-top: 20vh;
    background: rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(2px);
}

.palette-panel {
    width: 480px;
    max-height: 340px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16), 0 0 0 1px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-self: flex-start;
}

.palette-input-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
}

.palette-search-icon {
    color: #909399;
    flex-shrink: 0;
}

.palette-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 14px;
    color: #303133;
    background: transparent;
    line-height: 1.5;
}

.palette-input::placeholder {
    color: #c0c4cc;
}

.palette-kbd {
    font-size: 11px;
    color: #909399;
    background: #f5f5f7;
    border: 1px solid #e5e6eb;
    border-radius: 4px;
    padding: 1px 6px;
    font-family: inherit;
    line-height: 1.6;
    flex-shrink: 0;
}

.palette-list {
    overflow-y: auto;
    padding: 6px;
}

.palette-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.1s;
}

.palette-item.is-active {
    background: #f0f5ff;
}

.palette-item-icon {
    color: #606266;
    flex-shrink: 0;
}

.palette-item.is-active .palette-item-icon {
    color: var(--el-color-primary);
}

.palette-item-title {
    font-size: 14px;
    color: #303133;
    font-weight: 500;
}

.palette-item.is-active .palette-item-title {
    color: var(--el-color-primary);
}

.palette-item-path {
    margin-left: auto;
    font-size: 12px;
    color: #c0c4cc;
    font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}

.palette-empty {
    padding: 24px 16px;
    text-align: center;
    font-size: 13px;
    color: #909399;
}

/* Transition */
.palette-enter-active {
    transition: opacity 0.15s ease;
}

.palette-leave-active {
    transition: opacity 0.1s ease;
}

.palette-enter-from,
.palette-leave-to {
    opacity: 0;
}

.palette-enter-active .palette-panel {
    animation: palette-slide-in 0.15s ease;
}

@keyframes palette-slide-in {
    from {
        opacity: 0;
        transform: translateY(-8px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}
</style>
