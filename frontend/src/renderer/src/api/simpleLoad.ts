import { API_BASE, WS_BASE, waitBackend } from '@renderer/api/backend'
import type { Axis, LoadColumn, SourceAxis } from '@renderer/constants/simpleLoad'

// Romax 的轴取载荷文件里的哪个轴
export interface AxisMapping {
    romax: Axis
    origin: SourceAxis
}

// 载荷文件夹里 txt 的个数和总大小，以及第一个 txt 开头几行的原文（空行不算）
export interface PreviewResult {
    fileCount: number
    totalSize: number
    sampleFile: string
    lines: string[]
}

export interface LoadParams {
    loadDir: string
    freqTablePath: string
    // txt 每一列是什么，null 是不用的列
    columns: (LoadColumn | null)[]
    // 数据行前面跳过几行（列名、END_OF_HEADER 这类）
    skipRows: number
    unitForce: number
    unitMoment: number
    unitSpeed: number
}

export interface ReduceParams {
    // 参与分组的分量 → 从小到大的区间边界
    intervals: Partial<Record<LoadColumn, number[]>>
    // 依次是 Romax 的 x、y、z
    axisMapping: AxisMapping[]
    keepTorque: boolean
    slope: number
    temperature: number
    tol: number
    outputDir: string
}

// 一个分量的最值和加权时间占比分布，分布只含占比不小于 1e-4 的柱，share 是 0~1
export interface ComponentStats {
    component: LoadColumn
    min: number
    max: number
    binLeft: number[]
    binRight: number[]
    share: number[]
}

// 计算进度：当前阶段和总进度 0~100
export interface ProgressMessage {
    type: 'progress'
    stage: string
    percent: number
}

export interface LoadDoneMessage {
    type: 'done'
    fileCount: number
    rowCount: number
    components: ComponentStats[]
}

export interface ReduceDoneMessage {
    type: 'done'
    // 有载荷的格子数
    cellCount: number
    files: string[]
}

export interface ErrorMessage {
    type: 'error'
    message: string
}

export type LoadMessage = ProgressMessage | LoadDoneMessage | ErrorMessage
export type ReduceMessage = ProgressMessage | ReduceDoneMessage | ErrorMessage

const postJson = async <T>(path: string, body: unknown): Promise<T> => {
    await waitBackend()
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(typeof err.detail === 'string' ? err.detail : `HTTP ${res.status}`)
    }
    return res.status === 204 ? (undefined as T) : res.json()
}

export const previewLoadDir = (loadDir: string): Promise<PreviewResult> =>
    postJson('/api/simple-load/preview', { loadDir })

// 丢掉后端加载过的数据，把内存还回去
export const clearLoadedData = (): Promise<void> => postJson('/api/simple-load/clear', {})

// 加载和缩减各走一条 WebSocket：连上后发一条参数，后端推 progress，最后推 done 或 error 再关掉连接。
// 收到 done 或 error 之前连接就断了，按出错处理。
const runSocket = <M extends { type: string }>(
    path: string,
    payload: unknown,
    onMessage: (msg: M | ErrorMessage) => void
): void => {
    let finished = false
    const emit = (msg: M | ErrorMessage): void => {
        if (finished) return
        finished = msg.type === 'done' || msg.type === 'error'
        onMessage(msg)
    }

    waitBackend()
        .then(() => {
            const socket = new WebSocket(`${WS_BASE}${path}`)
            socket.onopen = () => socket.send(JSON.stringify(payload))
            socket.onmessage = (event) => {
                try {
                    emit(JSON.parse(event.data))
                } catch {
                    emit({ type: 'error', message: '后端返回了无效数据' })
                    socket.close()
                }
            }
            socket.onclose = () => emit({ type: 'error', message: '与后端的连接断开了' })
        })
        .catch((err: Error) => emit({ type: 'error', message: err.message }))
}

export const loadData = (params: LoadParams, onMessage: (msg: LoadMessage) => void): void =>
    runSocket<LoadMessage>('/ws/simple-load/load', params, onMessage)

export const reduceLoad = (params: ReduceParams, onMessage: (msg: ReduceMessage) => void): void =>
    runSocket<ReduceMessage>('/ws/simple-load/reduce', params, onMessage)
