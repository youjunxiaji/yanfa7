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
    <CommandPalette v-model:visible="paletteVisible" />

    <!-- 退出确认 -->
    <Teleport to="body">
        <Transition name="quit-fade">
            <div v-if="quitVisible" class="quit-overlay" @click.self="quitVisible = false">
                <Transition name="quit-dialog" appear>
                    <div v-if="quitVisible" class="quit-dialog">
                        <p class="quit-message">确定要退出应用吗？</p>
                        <div class="quit-actions">
                            <button class="quit-btn quit-btn-cancel" @click="quitVisible = false">取消</button>
                            <button class="quit-btn quit-btn-confirm" @click="doQuit">退出</button>
                        </div>
                    </div>
                </Transition>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import SideNav from '@renderer/components/SideNav.vue'
import CommandPalette from '@renderer/components/CommandPalette.vue'

const collapsed = ref(false)
const sideWidth = computed(() => (collapsed.value ? '64px' : '200px'))

const paletteVisible = ref(false)
const quitVisible = ref(false)

function doQuit(): void {
    window.electronAPI.confirmQuit()
}

function handleKeydown(e: KeyboardEvent): void {
    if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault()
        paletteVisible.value = !paletteVisible.value
    }
}

async function restoreTheme(): Promise<void> {
    const saved = await window.electronAPI.settings.get('appearance') as string | null
    let dark = false
    if (saved === 'dark') {
        dark = true
    } else if (saved === 'system') {
        dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    document.documentElement.classList.toggle('dark', dark)
}

onMounted(() => {
    restoreTheme()
    window.addEventListener('keydown', handleKeydown)
    window.electronAPI.onConfirmQuit(() => {
        quitVisible.value = true
    })
})
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style>
.app-layout {
    height: 100vh;
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

/* ========== 退出确认对话框 ========== */
.quit-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(0, 0, 0, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
}

.quit-dialog {
    background: #fff;
    border-radius: 14px;
    padding: 28px 32px 20px;
    width: 320px;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.14), 0 4px 16px rgba(0, 0, 0, 0.08);
    text-align: center;
}

.quit-message {
    font-size: 15px;
    font-weight: 500;
    color: #1d1d1f;
    margin: 0 0 24px;
}

.quit-actions {
    display: flex;
    gap: 12px;
}

.quit-btn {
    flex: 1;
    height: 36px;
    border-radius: 8px;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.15s;
}

.quit-btn:active {
    opacity: 0.75;
}

.quit-btn-cancel {
    background: #f0f0f3;
    color: #1d1d1f;
}

.quit-btn-cancel:hover {
    background: #e5e5ea;
}

.quit-btn-confirm {
    background: var(--el-color-primary);
    color: #fff;
}

.quit-btn-confirm:hover {
    background: var(--el-color-primary-light-3);
}

/* ========== 退出对话框动画 ========== */
.quit-fade-enter-active,
.quit-fade-leave-active {
    transition: opacity 0.2s ease;
}
.quit-fade-enter-from,
.quit-fade-leave-to {
    opacity: 0;
}

.quit-dialog-enter-active {
    transition: all 0.2s ease-out;
}
.quit-dialog-leave-active {
    transition: all 0.15s ease-in;
}
.quit-dialog-enter-from {
    opacity: 0;
    transform: scale(0.95);
}
.quit-dialog-leave-to {
    opacity: 0;
    transform: scale(0.97);
}
</style>
