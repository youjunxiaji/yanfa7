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
    }
]

const router = createRouter({
    history: createWebHashHistory(),
    routes
})

export default router
