import { API_BASE, waitBackend } from '@renderer/api/backend'

// TMB 服务器（tmb_web_v1）的账号，经本地后端 backend/app_account 转发

export interface AccountUser {
    // 工号
    username: string
    // 中文名，没填时是工号
    name: string
    department: string | null
}

// access 15 分钟过期，refresh 7 天；续期时两个都换新的
export interface TokenPair {
    access: string
    refresh: string
}

export interface LoginResult extends TokenPair {
    user: AccountUser
}

// 后端回 401：令牌过期或无效。先续期重试，续期也被拒就要重新登录
export class AuthExpiredError extends Error {}

// 调本地后端，出错时抛后端给的 detail；401 抛 AuthExpiredError，交给 stores/account.ts 的 withAccess 续期重试
export const requestJson = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
    await waitBackend()
    const res = await fetch(`${API_BASE}${path}`, init)
    if (res.ok) return res.json()
    const err = await res.json().catch(() => ({}))
    const detail = typeof err.detail === 'string' && err.detail ? err.detail : `HTTP ${res.status}`
    throw res.status === 401 ? new AuthExpiredError(detail) : new Error(detail)
}

const postJson = <T>(path: string, body: unknown): Promise<T> =>
    requestJson(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })

// TMB 服务器同一账号只留一处登录：登录成功后，网页版上的这个账号会被下线
export const login = (username: string, password: string): Promise<LoginResult> =>
    postJson('/api/account/login', { username, password })

export const refreshTokens = (refresh: string): Promise<TokenPair> =>
    postJson('/api/account/refresh', { refresh })

export const fetchMe = (access: string): Promise<AccountUser> =>
    requestJson('/api/account/me', { headers: { Authorization: `Bearer ${access}` } })
