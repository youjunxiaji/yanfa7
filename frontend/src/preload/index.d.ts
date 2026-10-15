import { ElectronAPI } from '@electron-toolkit/preload'

interface CustomElectronAPI {
    openFileDialog: (options: {
        filters?: { name: string; extensions: string[] }[]
        title?: string
    }) => Promise<{ canceled: boolean; filePaths: string[]; fileSizes: number[] }>

    openDir: (options: { title?: string }) => Promise<{ canceled: boolean; rootDir: string }>

    scanDir: (options: {
        rootDir: string
        extensions?: string[]
    }) => Promise<{ filePaths: string[]; fileSizes: number[] }>

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

    // TMB 服务器的登录状态，存在 account.json；内容由 stores/account.ts 定，读出来先校验
    account: {
        load: () => Promise<unknown>
        save: (account: unknown) => Promise<void>
    }

    // 在资源管理器里打开日志目录，选中这次运行的日志；开发版没有日志文件
    openLogDir: () => Promise<void>

    startDrag: (filePath: string) => void
}

declare global {
    interface Window {
        electron: ElectronAPI
        electronAPI: CustomElectronAPI
    }
}
