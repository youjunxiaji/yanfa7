<template>
    <div class="settings-page">
        <h2 class="settings-title">设置</h2>

        <div class="settings-section">
            <div class="settings-card">
                <!-- 外观 -->
                <div class="setting-item">
                    <div class="setting-label">
                        <el-icon :size="18"><Sunny v-if="!isDark" /><Moon v-else /></el-icon>
                        <span>外观</span>
                    </div>
                    <div class="appearance-options">
                        <button
                            v-for="opt in appearanceOptions"
                            :key="opt.value"
                            class="appearance-btn"
                            :class="{ active: appearance === opt.value }"
                            @click="setAppearance(opt.value)"
                        >
                            <el-icon :size="16"><component :is="opt.icon" /></el-icon>
                            <span>{{ opt.label }}</span>
                        </button>
                    </div>
                </div>

                <div class="setting-divider" />

                <!-- 语言 -->
                <div class="setting-item">
                    <div class="setting-label">
                        <el-icon :size="18"><ChatLineSquare /></el-icon>
                        <span>语言</span>
                    </div>
                    <el-select
                        v-model="language"
                        class="lang-select"
                        size="default"
                        :disabled="true"
                    >
                        <el-option label="简体中文" value="zh-CN" />
                        <el-option label="English" value="en" />
                    </el-select>
                </div>
            </div>
            <p class="setting-hint">语言切换功能即将推出</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw, type Component } from 'vue'
import { Sunny, Moon, Monitor, ChatLineSquare } from '@element-plus/icons-vue'

type AppearanceMode = 'light' | 'dark' | 'system'

interface AppearanceOption {
    value: AppearanceMode
    label: string
    icon: Component
}

const appearanceOptions: AppearanceOption[] = [
    { value: 'light', label: '浅色', icon: markRaw(Sunny) },
    { value: 'dark', label: '深色', icon: markRaw(Moon) },
    { value: 'system', label: '跟随系统', icon: markRaw(Monitor) }
]

const appearance = ref<AppearanceMode>('light')
const language = ref('zh-CN')

const mql = window.matchMedia('(prefers-color-scheme: dark)')
const isDark = ref(mql.matches)

const setAppearance = async (mode: AppearanceMode): Promise<void> => {
    appearance.value = mode
    const dark = await window.electronAPI.theme.set(mode)
    isDark.value = dark
}

onMounted(async () => {
    const info = await window.electronAPI.theme.get()
    if (['light', 'dark', 'system'].includes(info.source)) {
        appearance.value = info.source as AppearanceMode
    }
    isDark.value = info.shouldUseDarkColors

    mql.addEventListener('change', (e) => {
        isDark.value = e.matches
    })
})
</script>

<style scoped>
.settings-page {
    max-width: 560px;
    margin: 0 auto;
    padding: 8px 0;
}

.settings-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--settings-text-primary, #1d1d1f);
    margin-bottom: 28px;
}

.settings-card {
    background: var(--settings-card-bg, #ffffff);
    border-radius: 12px;
    padding: 4px 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}

.setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    min-height: 52px;
}

.setting-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 500;
    color: var(--settings-text-primary, #1d1d1f);
}

.setting-divider {
    height: 1px;
    background: var(--settings-divider, #f0f0f3);
    margin: 0 20px;
}

.appearance-options {
    display: flex;
    gap: 6px;
    background: var(--settings-seg-bg, #f0f0f3);
    border-radius: 8px;
    padding: 3px;
}

.appearance-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--settings-text-secondary, #86868b);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.appearance-btn:hover {
    color: var(--settings-text-primary, #1d1d1f);
}

.appearance-btn.active {
    background: var(--settings-seg-active-bg, #ffffff);
    color: var(--settings-text-primary, #1d1d1f);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.lang-select {
    width: 140px;
}

.setting-hint {
    font-size: 12px;
    color: var(--settings-text-tertiary, #c7c7cc);
    margin-top: 8px;
    padding-left: 4px;
}
</style>
