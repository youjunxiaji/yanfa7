<template>
    <div class="side-nav">
        <el-menu
            :default-active="activeMenu"
            :collapse="collapsed"
            :router="true"
            class="side-menu"
        >
            <li class="el-menu-item collapse-item" @click="toggleCollapse">
                <el-icon>
                    <Fold v-if="!collapsed" />
                    <Expand v-else />
                </el-icon>
                <span v-show="!collapsed" class="collapse-label">收起</span>
            </li>

            <el-menu-item
                v-for="route in menuRoutes"
                :key="route.path"
                :index="route.path"
            >
                <el-icon>
                    <component :is="iconMap[route.meta?.icon as string]" />
                </el-icon>
                <template #title>{{ route.meta?.title }}</template>
            </el-menu-item>

            <div class="menu-spacer" />

            <el-menu-item index="/docs" disabled>
                <el-icon><Document /></el-icon>
                <template #title>文档</template>
            </el-menu-item>
            <el-menu-item index="/settings" disabled>
                <el-icon><Setting /></el-icon>
                <template #title>设置</template>
            </el-menu-item>
        </el-menu>
    </div>
</template>

<script setup lang="ts">
import { computed, type Component, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
    Document,
    Setting,
    Fold,
    Expand,
    Histogram
} from '@element-plus/icons-vue'

const iconMap: Record<string, Component> = {
    Histogram: markRaw(Histogram)
}

const collapsed = defineModel<boolean>('collapsed', { default: false })

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)

const menuRoutes = computed(() =>
    router.options.routes.filter((r) => r.meta?.title && r.meta?.icon)
)

function toggleCollapse() {
    collapsed.value = !collapsed.value
}
</script>

<style scoped>
.side-nav {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.side-menu {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: none !important;
}

.side-menu:not(.el-menu--collapse) {
    width: 200px;
}

.collapse-item {
    cursor: pointer;
}

.collapse-item:hover {
    color: var(--el-color-primary) !important;
}

.collapse-item .collapse-label {
    margin-left: 4px;
}

.menu-spacer {
    flex: 1;
}
</style>
