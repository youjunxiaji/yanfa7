<template>
    <div class="side-nav">
        <router-link to="/" class="logo-link">
            <div class="logo-area" :class="{ 'logo-collapsed': collapsed }">
                <img
                    v-if="collapsed"
                    src="@renderer/assets/logo.png"
                    alt="logo"
                    class="logo-icon"
                />
                <template v-else>
                    <img src="@renderer/assets/logo.png" alt="logo" class="logo-img" />
                    <span class="logo-title">研发七部工具包</span>
                </template>
            </div>
        </router-link>

        <el-menu
            :default-active="activeMenu"
            :collapse="collapsed"
            :router="true"
            class="side-menu"
        >
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
    Histogram,
    HomeFilled
} from '@element-plus/icons-vue'

const iconMap: Record<string, Component> = {
    HomeFilled: markRaw(HomeFilled),
    Histogram: markRaw(Histogram)
}

const collapsed = defineModel<boolean>('collapsed', { default: false })

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)

const menuRoutes = computed(() =>
    router.options.routes.filter((r) => r.meta?.title && r.meta?.icon)
)

</script>

<style scoped>
.side-nav {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.logo-area {
    display: flex;
    align-items: flex-end;
    padding: 14px 20px;
    height: 56px;
    box-sizing: border-box;
    overflow: hidden;
    background-color: #ffffff;
    transition: padding 0.3s ease-in-out;
}

.logo-area.logo-collapsed {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px;
    gap: 4px;
}

.logo-link {
    text-decoration: none;
    color: inherit;
    min-width: 0;
}

.logo-collapsed .logo-link {
    flex: none;
}

.logo-img {
    height: 20px;
    width: auto;
    flex-shrink: 0;
}

.logo-icon {
    max-width: 44px;
    height: auto;
}

.logo-title {
    margin-left: 8px;
    font-size: 12px;
    font-weight: 600;
    color: #909399;
    white-space: nowrap;
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

.menu-spacer {
    flex: 1;
}
</style>
