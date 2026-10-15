/**
 * Tauri compatibility shim.
 *
 * Re-implements the exact `window.electron` / `window.electronAPI` /
 * `window.previewAPI` surfaces that the Vue renderer expects, but backed by
 * Tauri v2 APIs instead of Electron IPC. `initTauriBridge()` must be awaited
 * before the Vue app is mounted (see main.ts / preview.ts) so the globals and
 * persisted theme are in place before any component setup runs.
 */
import { convertFileSrc, invoke } from '@tauri-apps/api/core'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { WebviewWindow } from '@tauri-apps/api/webviewWindow'
import { open as openDialog } from '@tauri-apps/plugin-dialog'
import { revealItemInDir } from '@tauri-apps/plugin-opener'
import { platform } from '@tauri-apps/plugin-os'
import { load, type Store } from '@tauri-apps/plugin-store'
import { startDrag as tauriStartDrag } from '@crabnebula/tauri-plugin-drag'
import { logError } from '@renderer/api/logs'

type AppearanceMode = 'light' | 'dark' | 'system'

// ---- platform (synchronous reads after init) ------------------------------
const PLATFORM_MAP: Record<string, string> = {
    macos: 'darwin',
    windows: 'win32',
    linux: 'linux'
}
let resolvedPlatform = 'darwin'

// ---- settings store (replaces electron-store) -----------------------------
let settingsStore: Store | null = null
async function getStore(): Promise<Store> {
    if (!settingsStore) {
        settingsStore = await load('settings.json', { defaults: {}, autoSave: true })
    }
    return settingsStore
}

// ---- account store --------------------------------------------------------
// TMB 服务器的登录状态（令牌和用户信息）和设置分开放，内容由渲染层的 stores/account.ts 定
let accountStore: Store | null = null
const getAccountStore = async (): Promise<Store> => {
    accountStore ??= await load('account.json', { defaults: {}, autoSave: true })
    return accountStore
}

function shouldUseDark(mode: string): boolean {
    if (mode === 'dark') return true
    if (mode === 'light') return false
    return window.matchMedia('(prefers-color-scheme: dark)').matches
}

async function applyTheme(mode: AppearanceMode): Promise<void> {
    // Driving the native window theme makes the webview's prefers-color-scheme
    // follow the setting, which the renderer's syncDarkClass() already reacts to.
    try {
        await getCurrentWindow().setTheme(mode === 'system' ? null : mode)
    } catch {
        /* setTheme may be unavailable on some platforms — fall through */
    }
    document.documentElement.classList.toggle('dark', shouldUseDark(mode))
}

// ---- drag-out icon --------------------------------------------------------
// The drag plugin shows the icon at its natural size, so a full chart PNG would
// cover half the screen; scale it down like Electron's nativeImage.resize() did.
// The asset protocol answers with an Access-Control-Allow-Origin header, so a
// crossOrigin load keeps the canvas untainted. Falls back to the PNG itself.
const DRAG_ICON_WIDTH = 200

const makeDragIcon = async (filePath: string): Promise<string> => {
    try {
        const img = new Image()
        img.crossOrigin = 'anonymous'
        img.src = `${convertFileSrc(filePath)}?t=${Date.now()}`
        await img.decode()
        const canvas = document.createElement('canvas')
        canvas.width = DRAG_ICON_WIDTH
        canvas.height = Math.round((img.naturalHeight / img.naturalWidth) * DRAG_ICON_WIDTH)
        const ctx = canvas.getContext('2d')
        if (!ctx || !canvas.height) return filePath
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        return canvas.toDataURL('image/png')
    } catch {
        return filePath
    }
}

// ---- window.electron ------------------------------------------------------
const electronShim = {
    process: {
        get platform(): string {
            return resolvedPlatform
        },
        versions: {} as Record<string, string>
    }
}

// ---- window.electronAPI ---------------------------------------------------
const PREVIEW_LABEL = 'preview'

