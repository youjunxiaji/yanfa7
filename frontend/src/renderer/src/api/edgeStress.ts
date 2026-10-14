import { WS_BASE, waitBackend } from '@renderer/api/backend'

export interface PreviewItem {
    colIndex: number
    path: string
}

// 开始处理第 current 个文件
export interface ProgressMessage {
    type: 'progress'
    current: number
    total: number
    filename: string
}

// 单个文件处理完就推一条，index 是文件在请求 filePaths 里的下标
export interface FileDoneMessage {
    type: 'fileDone'
    index: number
    columns: number[]
    previewItems: PreviewItem[]
}

export interface FileSkippedMessage {
    type: 'fileSkipped'
    index: number
    reason: string
}

export interface DoneMessage {
    type: 'done'
    generatedFiles: string[]
}

export interface ErrorMessage {
    type: 'error'
    message: string
}

export type WsMessage =
    | ProgressMessage
    | FileDoneMessage
    | FileSkippedMessage
    | DoneMessage
    | ErrorMessage

export const parseWithProgress = (
    filePaths: string[],
    fileType: 'htm' | 'xlsx',
    peakThreshold: number,
    outputDir: string,
    reportConfig: {
        picWidth: number
        picHeight: number
        loadPolarMin: number
        pressPolarMin: number
    },
    onMessage: (msg: WsMessage) => void
): { cancel: () => void } => {
    let ws: WebSocket | null = null
    let canceled = false

    const connect = (): void => {
        const socket = new WebSocket(`${WS_BASE}/ws/parse`)
        ws = socket

        socket.onopen = () => {
            socket.send(
                JSON.stringify({ filePaths, fileType, peakThreshold, outputDir, reportConfig })
            )
        }

        socket.onmessage = (event) => {
            try {
                const msg: WsMessage = JSON.parse(event.data)
                onMessage(msg)
            } catch {
                onMessage({ type: 'error', message: '解析服务返回了无效数据' })
            }
        }

        socket.onerror = () => {
            onMessage({ type: 'error', message: '与解析服务的连接异常' })
        }

        socket.onclose = (event) => {
            if (event.code !== 1000 && event.code !== 1005) {
                onMessage({ type: 'error', message: `连接关闭 (code: ${event.code})` })
            }
        }
    }

    waitBackend()
        .then(() => {
            if (!canceled) connect()
        })
        .catch((err: Error) => {
            if (!canceled) onMessage({ type: 'error', message: err.message })
        })

    return {
        cancel: () => {
            canceled = true
            if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
                ws.close()
            }
        }
    }
}
