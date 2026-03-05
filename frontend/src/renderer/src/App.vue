<template>
    <el-container class="app-layout">
        <el-aside
            :width="sideWidth"
            class="app-aside"
        >
            <SideNav v-model:collapsed="collapsed" />
        </el-aside>
        <el-main class="app-main">
            <router-view />
        </el-main>
    </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
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
    transition: width 0.3s ease;
    border-right: 1px solid #e5e6eb;
}

.app-main {
    padding: 20px 24px 24px;
    background-color: #f5f5f7;
    overflow-y: auto;
}
</style>
