<template>
    <AppProviders>
        <div class="app-layout">
            <SideNav v-model:collapsed="collapsed" />
            <main class="app-main">
                <div class="app-panel">
                    <router-view />
                </div>
            </main>
        </div>
        <CommandPalette v-model:visible="paletteVisible" />
        <LoginModal />
        <n-modal
            v-model:show="quitVisible"
            preset="dialog"
            title="退出应用"
            content="确定要退出应用吗？"
            positive-text="退出"
            negative-text="取消"
            :show-icon="false"
            @positive-click="doQuit"
        />
    </AppProviders>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { NModal } from 'naive-ui'
import AppProviders from '@renderer/components/AppProviders.vue'
import SideNav from '@renderer/components/SideNav.vue'
import CommandPalette from '@renderer/components/CommandPalette.vue'
import LoginModal from '@renderer/components/LoginModal.vue'
import { useAccountStore } from '@renderer/stores/account'

const account = useAccountStore()

const collapsed = ref(false)
const paletteVisible = ref(false)
const quitVisible = ref(false)

const doQuit = (): void => {
    window.electronAPI?.confirmQuit()
}

const handleKeydown = (e: KeyboardEvent): void => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault()
        paletteVisible.value = !paletteVisible.value
    }
}

const syncDarkClass = (): void => {
    const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', dark)
}

onMounted(() => {
    syncDarkClass()
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncDarkClass)
    window.addEventListener('keydown', handleKeydown)
    window.electronAPI?.onConfirmQuit(() => {
        quitVisible.value = true
    })
    // 登录不是必需的：连不上内网时工具照常用，只有查历史记录要登录
    account.restore()
})

onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.app-layout {
    display: flex;
    height: 100vh;
    background: var(--canvas);
}

.app-main {
    display: flex;
    flex: 1;
    min-width: 0;
    padding: 8px 8px 8px 0;
}

.app-panel {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: var(--shadow-sm);
}
</style>
