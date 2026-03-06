<template>
    <el-container class="app-layout">
        <el-aside
            :width="sideWidth"
            class="app-aside"
        >
            <SideNav v-model:collapsed="collapsed" />
        </el-aside>
        <button class="collapse-trigger" :style="{ left: sideWidth }" @click="collapsed = !collapsed">
            <el-icon :size="12">
                <DArrowLeft v-if="!collapsed" />
                <DArrowRight v-else />
            </el-icon>
        </button>
        <el-main class="app-main">
            <router-view />
        </el-main>
    </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import SideNav from '@renderer/components/SideNav.vue'

const collapsed = ref(false)
const sideWidth = computed(() => (collapsed.value ? '64px' : '200px'))
</script>

<style>
.app-layout {
    min-height: 100vh;
}

.app-aside {
    overflow: hidden;
    transition: width 0.3s ease-in-out;
    border-right: 1px solid #e5e6eb;
}

.collapse-trigger {
    position: fixed;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: 1px solid #e5e6eb;
    background: #ffffff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #909399;
    z-index: 10;
    transition: left 0.3s ease-in-out, color 0.2s, border-color 0.2s, box-shadow 0.2s;
    padding: 0;
}

.collapse-trigger:hover {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary);
    box-shadow: 0 0 4px rgba(64, 158, 255, 0.3);
}

.app-main {
    padding: 20px 24px 24px;
    background-color: #f5f5f7;
    overflow-y: auto;
}
</style>
