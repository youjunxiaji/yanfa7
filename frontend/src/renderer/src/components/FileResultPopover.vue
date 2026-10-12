<template>
    <n-popover
        trigger="hover"
        placement="right"
        :disabled="!previewItems?.length"
        :delay="250"
        :show-arrow="false"
    >
        <template #trigger>
            <slot />
        </template>
        <div class="thumb-pop">
            <div class="thumb-title">{{ fileName }}</div>
            <div class="thumb-list">
                <div v-for="item in previewItems" :key="item.colIndex">
                    <div v-if="(previewItems?.length ?? 0) > 1" class="thumb-label">
                        第 {{ item.colIndex }} 列
                    </div>
                    <img :src="convertFileSrc(item.path)" alt="预览" class="thumb-img" />
                </div>
            </div>
        </div>
    </n-popover>
</template>

<script setup lang="ts">
// 文件名上的悬停缩略图：解析完成后才有 previewItems，没有时不弹
import { NPopover } from 'naive-ui'
import { convertFileSrc } from '@tauri-apps/api/core'

export interface PreviewItem {
    colIndex: number
    path: string
}

defineProps<{
    fileName: string
    previewItems?: PreviewItem[]
}>()
</script>

<style scoped>
.thumb-pop {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.thumb-title {
    font-weight: 600;
}

.thumb-list {
    display: flex;
    gap: 10px;
}

.thumb-label {
    margin-bottom: 4px;
    font-size: 12px;
    color: var(--text-3);
}

.thumb-img {
    display: block;
    width: 200px;
    max-height: 280px;
    object-fit: contain;
    background: var(--paper);
    border: 1px solid var(--border);
    border-radius: 6px;
}
</style>
