import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        name: 'Home',
        meta: { title: '首页', icon: 'HomeFilled' },
        component: () => import('@renderer/views/HomeView.vue')
    },
    {
        path: '/edge-stress',
        name: 'EdgeStress',
        meta: { title: '边缘应力', icon: 'Histogram' },
        component: () => import('@renderer/views/EdgeStressView.vue')
    },
    {
        path: '/docs',
        name: 'Docs',
        meta: { title: '文档', icon: 'Document', bottomNav: true },
        component: () => import('@renderer/views/DocsView.vue')
    },
    {
        path: '/settings',
        name: 'Settings',
        meta: { title: '设置', icon: 'Setting', bottomNav: true },
        component: () => import('@renderer/views/SettingsView.vue')
    }
]

const router = createRouter({
    history: createWebHashHistory(),
    routes
})

export default router
