import { markRaw, type Component } from 'vue'
import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { BookOpen, ChartColumn, ChartSpline, House, Settings } from '@lucide/vue'
import { ToolTone } from '@renderer/constants/ui'

// 工具页的完整名称、一句话说明和色调：页面标题栏和首页工具卡都读这里
interface ToolInfo {
    name: string
    desc: string
    tone: ToolTone
}

declare module 'vue-router' {
    interface RouteMeta {
        title?: string
        icon?: Component
        bottomNav?: boolean
        tool?: ToolInfo
    }
}

// 侧栏、命令面板、首页都从这份路由读标题和图标；带 bottomNav 的放到侧栏底部
const routes: RouteRecordRaw[] = [
    {
        path: '/',
        name: 'Home',
        meta: { title: '首页', icon: markRaw(House) },
        component: () => import('@renderer/views/HomeView.vue')
    },
    {
        path: '/edge-stress',
        name: 'EdgeStress',
        meta: {
            title: '边缘应力',
            icon: markRaw(ChartSpline),
            tool: {
                name: '边缘应力分析',
                desc: 'HTM 数据解析、去峰处理与报告生成',
                tone: ToolTone.BLUE
            }
        },
        component: () => import('@renderer/views/EdgeStressView.vue')
    },
    {
        path: '/pmax',
        name: 'Pmax',
        meta: {
            title: 'Pmax 占比',
            icon: markRaw(ChartColumn),
            tool: {
                name: 'Pmax 时间占比',
                desc: '轴承最大接触应力区间分析与柱状图生成',
                tone: ToolTone.GREEN
            }
        },
        component: () => import('@renderer/views/PmaxView.vue')
    },
    {
        path: '/docs',
        name: 'Docs',
        meta: { title: '文档', icon: markRaw(BookOpen), bottomNav: true },
        component: () => import('@renderer/views/DocsView.vue')
    },
    {
        path: '/settings',
        name: 'Settings',
        meta: { title: '设置', icon: markRaw(Settings), bottomNav: true },
        component: () => import('@renderer/views/SettingsView.vue')
    }
]

const router = createRouter({
    history: createWebHashHistory(),
    routes
})

export default router
