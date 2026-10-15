import type { App } from 'vue'
import { API_BASE, waitBackend } from '@renderer/api/backend'
import { LogLevel, type LogSource } from '@renderer/constants/log'

// 「日志」页的一行，后端 backend/app_log/serializers.py 的 LogEntry
export interface LogEntry {
    // 后端这次运行里的序号，从 1 起递增
    seq: number
    // 本机时间，ISO 8601，到毫秒
    time: string
    level: LogLevel
    source: LogSource
    // 第一行
    message: string
    // 其余几行和报错堆栈，没有时是空串
    detail: string
}

export interface LogsResult {
    // 后端这次运行的标识，变了说明后端重启过
    session: string
    records: LogEntry[]
}

// 只取 seq 大于 after 的；session 对不上（后端重启过）时后端从头给
export const fetchLogs = async (session: string, after: number): Promise<LogsResult> => {
    await waitBackend()
    const query = new URLSearchParams({ session, after: String(after) })
    const res = await fetch(`${API_BASE}/api/logs?${query}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
}

// ========== 界面上的报错报给后端，和后端的日志记在一起 ==========
interface LogReport {
    level: LogLevel
    message: string
    detail: string
}

// 后端还没起来或连不上时先攒着，下一次报的时候一起补上；攒太多就丢最早的
const MAX_PENDING = 100
const pending: LogReport[] = []
let flushing = false

const flush = async (): Promise<void> => {
    if (flushing) return
    flushing = true
    try {
        await waitBackend()
        while (pending.length) {
            await fetch(`${API_BASE}/api/logs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pending[0])
            })
            // 后端收到了，不管收没收下都不再重发：重发也是一样的结果
            pending.shift()
        }
    } catch {
        // 连不上后端：留着，下一次报的时候再补
    } finally {
        flushing = false
    }
}

// Error 取说明和堆栈，别的转成文字
const describe = (err: unknown): { text: string; stack: string } => {
    if (err instanceof Error) return { text: err.message || err.name, stack: err.stack ?? '' }
    if (typeof err === 'string') return { text: err, stack: '' }
    try {
        return { text: JSON.stringify(err) ?? String(err), stack: '' }
    } catch {
        return { text: String(err), stack: '' }
    }
}

const report = (level: LogLevel, message: string, err: unknown): void => {
    const { text, stack } = err === undefined ? { text: '', stack: '' } : describe(err)
    pending.push({ level, message: text ? `${message}：${text}` : message, detail: stack })
    if (pending.length > MAX_PENDING) pending.shift()
    flush()
}

// 界面上的报错：照常打到控制台，同时记进「日志」页
export const logError = (message: string, err?: unknown): void => {
    if (err === undefined) console.error(message)
    else console.error(message, err)
    report(LogLevel.ERROR, message, err)
}

export const logWarning = (message: string, err?: unknown): void => {
    if (err === undefined) console.warn(message)
    else console.warn(message, err)
    report(LogLevel.WARNING, message, err)
}

// 没接住的报错都记进「日志」页：组件里的（Vue）、脚本里的、没人处理的 Promise
export const installErrorReporting = (app: App): void => {
    app.config.errorHandler = (err) => logError('界面出错', err)
    window.addEventListener('error', (event) => logError('界面出错', event.error ?? event.message))
    window.addEventListener('unhandledrejection', (event) =>
        logError('异步操作出错，没有处理', event.reason)
    )
}
