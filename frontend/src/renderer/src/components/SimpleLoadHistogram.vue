<template>
    <div class="chart-card">
        <div class="chart-head">
            <n-tabs
                type="segment"
                size="small"
                :value="store.activeComponent"
                :animated="false"
                class="component-tabs"
                :style="{ width: `${store.participating.length * TAB_WIDTH}px` }"
                @update:value="selectComponent"
            >
                <n-tab v-for="component in store.participating" :key="component" :name="component">
                    {{ component }}
                </n-tab>
            </n-tabs>
            <span class="brush-sum">
                <span class="brush-label">X 轴区间选择合计</span>
                <span class="brush-value num">{{ brushPercentText }}</span>
                <span class="brush-count">{{ brushCountText }}</span>
            </span>
        </div>
        <div ref="chartRef" class="chart" />
    </div>
</template>

<script setup lang="ts">
// 分布图：选中分量的加权时间占比，每根柱是一个小区间。图表配置照搬网页版的 ECharts（工具栏的区域缩放、
// X 轴区间选择、清除选择、恢复），使用者习惯了这套用法；框选几根柱，标题栏给出它们的占比合计
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { NTab, NTabs } from 'naive-ui'
import * as echarts from 'echarts'
import type { ComponentStats } from '@renderer/api/simpleLoad'
import { useDarkClass } from '@renderer/composables/useDarkClass'
import { useSimpleLoadStore } from '@renderer/stores/simpleLoad'

interface BrushSelectedParams {
    batch?: { selected?: { seriesIndex: number; dataIndex: number[] }[] }[]
}

// 分段控件每段的宽度，放得下 Mx[KNm] 这样的分量名
const TAB_WIDTH = 78

const store = useSimpleLoadStore()
const isDark = useDarkClass()

const chartRef = ref<HTMLDivElement | null>(null)
const chart = shallowRef<echarts.ECharts | null>(null)
const selectedIndices = ref<number[]>([])

const stats = computed(() => store.loaded?.stats[store.activeComponent])

const formatPercentFixed = (value: number): string => `${(value * 100).toFixed(2)}%`

const brushPercentText = computed(() => {
    const shares = stats.value?.share ?? []
    const total = selectedIndices.value.reduce((sum, index) => sum + (shares[index] ?? 0), 0)
    return formatPercentFixed(total)
})

const brushCountText = computed(() =>
    selectedIndices.value.length > 0 ? `${selectedIndices.value.length} 个区间` : '未框选'
)

const selectComponent = (value: string | number): void => {
    const hit = store.participating.find((component) => component === value)
    if (hit) store.selectedComponent = hit
}

const handleBrushSelected = (params: BrushSelectedParams): void => {
    const selected = params.batch?.[0]?.selected ?? []
    selectedIndices.value = selected.find((item) => item.seriesIndex === 0)?.dataIndex ?? []
}

// 框选的颜色取品牌蓝，组件里不写色值
const cssVar = (name: string): string =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim()

const buildOption = (data: ComponentStats): echarts.EChartsOption => ({
    // 暗色主题自带深蓝底，改透明，跟着面板色走
    backgroundColor: 'transparent',
    title: { show: false },
    toolbox: {
        show: true,
        showTitle: false,
        top: 10,
        right: 12,
        itemSize: 18,
        itemGap: 10,
        feature: {
            dataZoom: {
                show: true,
                title: { zoom: '区域缩放', back: '缩放还原' },
                yAxisIndex: false
            },
            brush: {
                show: true,
                type: ['lineX', 'clear'],
                title: { lineX: 'X 轴区间选择', clear: '清除选择' }
            },
            restore: { show: true, title: '恢复' }
        },
        tooltip: {
            show: true,
            formatter: (param: unknown) => (param as { title: string }).title
        }
    },
    brush: {
        toolbox: ['lineX', 'clear'],
        xAxisIndex: 0,
        brushMode: 'single',
        throttleType: 'debounce',
        throttleDelay: 80,
        brushStyle: {
            borderWidth: 1,
            color: cssVar('--accent-soft'),
            borderColor: cssVar('--accent')
        }
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        valueFormatter: (value) => formatPercentFixed(Number(value))
    },
    // 每根柱的区间写成 pandas 的写法，和网页版一样，如 (-1000, -990]
    xAxis: {
        type: 'category',
        data: data.binLeft.map((left, index) => `(${left}, ${data.binRight[index]}]`),
        axisLabel: { rotate: 0, interval: 0, hideOverlap: true, margin: 10, fontSize: 11 }
    },
    grid: { top: 64, right: 24, bottom: 28, left: 24, containLabel: true },
    yAxis: {
        type: 'value',
        axisLabel: { formatter: (value: number) => formatPercentFixed(value) }
    },
    series: [{ data: data.share, type: 'bar', name: '占比' }]
})

const render = (): void => {
    const data = stats.value
    if (!chart.value || !data) return
    // 整个换掉配置，旧的框选也跟着清掉
    chart.value.setOption(buildOption(data), true)
    selectedIndices.value = []
}

// 亮色用 ECharts 默认主题，和网页版一样；暗色用它自带的 dark 主题。切换主题要重建实例
const init = (): void => {
    const el = chartRef.value
    if (!el) return
    chart.value?.dispose()
    const instance = echarts.init(el, isDark.value ? 'dark' : undefined)
    instance.on('brushSelected', (params) => handleBrushSelected(params as BrushSelectedParams))
    chart.value = instance
    render()
}

// 容器跟着窗口、侧栏和上面的区间表变大小
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
    init()
    if (!chartRef.value) return
    resizeObserver = new ResizeObserver(() => chart.value?.resize())
    resizeObserver.observe(chartRef.value)
})

watch(stats, render)
watch(isDark, init)

onBeforeUnmount(() => {
    resizeObserver?.disconnect()
    chart.value?.dispose()
    chart.value = null
})
</script>

<style scoped>
.chart-card {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 300px;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 10px;
}

.chart-head {
    display: flex;
    flex-shrink: 0;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 16px;
    padding: 7px 12px;
    border-bottom: 1px solid var(--divider);
}

.component-tabs {
    max-width: 100%;
}

.brush-sum {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-size: 12px;
    color: var(--text-3);
    white-space: nowrap;
}

.brush-label {
    color: var(--text-2);
}

.brush-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
}

.chart {
    flex: 1;
    min-height: 0;
}
</style>
