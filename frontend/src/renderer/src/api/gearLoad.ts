import { requestJson } from '@renderer/api/account'
import type { GearStage } from '@renderer/constants/gearLoad'

// 齿轮载荷，后端 backend/app_gearLoad。输入表、多工况、计算结果都沿用网页版的写法，历史记录经后端转发 TMB 服务器

// 输入表的一行：英文参数名和 4 级的值（输入框里的字符串，空串是没填）
export type InputRow = { parameter: string; editable: boolean } & Record<GearStage, string>

// 多工况的一行：扭矩 T (kNm)、转速 n (rpm)
export interface ConditionRow {
    torque: string
    rpm: string
}

// 结果里的一格：数值（四舍五入到 3 位小数），算不出来是空串，除以 0 是 "Infinity" / "-Infinity"
export type StageValue = number | string

// 一级的计算结果，各列表的顺序同结果表（constants/gearLoad.ts）
export interface StageResult {
    // 功率、输出扭矩、输出转速，填到下一级的输入
    input_data: StageValue[]
    gear_loads: StageValue[]
    speed_of_components: StageValue[]
    equivalent_diameter: StageValue[]
}

// 有几列 16 行都填了，就只有 Stage I 起的前几级
export type CalculateResult = Partial<Record<GearStage, StageResult>>

export interface ExportParams {
    inputData: InputRow[]
    selectedData: ConditionRow[]
    // 选好的 xlsx 保存位置
    path: string
}

// 基础设置：历史记录按登录的人 + 这三项存
export interface HistoryForm {
    gearUnit: string
    windTurbine: string
    loadSpectrum: string
}

// 历史记录列表的一条：label 是「齿轮单元/风机/载荷谱」
export interface HistoryItem {
    id: number
    label: string
}

// 一条历史记录，网页版的记录里输入表、多工况可能是空的
export interface HistoryDetail {
    formData: HistoryForm
    inputData: InputRow[] | null
    selectedData: ConditionRow[] | null
}

export interface HistorySaveParams {
    formData: HistoryForm
    inputData: InputRow[]
    selectedData: ConditionRow[]
}

const postJson = <T>(
    path: string,
    body: unknown,
    headers: Record<string, string> = {}
): Promise<T> =>
    requestJson(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: JSON.stringify(body)
    })

const bearer = (access: string): Record<string, string> => ({ Authorization: `Bearer ${access}` })

export const calculateGearLoads = (inputData: InputRow[]): Promise<CalculateResult> =>
    postJson('/api/gear-load/calculate', { inputData })

// 多工况逐个算，每级一张表写进 xlsx
export const exportGearLoads = (params: ExportParams): Promise<{ path: string }> =>
    postJson('/api/gear-load/export', params)

// 要登录：只查得到自己存的，三项基础设置任一项模糊匹配，新存的在前
export const fetchHistories = (access: string, query: string): Promise<HistoryItem[]> =>
    requestJson(`/api/gear-load/histories?${new URLSearchParams({ query })}`, {
        headers: bearer(access)
    })

export const fetchHistory = (access: string, id: number): Promise<HistoryDetail> =>
    requestJson(`/api/gear-load/histories/${id}`, { headers: bearer(access) })

// 要登录：按三项基础设置存，自己存过同样三项的就整条覆盖；created 是 false 说明覆盖了
export const saveHistory = (
    access: string,
    params: HistorySaveParams
): Promise<{ created: boolean }> => postJson('/api/gear-load/histories', params, bearer(access))
