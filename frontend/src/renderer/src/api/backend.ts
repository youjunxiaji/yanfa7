// 开发时后端由 `uv run main.py` 起在 8006，打包后的后端固定 8000，与 backend/main.py 保持一致
const BACKEND_PORT = import.meta.env.DEV ? 8006 : 8000

export const API_BASE = `http://localhost:${BACKEND_PORT}`
export const WS_BASE = `ws://localhost:${BACKEND_PORT}`

// 打包后的后端随应用一起启动（src-tauri/src/backend.rs）：装好或更新后第一次启动要解包，系统还要扫描
// 新解出的文件，要几十秒；之后每次一两秒。请求前先等它能应答，免得刚打开应用就操作时直接报连接失败。
const READY_TIMEOUT_MS = 120_000
const READY_POLL_MS = 500

let ready: Promise<void> | null = null

const pollReady = async (): Promise<void> => {
    const deadline = Date.now() + READY_TIMEOUT_MS
    while (Date.now() < deadline) {
        try {
            if ((await fetch(`${API_BASE}/docs`)).ok) return
        } catch {
            // 还没开始监听，接着等
        }
        await new Promise((resolve) => setTimeout(resolve, READY_POLL_MS))
    }
    throw new Error('后端服务没有启动，请重启应用')
}

/** 等后端能应答。就绪过一次就直接返回；超时的话，下次调用重新等。 */
export const waitBackend = (): Promise<void> => {
    ready ??= pollReady().catch((err: unknown) => {
        ready = null
        throw err
    })
    return ready
}
