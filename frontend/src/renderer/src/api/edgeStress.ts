const WS_BASE = 'ws://localhost:8000'

export interface PreviewItem {
    colIndex: number
    path: string
}

export interface ParseResult {
    fileNames: string[]
    columns: Record<string, number[]>
    generatedFiles: string[]
    previewMap: Record<string, PreviewItem[]>
}

export interface ProgressMessage {
    type: 'progress'
    current: number
    total: number
    filename: string
}

export interface DoneMessage extends ParseResult {
    type: 'done'
}

export interface ErrorMessage {
    type: 'error'
    message: string
}

export type WsMessage = ProgressMessage | DoneMessage | ErrorMessage

export function parseWithProgress(
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
): { cancel: () => void } {
    const ws = new WebSocket(`${WS_BASE}/ws/parse`)

    ws.onopen = () => {
        ws.send(
            JSON.stringify({ filePaths, fileType, peakThreshold, outputDir, reportConfig })
        )
    }

    ws.onmessage = (event) => {
        try {
            const msg: WsMessage = JSON.parse(event.data)
            onMessage(msg)
        } catch {
            onMessage({ type: 'error', message: '解析服务返回了无效数据' })
        }
    }

    ws.onerror = () => {
        onMessage({ type: 'error', message: '与解析服务的连接异常' })
    }

    ws.onclose = (event) => {
        if (event.code !== 1000 && event.code !== 1005) {
            onMessage({ type: 'error', message: `连接关闭 (code: ${event.code})` })
        }
    }

    return {
        cancel: () => {
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close()
            }
        }
    }
}
