<template>
    <header class="page-header">
        <div class="page-icon" :class="`is-${tool?.tone ?? ToolTone.BLUE}`">
            <component :is="route.meta.icon" :size="16" />
        </div>
        <div class="page-title">{{ tool?.name ?? route.meta.title }}</div>
        <div v-if="tool" class="page-desc">{{ tool.desc }}</div>
        <div v-if="$slots.default" class="page-actions">
            <slot />
        </div>
    </header>
</template>

<script setup lang="ts">
// 工具页标题栏：图标、名称、说明都取自路由 meta，和侧栏、首页是同一份
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ToolTone } from '@renderer/constants/ui'

const route = useRoute()
const tool = computed(() => route.meta.tool)
</script>
