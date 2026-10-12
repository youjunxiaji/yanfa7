<template>
    <div class="status-strip" :class="`is-${status}`">
        <div class="status-row">
            <component
                :is="icon"
                class="status-icon"
                :class="{ spin: status === 'processing' }"
                :size="15"
            />
            <span class="status-text">{{ text }}</span>
            <span v-if="meta" class="status-meta num">{{ meta }}</span>
        </div>
        <n-progress
            v-if="status === 'processing'"
            type="line"
            :percentage="percent"
            :show-indicator="false"
            :height="4"
            :border-radius="2"
            processing
        />
    </div>
</template>

<script setup lang="ts">
// 结果区工具栏下面的进度条带：处理中 / 完成 / 失败（见 UI Skill 界面标准第八节）
import { computed } from 'vue'
import { NProgress } from 'naive-ui'
import { CircleCheck, LoaderCircle, TriangleAlert } from '@lucide/vue'

const props = withDefaults(
    defineProps<{
        status: 'processing' | 'done' | 'error'
        text: string
        meta?: string
        percent?: number
    }>(),
    { percent: 0 }
)

const icon = computed(() => {
    if (props.status === 'done') return CircleCheck
    if (props.status === 'error') return TriangleAlert
    return LoaderCircle
})
</script>

<style scoped>
.status-strip {
    display: flex;
    flex-shrink: 0;
    flex-direction: column;
    gap: 8px;
    padding: 10px 20px;
    border-bottom: 1px solid var(--divider);
}

.status-strip.is-processing {
    background: var(--accent-soft);
}

.status-strip.is-done {
    background: var(--success-soft);
}

.status-strip.is-error {
    background: var(--danger-soft);
}

.status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.is-processing .status-icon {
    color: var(--accent);
}

.is-done .status-icon {
    color: var(--success);
}

.is-error .status-icon {
    color: var(--danger);
}

.status-text {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.status-meta {
    flex-shrink: 0;
    font-size: 12px;
    color: var(--text-2);
}
</style>
