<template>
    <div
        class="empty-state"
        :class="{ 'is-busy': busy, 'is-clickable': clickable && !busy }"
        @click="handleClick"
    >
        <div class="empty-icon">
            <LoaderCircle v-if="busy" class="spin" :size="20" />
            <component :is="icon" v-else :size="20" />
        </div>
        <div class="empty-title">{{ title }}</div>
        <div v-if="desc" class="empty-desc">{{ desc }}</div>
        <div v-if="$slots.default" class="empty-actions" @click.stop>
            <slot />
        </div>
    </div>
</template>

<script setup lang="ts">
// 结果区的空状态 / 忙碌态：虚线框整块可点，按钮放默认插槽（见 UI Skill 界面标准第八节）
import type { Component } from 'vue'
import { LoaderCircle } from '@lucide/vue'

const props = withDefaults(
    defineProps<{
        title: string
        icon?: Component
        desc?: string
        busy?: boolean
        clickable?: boolean
    }>(),
    { busy: false, clickable: true }
)

const emit = defineEmits<{ click: [] }>()

const handleClick = (): void => {
    if (props.clickable && !props.busy) emit('click')
}
</script>

<style scoped>
.empty-state {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin: 20px;
    padding: 32px;
    text-align: center;
    border: 1.5px dashed var(--border-strong);
    border-radius: 12px;
    transition:
        border-color 0.15s,
        background 0.15s;
}

.empty-state.is-clickable {
    cursor: pointer;
}

.empty-state.is-clickable:hover,
.empty-state.is-busy {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.empty-state.is-busy {
    cursor: progress;
}

.empty-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    margin-bottom: 10px;
    color: var(--text-2);
    background: var(--muted);
    border-radius: 12px;
    transition:
        background 0.15s,
        color 0.15s,
        transform 0.15s;
}

.empty-state.is-clickable:hover .empty-icon,
.empty-state.is-busy .empty-icon {
    color: var(--accent);
    background: var(--panel);
    box-shadow: var(--shadow-sm);
}

.empty-state.is-clickable:hover .empty-icon {
    transform: translateY(-1px);
}

.empty-title {
    font-size: 14px;
    font-weight: 600;
}

.empty-desc {
    max-width: 380px;
    font-size: 12.5px;
    color: var(--text-3);
}

.empty-actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
}
</style>
