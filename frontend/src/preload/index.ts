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

    settings: {
        get: (key: string) => ipcRenderer.invoke('settings:get', key),
        set: (key: string, value: unknown) => ipcRenderer.invoke('settings:set', key, value),
        getAll: () => ipcRenderer.invoke('settings:getAll')
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
