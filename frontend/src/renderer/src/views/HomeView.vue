<template>
    <div class="home-page">
        <div class="home-content">
            <!-- 欢迎区域 -->
            <div class="welcome-section">
                <img src="@renderer/assets/logo.png" alt="logo" class="welcome-logo" />
                <h1 class="welcome-title">研发七部工具包</h1>
                <p class="welcome-desc">
                    轴承数据分析与报告生成工具集
                    <span class="welcome-sep">·</span>
                    <span class="shortcut-link" @click="openPalette">
                        <kbd>{{ isMac ? '⌘' : 'Ctrl' }}</kbd><kbd>P</kbd> 快速跳转
                    </span>
                </p>
            </div>

            <!-- 工具卡片网格 -->
            <div class="tools-grid">
                <div
                    v-for="tool in tools"
                    :key="tool.path"
                    class="tool-card"
                    @click="router.push(tool.path)"
                >
                    <div class="tool-icon-wrapper" :style="{ background: tool.bgColor }">
                        <el-icon :size="28" :color="tool.iconColor">
                            <component :is="tool.icon" />
                        </el-icon>
                    </div>
                    <div class="tool-info">
                        <span class="tool-name">{{ tool.name }}</span>
                        <span class="tool-desc">{{ tool.desc }}</span>
                    </div>
                    <el-icon class="tool-arrow" :size="16" color="#c0c4cc">
                        <ArrowRight />
                    </el-icon>
                </div>
            </div>
        </div>

        <!-- 底部版本信息 -->
        <div class="home-footer">
            <span>v{{ version }}</span>
            <span class="footer-sep">·</span>
            <span>TMB®</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { markRaw, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { Histogram, TrendCharts, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const version = __APP_VERSION__
const isMac = window.electron.process.platform === 'darwin'

function openPalette(): void {
    window.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'p', metaKey: isMac, ctrlKey: !isMac })
    )
}

interface ToolItem {
    path: string
    name: string
    desc: string
    icon: Component
    iconColor: string
    bgColor: string
}

const tools: ToolItem[] = [
    {
        path: '/edge-stress',
        name: '边缘应力分析',
        desc: 'HTM 数据解析、去峰处理与报告生成',
        icon: markRaw(Histogram),
        iconColor: '#0071e3',
        bgColor: 'rgba(0, 113, 227, 0.08)'
    },
    {
        path: '/pmax',
        name: 'Pmax时间占比',
        desc: '轴承最大接触应力区间分析与柱状图生成',
        icon: markRaw(TrendCharts),
        iconColor: '#34c759',
        bgColor: 'rgba(52, 199, 89, 0.08)'
    }
]
</script>

<style scoped>
.home-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
    padding: 0 24px;
}

.home-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    max-width: 520px;
}

/* ========== 欢迎区域 ========== */
.welcome-section {
    text-align: center;
    margin-bottom: 48px;
}

.welcome-logo {
    height: 48px;
    width: auto;
    margin-bottom: 16px;
}

.welcome-title {
    font-size: 28px;
    font-weight: 700;
    color: #1d1d1f;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}

.welcome-desc {
    font-size: 15px;
    color: #86868b;
    font-weight: 400;
}

.welcome-sep {
    margin: 0 2px;
}

.shortcut-link {
    cursor: pointer;
    transition: color 0.15s;
}

.shortcut-link:hover {
    color: var(--el-color-primary);
}

.shortcut-link kbd {
    font-size: 11px;
    background: #ededf0;
    border-radius: 3px;
    padding: 1px 4px;
    font-family: inherit;
    margin-right: 1px;
}

/* ========== 工具卡片网格 ========== */
.tools-grid {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.tool-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    cursor: pointer;
    transition: box-shadow 0.2s ease, transform 0.15s ease;
}

.tool-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
    transform: translateY(-1px);
}

.tool-card:active {
    transform: translateY(0);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.tool-icon-wrapper {
    width: 52px;
    height: 52px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.tool-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.tool-name {
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
}

.tool-desc {
    font-size: 13px;
    color: #86868b;
}

.tool-arrow {
    flex-shrink: 0;
}

/* ========== 底部版本信息 ========== */
.home-footer {
    padding: 16px 0 20px;
    font-size: 12px;
    color: #c7c7cc;
    display: flex;
    align-items: center;
    gap: 6px;
}

.footer-sep {
    font-size: 10px;
}
</style>
