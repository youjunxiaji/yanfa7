<template>
    <aside class="side-nav" :class="{ 'is-collapsed': collapsed }">
        <router-link to="/" class="brand">
            <img class="brand-logo" src="@renderer/assets/logo.png" alt="TMB" />
            <template v-if="!collapsed">
                <span class="brand-sep" />
                <span class="brand-name">研发七部工具包</span>
            </template>
        </router-link>

        <nav
            v-for="section in sections"
            :key="section.key"
            class="nav-section"
            :class="{ 'is-bottom': section.bottom }"
        >
            <template v-if="section.label">
                <div v-if="!collapsed" class="nav-label">{{ section.label }}</div>
                <div v-else class="nav-divider" />
            </template>
            <n-tooltip
                v-for="item in section.items"
                :key="item.path"
                placement="right"
                :disabled="!collapsed"
                :delay="200"
            >
                <template #trigger>
                    <router-link
                        :to="item.path"
                        class="nav-item"
                        :class="{ 'is-active': route.path === item.path }"
                    >
                        <component :is="item.meta?.icon" :size="16" />
                        <span class="nav-text">{{ item.meta?.title }}</span>
                    </router-link>
                </template>
                {{ item.meta?.title }}
            </n-tooltip>
        </nav>

        <div class="nav-footer">
            <span v-if="!collapsed" class="nav-version">v{{ version }}</span>
            <n-tooltip placement="right" :delay="300">
                <template #trigger>
                    <button class="icon-btn" @click="collapsed = !collapsed">
                        <PanelLeftOpen v-if="collapsed" :size="16" />
                        <PanelLeftClose v-else :size="16" />
                    </button>
                </template>
                {{ collapsed ? '展开侧栏' : '收起侧栏' }}
            </n-tooltip>
        </div>
    </aside>
</template>

<script setup lang="ts">
// 侧栏只放导航，不放搜索框；首页、工具、底部（文档、设置）三组都从路由 meta 读
import { computed } from 'vue'
import { useRoute, useRouter, type RouteRecordRaw } from 'vue-router'
import { NTooltip } from 'naive-ui'
import { PanelLeftClose, PanelLeftOpen } from '@lucide/vue'
import { APP_VERSION } from '@renderer/constants/app'

interface NavSection {
    key: string
    label?: string
    bottom?: boolean
    items: RouteRecordRaw[]
}

const collapsed = defineModel<boolean>('collapsed', { default: false })

const route = useRoute()
const router = useRouter()
const version = APP_VERSION

const sections = computed<NavSection[]>(() => {
    const navRoutes = router.options.routes.filter((r) => r.meta?.title && r.meta?.icon)
    return [
        { key: 'main', items: navRoutes.filter((r) => !r.meta?.tool && !r.meta?.bottomNav) },
        { key: 'tools', label: '工具', items: navRoutes.filter((r) => r.meta?.tool) },
        { key: 'bottom', bottom: true, items: navRoutes.filter((r) => r.meta?.bottomNav) }
    ]
})
</script>

<style scoped>
.side-nav {
    display: flex;
    flex-shrink: 0;
    flex-direction: column;
    width: 216px;
    padding: 10px 8px 8px;
    overflow: hidden;
    transition: width 0.2s ease;
}

.side-nav.is-collapsed {
    width: 56px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 9px;
    height: 36px;
    margin-bottom: 12px;
    padding: 0 8px;
    color: inherit;
    text-decoration: none;
    white-space: nowrap;
}

.brand-logo {
    flex-shrink: 0;
    width: auto;
    height: 13px;
}

.brand-sep {
    flex-shrink: 0;
    width: 1px;
    height: 12px;
    background: var(--border-strong);
}

.brand-name {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.01em;
}

.is-collapsed .brand {
    justify-content: center;
    padding: 0;
}

.is-collapsed .brand-logo {
    height: 9px;
}

.nav-section {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.nav-section.is-bottom {
    margin-top: auto;
}

.nav-label {
    display: flex;
    align-items: center;
    height: 28px;
    margin-top: 10px;
    padding: 0 9px;
    font-size: 12px;
    color: var(--text-3);
    white-space: nowrap;
}

.nav-divider {
    height: 1px;
    margin: 10px 8px;
    background: var(--divider);
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 32px;
    padding: 0 9px;
    font-weight: 500;
    color: var(--text-2);
    text-decoration: none;
    white-space: nowrap;
    border-radius: 7px;
    user-select: none;
    transition:
        background 0.12s,
        color 0.12s;
}

.nav-item .lucide {
    color: var(--text-3);
    transition: color 0.12s;
}

.nav-item:hover {
    color: var(--text-1);
    background: var(--hover);
}

.nav-item:hover .lucide {
    color: var(--text-2);
}

.nav-item.is-active {
    color: var(--text-1);
    background: var(--nav-active);
    box-shadow:
        0 0 0 1px var(--nav-active-ring),
        var(--shadow-sm);
}

.nav-item.is-active .lucide {
    color: var(--accent);
}

.is-collapsed .nav-item {
    justify-content: center;
    padding: 0;
}

.is-collapsed .nav-text {
    display: none;
}

.nav-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 34px;
    margin-top: 6px;
    padding: 0 2px 0 9px;
}

.is-collapsed .nav-footer {
    justify-content: center;
    padding: 0;
}

.nav-version {
    font-size: 12px;
    color: var(--text-3);
    white-space: nowrap;
}
</style>
