import { ElectronAPI } from '@electron-toolkit/preload'

interface CustomElectronAPI {
    openFileDialog: (options: {
        filters?: { name: string; extensions: string[] }[]
        title?: string
    }) => Promise<{ canceled: boolean; filePaths: string[]; fileSizes: number[] }>

    openDirAndScan: (options: {
        title?: string
        extensions?: string[]
    }) => Promise<{ canceled: boolean; filePaths: string[]; fileSizes: number[] }>

    openDirectoryDialog: (options: {
        title?: string
    }) => Promise<{ canceled: boolean; filePaths: string[] }>

    openPreviewWindow: (options: {
        fileStem: string
        outputDir: string
        columns: string
        title?: string
    }) => Promise<void>

    onConfirmQuit: (callback: () => void) => void
    confirmQuit: () => void

    theme: {
        set: (mode: 'light' | 'dark' | 'system') => Promise<boolean>
        get: () => Promise<{ source: string; shouldUseDarkColors: boolean }>
    }
}

declare global {
    interface Window {
        electron: ElectronAPI
        electronAPI: CustomElectronAPI
    }
}
