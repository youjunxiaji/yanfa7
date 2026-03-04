import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'EdgeStress',
    component: () => import('@renderer/views/EdgeStressView.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
