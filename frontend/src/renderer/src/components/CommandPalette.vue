<template>
    <Teleport to="body">
        <Transition name="palette">
            <div v-if="visible" class="palette-mask" @mousedown.self="close">
                <div class="palette">
                    <div class="palette-input-row">
                        <Search :size="16" />
                        <input
                            ref="inputRef"
                            v-model="query"
                            class="palette-input"
                            placeholder="搜索页面跳转…"
                            @keydown.up.prevent="moveSelection(-1)"
                            @keydown.down.prevent="moveSelection(1)"
                            @keydown.enter.prevent="confirmSelection"
                            @keydown.esc.prevent="close"
                        />
                        <kbd>Esc</kbd>
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
                            <component :is="item.icon" :size="16" />
                            <span>{{ item.title }}</span>
                            <span class="palette-path">{{ item.path }}</span>
                        </div>
                    </div>
                    <div v-else class="palette-empty">无匹配结果</div>
                    <div class="palette-foot">
                        <span><kbd>↑</kbd><kbd>↓</kbd>选择</span>
                        <span><kbd>↵</kbd>打开</span>
                        <span><kbd>Esc</kbd>关闭</span>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
// ⌘P / Ctrl+P 唤起的页面跳转面板，页面列表和图标都取自路由 meta
import { ref, computed, watch, nextTick, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@lucide/vue'

interface RouteItem {
    path: string
    title: string
    icon: Component
}

const visible = defineModel<boolean>('visible', { default: false })

const router = useRouter()
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

const allRoutes = computed<RouteItem[]>(() =>
    router.options.routes.flatMap((r) =>
        r.meta?.title && r.meta?.icon
            ? [{ path: r.path, title: r.meta.title, icon: r.meta.icon }]
            : []
    )
)

const filteredRoutes = computed(() => {
    const q = query.value.trim().toLowerCase()
    if (!q) return allRoutes.value
    return allRoutes.value.filter(
        (r) => r.title.toLowerCase().includes(q) || r.path.toLowerCase().includes(q)
    )
})

watch(visible, (val) => {
    if (!val) return
    query.value = ''
    activeIndex.value = 0
    nextTick(() => inputRef.value?.focus())
})

watch(filteredRoutes, () => {
    activeIndex.value = 0
})

const close = (): void => {
    visible.value = false
}

const navigate = (path: string): void => {
    router.push(path)
    close()
}

const moveSelection = (delta: number): void => {
    const len = filteredRoutes.value.length
    if (!len) return
    activeIndex.value = (activeIndex.value + delta + len) % len
}

const confirmSelection = (): void => {
    const item = filteredRoutes.value[activeIndex.value]
    if (item) navigate(item.path)
}
</script>

<style scoped>
.palette-mask {
    position: fixed;
    inset: 0;
    z-index: 3000;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 16vh;
    background: var(--mask);
    backdrop-filter: blur(2px);
}

.palette {
    width: 540px;
    max-width: calc(100vw - 32px);
    overflow: hidden;
    background: var(--panel);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
}

.palette-input-row {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 50px;
    padding: 0 14px;
    color: var(--text-3);
    border-bottom: 1px solid var(--divider);
}

.palette-input {
    flex: 1;
    min-width: 0;
    font: inherit;
    font-size: 14px;
    color: var(--text-1);
    background: transparent;
    border: 0;
    outline: 0;
}

.palette-input::placeholder {
    color: var(--text-3);
}

.palette-list {
    max-height: 320px;
    padding: 6px;
    overflow-y: auto;
}

.palette-item {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 38px;
    padding: 0 10px;
    border-radius: 8px;
    cursor: pointer;
}

.palette-item .lucide {
    color: var(--text-3);
}

.palette-item.is-active {
    background: var(--muted);
}

.palette-item.is-active .lucide {
    color: var(--accent);
}

.palette-path {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-3);
}

.palette-empty {
    padding: 28px;
    color: var(--text-3);
    text-align: center;
}

.palette-foot {
    display: flex;
    gap: 16px;
    padding: 8px 14px;
    font-size: 12px;
    color: var(--text-3);
    background: var(--subtle);
    border-top: 1px solid var(--divider);
}

.palette-foot span {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.palette-enter-active,
.palette-leave-active {
    transition: opacity 0.14s ease;
}

.palette-enter-from,
.palette-leave-to {
    opacity: 0;
}

.palette-enter-active .palette {
    animation: palette-in 0.16s ease;
}

@keyframes palette-in {
    from {
        opacity: 0;
        transform: translateY(-6px) scale(0.98);
    }
}
</style>
