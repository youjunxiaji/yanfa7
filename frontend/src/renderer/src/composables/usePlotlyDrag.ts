import { ref, onBeforeUnmount, type Ref } from 'vue'
import Plotly from 'plotly.js-dist-min'

const DRAG_HIGHLIGHT_SIZE = 14
const DRAG_HIGHLIGHT_COLOR = '#ff4d4f'
const NORMAL_MARKER_SIZE = 6

export interface DragEndInfo {
    curveNumber: number
    pointNumber: number
    oldY: number
    newY: number
}

export interface PlotlyDrag {
    dragModeEnabled: Ref<boolean>
    toggleDragMode: (el: HTMLElement) => void
    setupDragListeners: (el: HTMLElement) => void
    teardownDragListeners: (el: HTMLElement) => void
    reset: () => void
}

interface DragState {
    active: boolean
    curveNumber: number
    pointNumber: number
    originalY: number
    yArray: number[]
}

// Plotly 内部坐标轴对象里用到的两个成员：像素偏移和像素转数据
interface PlotlyAxis {
    _offset: number
    p2d: (px: number) => number
}

// 拖拽编辑：开启后按住数据点上下拖，松手时回调 onDragEnd；开关由预览窗口的「拖拽编辑」按钮调 toggleDragMode
export const usePlotlyDrag = (onDragEnd?: (info: DragEndInfo) => void): PlotlyDrag => {
    const dragModeEnabled = ref(false)
    let dragTargetEl: HTMLElement | null = null
    let previousDragMode: string = 'zoom'

    const drag: DragState = {
        active: false,
        curveNumber: -1,
        pointNumber: -1,
        originalY: 0,
        yArray: []
    }

    const getYAxis = (el: HTMLElement): PlotlyAxis | null => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const fullLayout = (el as any)._fullLayout
        return fullLayout ? fullLayout.yaxis : null
    }

    const pixelToDataY = (el: HTMLElement, clientY: number): number | null => {
        const yaxis = getYAxis(el)
        if (!yaxis) return null
        const rect = el.getBoundingClientRect()
        return yaxis.p2d(clientY - rect.top - yaxis._offset)
    }

    const startDrag = (
        el: HTMLElement,
        curveNumber: number,
        pointNumber: number,
        yData: number[]
    ): void => {
        drag.active = true
        drag.curveNumber = curveNumber
        drag.pointNumber = pointNumber
        drag.originalY = yData[pointNumber]
        drag.yArray = [...yData]

        const markerSizes = drag.yArray.map((_, i) =>
            i === drag.pointNumber ? DRAG_HIGHLIGHT_SIZE : NORMAL_MARKER_SIZE
        )
        Plotly.restyle(
            el,
            {
                'marker.size': [markerSizes],
                'marker.color': [
                    drag.yArray.map((_, i) => (i === drag.pointNumber ? DRAG_HIGHLIGHT_COLOR : ''))
                ]
            },
            [drag.curveNumber]
        )
    }

    const onMouseMove = (e: MouseEvent): void => {
        if (!drag.active || !dragTargetEl) return
        e.preventDefault()
        const newY = pixelToDataY(dragTargetEl, e.clientY)
        if (newY == null || !isFinite(newY) || newY < 0) return

        drag.yArray[drag.pointNumber] = newY
        Plotly.restyle(dragTargetEl, { y: [[...drag.yArray]] }, [drag.curveNumber])
    }

    const endDrag = (): void => {
        if (!drag.active || !dragTargetEl) return

        const finalY = drag.yArray[drag.pointNumber]
        const changed = finalY !== drag.originalY

        Plotly.restyle(
            dragTargetEl,
            {
                'marker.size': [NORMAL_MARKER_SIZE],
                'marker.color': [null]
            },
            [drag.curveNumber]
        )

        if (changed && onDragEnd) {
            onDragEnd({
                curveNumber: drag.curveNumber,
                pointNumber: drag.pointNumber,
                oldY: drag.originalY,
                newY: finalY
            })
        }

        drag.active = false
        drag.curveNumber = -1
        drag.pointNumber = -1
        drag.originalY = 0
        drag.yArray = []
    }

    const onPlotMouseDown = (el: HTMLElement, e: MouseEvent): void => {
        if (!dragModeEnabled.value) return

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const hoverData = (el as any)._hoverdata
        if (!hoverData || hoverData.length === 0) return

        const pt = hoverData[0]
        if (pt.curveNumber == null || pt.pointNumber == null) return

        e.preventDefault()
        e.stopPropagation()
        dragTargetEl = el
        startDrag(el, pt.curveNumber, pt.pointNumber, pt.data.y)
    }

    const toggleDragMode = (el: HTMLElement): void => {
        dragModeEnabled.value = !dragModeEnabled.value
        dragTargetEl = dragModeEnabled.value ? el : null

        if (dragModeEnabled.value) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const currentMode = (el as any)._fullLayout?.dragmode
            if (currentMode && currentMode !== false) {
                previousDragMode = currentMode
            }
            Plotly.relayout(el, { dragmode: false as unknown as string })
        } else {
            if (drag.active) endDrag()
            Plotly.relayout(el, { dragmode: previousDragMode })
        }
    }

    const boundMouseDownHandlers = new WeakMap<HTMLElement, (e: MouseEvent) => void>()

    const boundRelayoutHandlers = new WeakMap<
        HTMLElement,
        (data: Record<string, unknown>) => void
    >()

    // 在 Plotly 工具条上切到缩放、平移等模式时，退出拖拽编辑
    const onRelayout = (data: Record<string, unknown>): void => {
        if (!dragModeEnabled.value) return
        if ('dragmode' in data && data.dragmode !== false) {
            dragModeEnabled.value = false
            if (drag.active) endDrag()
            dragTargetEl = null
        }
    }

    const setupDragListeners = (el: HTMLElement): void => {
        const plotArea = el.querySelector('.nsewdrag') as HTMLElement | null
        const target = plotArea || el

        const handler = (e: MouseEvent): void => onPlotMouseDown(el, e)
        boundMouseDownHandlers.set(el, handler)
        target.addEventListener('mousedown', handler)

        boundRelayoutHandlers.set(el, onRelayout)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(el as any).on('plotly_relayout', onRelayout)
    }

    const teardownDragListeners = (el: HTMLElement): void => {
        const plotArea = el.querySelector('.nsewdrag') as HTMLElement | null
        const target = plotArea || el
        const handler = boundMouseDownHandlers.get(el)
        if (handler) {
            target.removeEventListener('mousedown', handler)
            boundMouseDownHandlers.delete(el)
        }

        const relayoutHandler = boundRelayoutHandlers.get(el)
        if (relayoutHandler) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ;(el as any).removeListener?.('plotly_relayout', relayoutHandler)
            boundRelayoutHandlers.delete(el)
        }
    }

    const reset = (): void => {
        dragModeEnabled.value = false
        dragTargetEl = null
        drag.active = false
        drag.curveNumber = -1
        drag.pointNumber = -1
        drag.originalY = 0
        drag.yArray = []
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', endDrag)

    onBeforeUnmount(() => {
        document.removeEventListener('mousemove', onMouseMove)
        document.removeEventListener('mouseup', endDrag)
    })

    return {
        dragModeEnabled,
        toggleDragMode,
        setupDragListeners,
        teardownDragListeners,
        reset
    }
}