const electronAPIShim = {
    openFileDialog: async (options: {
        filters?: { name: string; extensions: string[] }[]
        title?: string
    }) => {
        const selected = await openDialog({
            multiple: true,
            title: options?.title,
            filters: options?.filters
        })
        if (selected == null) return { canceled: true, filePaths: [], fileSizes: [] }
        const filePaths = Array.isArray(selected) ? selected : [selected]
        return { canceled: false, filePaths, fileSizes: filePaths.map(() => 0) }
    },

    openDir: async (options: { title?: string }) => {
        const selected = await openDialog({
            directory: true,
            multiple: false,
            title: options?.title
        })
        if (selected == null) return { canceled: true, rootDir: '' }
        return { canceled: false, rootDir: selected as string }
    },

    scanDir: async (options: { rootDir: string; extensions?: string[] }) => {
        return await invoke<{ filePaths: string[]; fileSizes: number[] }>('scan_dir', {
            rootDir: options.rootDir,
            extensions: options.extensions
        })
    },

    openDirectoryDialog: async (options: { title?: string }) => {
        const selected = await openDialog({
            directory: true,
            multiple: false,
            title: options?.title
        })
        if (selected == null) return { canceled: true, filePaths: [] }
        return { canceled: false, filePaths: [selected as string] }
    },

    openPreviewWindow: async (options: {
        fileStem: string
        outputDir: string
        columns: string
        title?: string
    }) => {
        const query = new URLSearchParams({
            fileStem: options.fileStem,
            outputDir: options.outputDir,
            columns: options.columns
        }).toString()

        // Reuse the single preview window: tear down any existing one first so
        // the new query params take effect (Tauri has no JS-side navigate()).
        const existing = await WebviewWindow.getByLabel(PREVIEW_LABEL)
        if (existing) {
            await existing.destroy()
            for (let i = 0; i < 50; i++) {
                if (!(await WebviewWindow.getByLabel(PREVIEW_LABEL))) break
                await new Promise((r) => setTimeout(r, 20))
            }
        }

        const win = new WebviewWindow(PREVIEW_LABEL, {
            url: `preview.html?${query}`,
            title: options.title || '报告预览',
            width: 1400,
            height: 900
        })
        win.once('tauri://created', async () => {
            await win.maximize()
            await win.setFocus()
        })
        win.once('tauri://error', (e) => logError('[preview] 预览窗口没能打开', e))
    },

    onConfirmQuit: (callback: () => void) => {
        // Intercept the window close (X / Cmd-Q routed to window) and defer to
        // the renderer's confirm dialog instead of closing immediately.
        getCurrentWindow().onCloseRequested((event) => {
            event.preventDefault()
            callback()
        })
    },

    confirmQuit: async () => {
        const preview = await WebviewWindow.getByLabel(PREVIEW_LABEL)
        if (preview) await preview.destroy()
        await getCurrentWindow().destroy()
    },

    theme: {
        set: async (mode: AppearanceMode): Promise<boolean> => {
            const store = await getStore()
            await store.set('appearance', mode)
            await store.save()
            await applyTheme(mode)
            return shouldUseDark(mode)
        },
        get: async (): Promise<{ source: string; shouldUseDarkColors: boolean }> => {
            const store = await getStore()
            const source = ((await store.get<string>('appearance')) ?? 'light') as AppearanceMode
            return { source, shouldUseDarkColors: shouldUseDark(source) }
        }
    },

    account: {
        load: async (): Promise<unknown> => {
            const store = await getAccountStore()
            return (await store.get('account')) ?? null
        },
        save: async (account: unknown): Promise<void> => {
            const store = await getAccountStore()
            await store.set('account', account)
            await store.save()
        }
    },

    // 在资源管理器里打开日志目录，选中这次运行的日志（外壳按启动时间命名，见 src-tauri/src/backend.rs）；
    // 开发版不拉起后端，没有日志文件
    openLogDir: async (): Promise<void> => {
        const path = await invoke<string | null>('backend_log_path')
        if (!path) throw new Error('这次运行没有日志文件')
        await revealItemInDir(path)
    },

    startDrag: (filePath: string): void => {
        // Native drag-out (e.g. into Word): the webview's own <img> drag only carries
        // an asset:// URL that other apps cannot open.
        makeDragIcon(filePath)
            .then((icon) => tauriStartDrag({ item: [filePath], icon }))
            .catch((e) => logError('[startDrag] 图片没能拖出去', e))
    }
}

// ---- window.previewAPI ----------------------------------------------------
const previewAPIShim = {
    getSearchParams: (): Record<string, string> => {
        const params: Record<string, string> = {}
        new URL(window.location.href).searchParams.forEach((value, key) => {
            params[key] = value
        })
        return params
    }
}

/**
 * Re-export so components can build asset URLs directly where they previously
 * hand-rolled `local-file://` strings.
 */
export { convertFileSrc }

/**
 * Install the shims and apply persisted settings. Await before app.mount().
 */
export async function initTauriBridge(): Promise<void> {
    try {
        const p = platform()
        resolvedPlatform = PLATFORM_MAP[p] ?? p
    } catch {
        /* keep default */
    }

    try {
        const { getVersion, getTauriVersion } = await import('@tauri-apps/api/app')
        electronShim.process.versions = {
            app: await getVersion(),
            tauri: await getTauriVersion()
        }
    } catch {
        /* versions are cosmetic */
    }

    // Apply the persisted appearance at startup (Electron did this in main).
    try {
        const store = await getStore()
        const source = ((await store.get<string>('appearance')) ?? 'light') as AppearanceMode
        await applyTheme(source)
    } catch (e) {
        logError('[tauri-bridge] 外观设置没能应用', e)
    }

    const w = window as unknown as Record<string, unknown>
    w.electron = electronShim
    w.electronAPI = electronAPIShim
    w.previewAPI = previewAPIShim
}
