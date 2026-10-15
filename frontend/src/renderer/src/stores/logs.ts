import { defineStore } from 'pinia'
import { fetchLogs, type LogEntry } from '@renderer/api/logs'

// 「日志」页开着时每秒取一次新的
const POLL_MS = 1000
// 前端也只留最近这么多条，和后端 app_log 的 LogBuffer.MAX_RECORDS 一致
const MAX_ENTRIES = 2000

// 离开页面再回来时会重新开始轮询：旧的那一轮靠 generation 对不上自己停下
let timer: ReturnType<typeof setTimeout> | undefined
let generation = 0

// 这次运行的日志放在 store 里：切到别的页面再回来，已经取到的还在，「清屏」也还算数
export const useLogStore = defineStore('logs', {
    state: () => ({
        session: '',
        entries: [] as LogEntry[],
        // 「清屏」时最后一条的 seq，之前的不再显示；后端重启过就作废
        clearedSeq: 0,
        // 取到过一次就是 true，之前页面显示「正在连接后端…」
        connected: false,
        // 最近一次没取到的原因
        error: '',
        polling: false
    }),

    getters: {
        lastSeq: (state): number => state.entries.at(-1)?.seq ?? 0,

        shown: (state): LogEntry[] => state.entries.filter((entry) => entry.seq > state.clearedSeq)
    },

    actions: {
        async poll() {
            try {
                const result = await fetchLogs(this.session, this.lastSeq)
                if (result.session !== this.session) {
                    // 后端重启过（开发时热重载、打包后重开应用），这次运行的从头来
                    this.session = result.session
                    this.entries = result.records
                    this.clearedSeq = 0
                } else {
                    // 上一轮还没回来时又开了一轮，两边可能拿到同样的几条
                    const last = this.lastSeq
                    this.entries.push(...result.records.filter((entry) => entry.seq > last))
                }
                if (this.entries.length > MAX_ENTRIES) {
                    this.entries.splice(0, this.entries.length - MAX_ENTRIES)
                }
                this.connected = true
                this.error = ''
            } catch (err) {
                this.error = `连不上后端，日志取不到：${(err as Error).message}`
            }
        },

        // 「日志」页打开时开始轮询，离开时停
        start() {
            if (this.polling) return
            this.polling = true
            const current = ++generation
            const tick = async (): Promise<void> => {
                await this.poll()
                if (this.polling && current === generation) timer = setTimeout(tick, POLL_MS)
            }
            tick()
        },

        stop() {
            this.polling = false
            generation++
            clearTimeout(timer)
        },

        // 只清页面上已有的，后端和日志文件里的还在
        clear() {
            this.clearedSeq = this.lastSeq
        }
    }
})
