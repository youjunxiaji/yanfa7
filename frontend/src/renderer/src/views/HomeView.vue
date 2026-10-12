<template>
    <div class="home">
        <div class="home-inner">
            <img class="home-logo" src="@renderer/assets/logo.png" alt="TMB" />
            <h1 class="home-title">研发七部工具包</h1>
            <div class="home-desc">
                <span>轴承数据分析与报告生成工具集</span>
                <button class="shortcut-chip" @click="openPalette">
                    <span class="kbd-group">
                        <kbd>{{ isMac ? '⌘' : 'Ctrl' }}</kbd>
                        <kbd>P</kbd>
                    </span>
                    快速跳转
                </button>
            </div>

            <div class="tool-grid">
                <router-link
                    v-for="tool in tools"
                    :key="tool.path"
                    :to="tool.path"
                    class="tool-card"
                >
                    <div class="tool-card-top">
                        <div class="tool-icon" :class="`is-${tool.tone}`">
                            <component :is="tool.icon" :size="18" />
                        </div>
                        <ArrowRight class="tool-arrow" :size="16" />
                    </div>
                    <div>
                        <div class="tool-name">{{ tool.name }}</div>
                        <div class="tool-desc">{{ tool.desc }}</div>
                    </div>
                </router-link>
            </div>

            <div class="home-footer">
                <span>v{{ version }}</span>
                <span>·</span>
                <span>TMB®</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@lucide/vue'
import { APP_VERSION } from '@renderer/constants/app'

const router = useRouter()
const version = APP_VERSION
const isMac = window.electron.process.platform === 'darwin'

const tools = computed(() =>
    router.options.routes.flatMap((r) =>
        r.meta?.tool ? [{ path: r.path, icon: r.meta.icon, ...r.meta.tool }] : []
    )
)

const openPalette = (): void => {
    window.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'p', metaKey: isMac, ctrlKey: !isMac })
    )
}
</script>

<style scoped>
.home {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    min-height: 0;
    padding: 0 32px;
    overflow-y: auto;
}

.home-inner {
    width: 100%;
    max-width: 600px;
    margin: auto 0;
    padding: 48px 0 24px;
}

.home-logo {
    display: block;
    height: 22px;
}

.home-title {
    margin: 20px 0 6px;
    font-size: 26px;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.02em;
}

.home-desc {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: var(--text-2);
}

.shortcut-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 26px;
    padding: 0 10px 0 4px;
    font-size: 12px;
    color: var(--text-2);
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 999px;
    cursor: pointer;
    transition:
        border-color 0.15s,
        color 0.15s;
}

.shortcut-chip:hover {
    color: var(--text-1);
    border-color: var(--border-strong);
}

.kbd-group {
    display: flex;
    gap: 2px;
}

.tool-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 32px;
}

.tool-card {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
    color: inherit;
    text-decoration: none;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition:
        border-color 0.15s,
        box-shadow 0.15s,
        transform 0.15s;
}

.tool-card:hover {
    border-color: var(--border-strong);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

.tool-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.tool-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 9px;
}

.tool-icon.is-blue {
    color: var(--accent);
    background: var(--accent-soft);
}

.tool-icon.is-green {
    color: var(--success);
    background: var(--success-soft);
}

.tool-arrow {
    color: var(--text-3);
    transition:
        transform 0.15s,
        color 0.15s;
}

.tool-card:hover .tool-arrow {
    color: var(--text-1);
    transform: translateX(2px);
}

.tool-name {
    font-size: 14px;
    font-weight: 600;
}

.tool-desc {
    margin-top: 2px;
    font-size: 12.5px;
    color: var(--text-3);
}

.home-footer {
    display: flex;
    gap: 6px;
    margin-top: 40px;
    font-size: 12px;
    color: var(--text-3);
}
</style>
