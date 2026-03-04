import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const customAPI = {
    openFileDialog: (options: { filters?: { name: string; extensions: string[] }[]; title?: string }) =>
        ipcRenderer.invoke('dialog:openFile', options),

    openDirectoryDialog: (options: { title?: string }) =>
        ipcRenderer.invoke('dialog:openDirectory', options),

    openPreviewWindow: (options: { fileStem: string; outputDir: string; columns: string; title?: string }) =>
        ipcRenderer.invoke('window:openPreview', options)
}

if (process.contextIsolated) {
    try {
        contextBridge.exposeInMainWorld('electron', electronAPI)
        contextBridge.exposeInMainWorld('electronAPI', customAPI)
    } catch (error) {
        console.error(error)
    }
} else {
    // @ts-ignore (define in dts)
    window.electron = electronAPI
    // @ts-ignore (define in dts)
    window.electronAPI = customAPI
}
