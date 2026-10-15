import { defineStore } from 'pinia'
import {
    AuthExpiredError,
    fetchMe,
    login,
    refreshTokens,
    type AccountUser
} from '@renderer/api/account'
import { logError, logWarning } from '@renderer/api/logs'

// 存在本机的登录状态（Tauri store 的 account.json，经兼容垫片读写）
interface Session {
    user: AccountUser
    access: string
    refresh: string
}

interface SavedAccount {
    // 上次登录的工号，退出登录后也留着，登录框里预填
    username: string
    session: Session | null
}

// access token 离过期不到 30 秒就先续期，免得请求还没到服务器就过期了
const EXPIRE_MARGIN_MS = 30_000

// JWT 的过期时间（毫秒），解不出来当作已过期。只读 payload 不验签，验签是 TMB 服务器的事
const expiresAt = (token: string): number => {
    try {
        const payload = token.split('.')[1] ?? ''
        const { exp } = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
        return typeof exp === 'number' ? exp * 1000 : 0
    } catch {
        return 0
    }
}

const isUser = (value: unknown): value is AccountUser => {
    const user = value as AccountUser | null
    return typeof user?.username === 'string' && typeof user.name === 'string'
}

// account.json 是磁盘上的文件，可能是旧版本写的或被改坏了，对不上的部分当作没有
const parseSaved = (raw: unknown): SavedAccount => {
    const saved = (raw ?? {}) as Partial<SavedAccount>
    const session = saved.session
    const valid =
        isUser(session?.user) &&
        typeof session.access === 'string' &&
        typeof session.refresh === 'string'
    return {
        username: typeof saved.username === 'string' ? saved.username : '',
        session: valid ? session : null
    }
}

// 几个请求同时发现令牌过期时，共用同一次续期
let refreshing: Promise<string> | null = null

export const useAccountStore = defineStore('account', {
    state: () => ({
        user: null as AccountUser | null,
        access: '',
        refresh: '',
        lastUsername: '',
        // 本机存的登录状态读出来之前，侧栏先不显示账号
        ready: false,
        loginVisible: false
    }),

    actions: {
        // 启动时读出上次的登录状态，再找 TMB 服务器确认一下：顺带续期，常用的话不用每 7 天重新登录
        async restore() {
            try {
                const saved = parseSaved(await window.electronAPI.account.load())
                this.lastUsername = saved.username
                if (saved.session && expiresAt(saved.session.refresh) > Date.now()) {
                    this.setSession(saved.session)
                }
            } catch (err) {
                logError('[account] 读取登录状态失败', err)
            } finally {
                this.ready = true
            }
            if (!this.user) return
            try {
                this.user = await this.withAccess(fetchMe)
                await this.persist()
            } catch (err) {
                // 连不上服务器时先留着登录状态，登录过期的话 withAccess 里已经退出了
                logWarning('[account] 确认登录状态失败', err)
            }
        },

        async login(username: string, password: string) {
            const result = await login(username, password)
            this.setSession(result)
            this.lastUsername = result.user.username
            await this.persist()
        },

        // 只丢掉本机的令牌：tmb_web_v1 没开令牌黑名单，服务器那边没什么要撤销的
        async logout() {
            this.user = null
            this.access = ''
            this.refresh = ''
            await this.persist()
        },

        setSession(session: Session) {
            this.user = { ...session.user }
            this.access = session.access
            this.refresh = session.refresh
        },

        async persist() {
            const session = this.user
                ? { user: { ...this.user }, access: this.access, refresh: this.refresh }
                : null
            try {
                await window.electronAPI.account.save({ username: this.lastUsername, session })
            } catch (err) {
                logError('[account] 保存登录状态失败', err)
            }
        },

        // 拿一个没过期的 access token，快过期了先续期；refresh token 也被拒就退出登录
        async getAccess(force = false): Promise<string> {
            if (!this.user) throw new AuthExpiredError('请先登录')
            if (!force && expiresAt(this.access) - EXPIRE_MARGIN_MS > Date.now()) return this.access
            refreshing ??= refreshTokens(this.refresh)
                .then(async (tokens) => {
                    this.access = tokens.access
                    this.refresh = tokens.refresh
                    await this.persist()
                    return tokens.access
                })
                .catch(async (err: unknown) => {
                    if (err instanceof AuthExpiredError) await this.logout()
                    throw err
                })
                .finally(() => {
                    refreshing = null
                })
            return refreshing
        },

        // 带着 access token 调要登录的接口。没到期却被拒（比如服务器换了密钥）就强制续期再试一次，
        // 还被拒就退出登录
        async withAccess<T>(call: (access: string) => Promise<T>): Promise<T> {
            const access = await this.getAccess()
            try {
                return await call(access)
            } catch (err) {
                if (!(err instanceof AuthExpiredError)) throw err
            }
            try {
                return await call(await this.getAccess(true))
            } catch (err) {
                if (err instanceof AuthExpiredError) await this.logout()
                throw err
            }
        }
    }
})
