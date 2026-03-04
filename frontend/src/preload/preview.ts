import { contextBridge } from 'electron'

const previewAPI = {
    getSearchParams: (): Record<string, string> => {
        const params: Record<string, string> = {}
        const url = new URL(window.location.href)
        url.searchParams.forEach((value, key) => {
            params[key] = value
        })
        return params
    }
}

if (process.contextIsolated) {
    try {
        contextBridge.exposeInMainWorld('previewAPI', previewAPI)
    } catch (error) {
        console.error(error)
    }
} else {
    // @ts-ignore
    window.previewAPI = previewAPI
}
