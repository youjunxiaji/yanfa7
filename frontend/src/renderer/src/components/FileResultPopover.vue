<template>
    <el-popover
        trigger="hover"
        :width="'auto'"
        placement="right"
    >
        <template #reference>
            <slot />
        </template>
        <div class="popover-content">
            <div class="popover-title">{{ fileName }}</div>
            <div
                v-if="previewItems && previewItems.length > 0"
                class="popover-previews"
            >
                <div
                    v-for="item in previewItems"
                    :key="item.colIndex"
                    class="popover-preview"
                >
                    <div
                        v-if="previewItems.length > 1"
                        class="col-label"
                    >
                        第{{ item.colIndex }}列
                    </div>
                    <img
                        :src="`local-file://${item.path}`"
                        alt="预览"
                        class="preview-img"
                    >
                </div>
            </div>
        </div>
    </el-popover>
</template>

<script setup lang="ts">
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
.popover-content {
    min-width: 160px;
    padding: 4px 0;
}

.popover-title {
    font-size: 13px;
    font-weight: 600;
    color: #1d1d1f;
}

.popover-previews {
    display: flex;
    gap: 12px;
    margin-top: 8px;
}

.popover-preview {
    flex: 1;
    min-width: 0;
}

.col-label {
    font-size: 12px;
    color: #86868b;
    margin-bottom: 4px;
    font-weight: 500;
}

.preview-img {
    max-width: 200px;
    max-height: 280px;
    border-radius: 6px;
    border: 1px solid #e5e5ea;
    object-fit: contain;
}
</style>
