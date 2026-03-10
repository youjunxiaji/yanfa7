import { ref, onBeforeUnmount } from 'vue'
import Plotly from 'plotly.js-dist-min'
import dragIconSvg from '@renderer/assets/drag.svg?raw'

export const DRAG_ICON_SVG = { svg: dragIconSvg }

const DRAG_HIGHLIGHT_SIZE = 14
const DRAG_HIGHLIGHT_COLOR = '#ff4d4f'
const NORMAL_MARKER_SIZE = 6

export interface DragEndInfo {
    curveNumber: number
    pointNumber: number
    oldY: number
    newY: number
}

interface DragState {
    active: boolean
    curveNumber: number
    pointNumber: number
    originalY: number
    yArray: number[]
}

export function usePlotlyDrag(onDragEnd?: (info: DragEndInfo) => void) {
    const dragModeEnabled = ref(false)
    let dragTargetEl: HTMLElement | null = null
    let previousDragMode: string = 'zoom'

    const drag: DragState = {
        active: false,
        curveNumber: -1,
        pointNumber: -1,
        originalY: 0,
        yArray: [],
    }

    function getPlotlyAxis(el: HTMLElement) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const fullLayout = (el as any)._fullLayout
        if (!fullLayout) return null
        return { xaxis: fullLayout.xaxis, yaxis: fullLayout.yaxis }
    }

    function pixelToDataY(el: HTMLElement, clientY: number): number | null {
        const axes = getPlotlyAxis(el)
        if (!axes) return null
        const rect = el.getBoundingClientRect()
        const yOffset = axes.yaxis._offset
        const pixelInDiv = clientY - rect.top
        return axes.yaxis.p2d(pixelInDiv - yOffset)
    }

    function startDrag(el: HTMLElement, curveNumber: number, pointNumber: number, yData: number[]) {
        drag.active = true
        drag.curveNumber = curveNumber
        drag.pointNumber = pointNumber
        drag.originalY = yData[pointNumber]
        drag.yArray = [...yData]

        const markerSizes = drag.yArray.map((_, i) =>
            i === drag.pointNumber ? DRAG_HIGHLIGHT_SIZE : NORMAL_MARKER_SIZE
        )
        Plotly.restyle(el, {
            'marker.size': [markerSizes],
            'marker.color': [
                drag.yArray.map((_, i) =>
                    i === drag.pointNumber ? DRAG_HIGHLIGHT_COLOR : ''
                ),
            ],
        }, [drag.curveNumber])
    }

    function onMouseMove(e: MouseEvent) {
        if (!drag.active || !dragTargetEl) return
        e.preventDefault()
        const newY = pixelToDataY(dragTargetEl, e.clientY)
        if (newY == null || !isFinite(newY) || newY < 0) return

        drag.yArray[drag.pointNumber] = newY
        Plotly.restyle(dragTargetEl, { y: [[...drag.yArray]] }, [drag.curveNumber])
    }

    function endDrag() {
        if (!drag.active || !dragTargetEl) return

        const finalY = drag.yArray[drag.pointNumber]
        const changed = finalY !== drag.originalY

        Plotly.restyle(dragTargetEl, {
            'marker.size': [NORMAL_MARKER_SIZE],
            'marker.color': [null],
        }, [drag.curveNumber])

        if (changed && onDragEnd) {
            onDragEnd({
                curveNumber: drag.curveNumber,
                pointNumber: drag.pointNumber,
                oldY: drag.originalY,
                newY: finalY,
            })
        }

        drag.active = false
        drag.curveNumber = -1
        drag.pointNumber = -1
        drag.originalY = 0
        drag.yArray = []
    }

    function onPlotMouseDown(el: HTMLElement, e: MouseEvent) {
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

    function updateDragButtonStyle(el: HTMLElement) {
        const btn = el.querySelector('.modebar-btn[data-title="拖拽编辑"]') as HTMLElement | null
        if (!btn) return
        if (dragModeEnabled.value) {
            btn.style.background = 'rgba(68,68,68,0.15)'
            btn.style.borderRadius = '3px'
        } else {
            btn.style.background = ''
            btn.style.borderRadius = ''
        }
    }

    function toggleDragMode(el: HTMLElement) {
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

        updateDragButtonStyle(el)
    }

    const boundMouseDownHandlers = new WeakMap<HTMLElement, (e: MouseEvent) => void>()

    const boundRelayoutHandlers = new WeakMap<HTMLElement, (data: Record<string, unknown>) => void>()

    function onRelayout(el: HTMLElement, data: Record<string, unknown>) {
        if (!dragModeEnabled.value) return
        if ('dragmode' in data && data.dragmode !== false) {
            dragModeEnabled.value = false
            if (drag.active) endDrag()
            dragTargetEl = null
            updateDragButtonStyle(el)
        }
    }

    function setupDragListeners(el: HTMLElement) {
        const plotArea = el.querySelector('.nsewdrag') as HTMLElement | null
        const target = plotArea || el

        const handler = (e: MouseEvent) => onPlotMouseDown(el, e)
        boundMouseDownHandlers.set(el, handler)
        target.addEventListener('mousedown', handler)

        const relayoutHandler = (data: Record<string, unknown>) => onRelayout(el, data)
        boundRelayoutHandlers.set(el, relayoutHandler)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(el as any).on('plotly_relayout', relayoutHandler)
    }

    function teardownDragListeners(el: HTMLElement) {
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

    function reset() {
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
        reset,
    }
}
