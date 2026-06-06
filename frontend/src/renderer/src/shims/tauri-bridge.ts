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
import { platform } from '@tauri-apps/plugin-os'
import { load, type Store } from '@tauri-apps/plugin-store'
import { startDrag as tauriStartDrag } from '@crabnebula/tauri-plugin-drag'

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
    if (!settingsStore) settingsStore = await load('settings.json', { autoSave: true })
    return settingsStore
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
        const selected = await openDialog({ directory: true, multiple: false, title: options?.title })
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
        const selected = await openDialog({ directory: true, multiple: false, title: options?.title })
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
        win.once('tauri://error', (e) => console.error('[preview] create error', e))
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

    startDrag: (filePath: string): void => {
        // Native drag-out (e.g. into Word). The chart PNG doubles as drag icon.
        tauriStartDrag({ item: [filePath], icon: filePath }).catch((e) =>
            console.error('[startDrag]', e)
        )
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
        console.error('[tauri-bridge] theme init failed', e)
    }

    const w = window as unknown as Record<string, unknown>
    w.electron = electronShim
    w.electronAPI = electronAPIShim
    w.previewAPI = previewAPIShim
}
