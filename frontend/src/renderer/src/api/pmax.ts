const API_BASE = 'http://localhost:8000'

export interface BinItem {
    label: string
    percentage: number
}

export interface BearingResult {
    chartPath: string
    bins: BinItem[]
}

export interface AnalyzeResponse {
    front: BearingResult
    rear: BearingResult
}

export interface AnalyzeParams {
    data: string[][]
    binConfig: {
        front: { min: number; max: number; step: number }
        rear: { min: number; max: number; step: number }
    }
    chartConfig: {
        titleFontSize: number
        labelFontSize: number
        tickFontSize: number
        textFontSize: number
        width: number
        height: number
    }
    language: string
}

export async function analyzePmax(params: AnalyzeParams): Promise<AnalyzeResponse> {
    const res = await fetch(`${API_BASE}/api/pmax/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    })
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
}
