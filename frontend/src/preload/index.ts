import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const customAPI = {
    openFileDialog: (options: { filters?: { name: string; extensions: string[] }[]; title?: string }) =>
        ipcRenderer.invoke('dialog:openFile', options),

    openDirAndScan: (options: { title?: string; extensions?: string[] }) =>
        ipcRenderer.invoke('dialog:openDirAndScan', options),

    openDirectoryDialog: (options: { title?: string }) =>
        ipcRenderer.invoke('dialog:openDirectory', options),

    openPreviewWindow: (options: { fileStem: string; outputDir: string; columns: string; title?: string }) =>
        ipcRenderer.invoke('window:openPreview', options),

    onConfirmQuit: (callback: () => void) => {
        ipcRenderer.on('app:confirm-quit', () => callback())
    },

    confirmQuit: () => ipcRenderer.send('app:quit-confirmed'),

    theme: {
        set: (mode: 'light' | 'dark' | 'system') => ipcRenderer.invoke('theme:set', mode),
        get: () => ipcRenderer.invoke('theme:get') as Promise<{ source: string; shouldUseDarkColors: boolean }>
    }
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
