import { app, shell, BrowserWindow, ipcMain, dialog, protocol, net } from 'electron'
import { join } from 'path'
import { stat } from 'fs/promises'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { pathToFileURL } from 'url'
import { ChildProcess, spawn } from 'child_process'

let backendProcess: ChildProcess | null = null
let previewWindow: BrowserWindow | null = null
let isQuitting = false

function killBackend(): void {
    if (!backendProcess) return
    console.log('[Backend] Stopping...')
    if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'])
    } else {
        backendProcess.kill('SIGTERM')
    }
    backendProcess = null
}

function createWindow(): void {
    // Create the browser window.
    const mainWindow = new BrowserWindow({
        title: '研发七部工具包',
        width: 1000,
        height: 600,
        show: false,
        autoHideMenuBar: true,
        ...(process.platform === 'linux' ? { icon } : {}),
        webPreferences: {
            preload: join(__dirname, '../preload/index.js'),
            sandbox: false
        }
    })

    mainWindow.on('ready-to-show', () => {
        mainWindow.show()
    })

    let forceClose = false
    mainWindow.on('close', (event) => {
        if (forceClose) return
        event.preventDefault()
        dialog
            .showMessageBox(mainWindow, {
                type: 'question',
                buttons: ['取消', '退出'],
                defaultId: 1,
                cancelId: 0,
                title: '确认退出',
                message: '确定要退出应用吗？'
            })
            .then(({ response }) => {
                if (response === 1) {
                    if (previewWindow && !previewWindow.isDestroyed()) {
                        previewWindow.destroy()
                        previewWindow = null
                    }
                    forceClose = true
                    isQuitting = true
                    mainWindow.close()
                }
            })
    })

    mainWindow.webContents.setWindowOpenHandler((details) => {
        shell.openExternal(details.url)
        return { action: 'deny' }
    })

    // HMR for renderer base on electron-vite cli.
    // Load the remote URL for development or the local html file for production.
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
        mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
    } else {
        mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
    }
}

protocol.registerSchemesAsPrivileged([
    { scheme: 'local-file', privileges: { bypassCSP: true, stream: true, supportFetchAPI: true } }
])

app.whenReady().then(async () => {
    protocol.handle('local-file', (request) => {
        const urlWithoutScheme = request.url.replace('local-file://', '')
        const filePath = decodeURIComponent(urlWithoutScheme.split('?')[0])
        return net.fetch(pathToFileURL(filePath).href)
    })

    electronApp.setAppUserModelId('com.rd7.edge-stress')

    app.on('browser-window-created', (_, window) => {
        optimizer.watchWindowShortcuts(window)
    })

    ipcMain.on('ping', () => console.log('pong'))

    ipcMain.handle(
        'dialog:openFile',
        async (_event, options: { filters?: { name: string; extensions: string[] }[]; title?: string }) => {
            const win = BrowserWindow.getFocusedWindow()
            if (!win) return { canceled: true, filePaths: [], fileSizes: [] }
            const result = await dialog.showOpenDialog(win, {
                title: options.title,
                filters: options.filters,
                properties: ['openFile', 'multiSelections']
            })
            if (result.canceled) return { ...result, fileSizes: [] }
            const fileSizes = await Promise.all(
                result.filePaths.map(async (fp) => {
                    try {
                        const s = await stat(fp)
                        return s.size
                    } catch {
                        return 0
                    }
                })
            )
            return { ...result, fileSizes }
        }
    )

    ipcMain.handle(
        'dialog:openDirectory',
        async (_event, options: { title?: string }) => {
            const win = BrowserWindow.getFocusedWindow()
            if (!win) return { canceled: true, filePaths: [] }
            return dialog.showOpenDialog(win, {
                title: options.title,
                properties: ['openDirectory']
            })
        }
    )

    ipcMain.handle(
        'window:openPreview',
        async (
            _event,
            options: { fileStem: string; outputDir: string; columns: string; title?: string }
        ) => {
            const queryStr = new URLSearchParams({
                fileStem: options.fileStem,
                outputDir: options.outputDir,
                columns: options.columns
            }).toString()

            if (previewWindow && !previewWindow.isDestroyed()) {
                if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
                    previewWindow.loadURL(
                        `${process.env['ELECTRON_RENDERER_URL']}/preview.html?${queryStr}`
                    )
                } else {
                    previewWindow.loadFile(join(__dirname, '../renderer/preview.html'), {
                        search: queryStr
                    })
                }
                previewWindow.focus()
                return
            }

            previewWindow = new BrowserWindow({
                title: options.title || '报告预览',
                autoHideMenuBar: true,
                webPreferences: {
                    preload: join(__dirname, '../preload/preview.js'),
                    sandbox: false
                }
            })
            previewWindow.maximize()

            previewWindow.on('close', (event) => {
                if (isQuitting) {
                    event.preventDefault()
                }
            })

            previewWindow.on('closed', () => {
                previewWindow = null
            })

            if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
                previewWindow.loadURL(
                    `${process.env['ELECTRON_RENDERER_URL']}/preview.html?${queryStr}`
                )
            } else {
                previewWindow.loadFile(join(__dirname, '../renderer/preview.html'), {
                    search: queryStr
                })
            }
        }
    )

    // startBackend()
    // const ready = await waitForBackend()
    // if (!ready) {
    //     console.error('[Backend] Timed out waiting for backend to start')
    // }

    createWindow()

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})

app.on('window-all-closed', () => {
    killBackend()
    app.quit()
})

app.on('before-quit', (event) => {
    if (!isQuitting) {
        event.preventDefault()
        isQuitting = true
        const mainWindow = BrowserWindow.getAllWindows().find(
            (w) => w !== previewWindow && !w.isDestroyed()
        )
        if (mainWindow) {
            mainWindow.close()
        }
        return
    }
    killBackend()
})
