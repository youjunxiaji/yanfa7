<template>
    <div class="reading">
        <div class="settings">
            <h1 class="reading-title">设置</h1>

            <div class="group-title">通用</div>
            <div class="settings-card">
                <div class="setting-row">
                    <div class="setting-main">
                        <div class="setting-name">外观</div>
                        <div class="setting-desc">浅色、深色，或跟随系统切换</div>
                    </div>
                    <n-tabs
                        :value="appearance"
                        type="segment"
                        size="small"
                        :animated="false"
                        class="appearance-tabs"
                        @update:value="handleAppearanceChange"
                    >
                        <n-tab v-for="opt in appearanceOptions" :key="opt.value" :name="opt.value">
                            <span class="tab-label">
                                <component :is="opt.icon" :size="14" />
                                {{ opt.label }}
                            </span>
                        </n-tab>
                    </n-tabs>
                </div>

                <div class="setting-row">
                    <div class="setting-main">
                        <div class="setting-name">语言</div>
                        <div class="setting-desc">界面显示语言</div>
                    </div>
                    <n-select
                        v-model:value="language"
                        :options="languageOptions"
                        size="small"
                        disabled
                        class="lang-select"
                    />
                </div>
            </div>
            <p class="setting-hint">语言切换功能即将推出</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw, type Component } from 'vue'
import { NSelect, NTab, NTabs } from 'naive-ui'
import { Monitor, Moon, Sun } from '@lucide/vue'

type AppearanceMode = 'light' | 'dark' | 'system'

interface AppearanceOption {
    value: AppearanceMode
    label: string
    icon: Component
}

const appearanceOptions: AppearanceOption[] = [
    { value: 'light', label: '浅色', icon: markRaw(Sun) },
    { value: 'dark', label: '深色', icon: markRaw(Moon) },
    { value: 'system', label: '跟随系统', icon: markRaw(Monitor) }
]

const languageOptions = [
    { label: '简体中文', value: 'zh-CN' },
    { label: 'English', value: 'en' }
]

const appearance = ref<AppearanceMode>('light')
const language = ref('zh-CN')

const setAppearance = async (mode: AppearanceMode): Promise<void> => {
    appearance.value = mode
    await window.electronAPI.theme.set(mode)
}

const handleAppearanceChange = (value: string | number): void => {
    const option = appearanceOptions.find((opt) => opt.value === value)
    if (option) setAppearance(option.value)
}

onMounted(async () => {
    const info = await window.electronAPI.theme.get()
    const option = appearanceOptions.find((opt) => opt.value === info.source)
    if (option) appearance.value = option.value
})
</script>

<style scoped>
.settings {
    max-width: 600px;
    margin: 0 auto;
    padding: 40px 32px;
}

.group-title {
    margin: 0 0 8px 2px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-3);
}

.settings-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.setting-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 16px;
}

.setting-row + .setting-row {
    border-top: 1px solid var(--divider);
}

.setting-main {
    flex: 1;
    min-width: 0;
}

.setting-name {
    font-weight: 500;
}

.setting-desc {
    margin-top: 2px;
    font-size: 12px;
    color: var(--text-3);
}

.appearance-tabs {
    flex-shrink: 0;
    width: 272px;
}

.tab-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.lang-select {
    width: 160px;
}

.setting-hint {
    margin: 8px 0 0 2px;
    font-size: 12px;
    color: var(--text-3);
}
</style>
