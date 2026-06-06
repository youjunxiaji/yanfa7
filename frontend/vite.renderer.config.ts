import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import pkg from './package.json'

// Standalone Vite config for the Vue renderer, driven by Tauri.
// Mirrors the `renderer` section of electron.vite.config.ts so the same
// source tree builds under Tauri without electron-vite.
export default defineConfig({
    root: resolve(__dirname, 'src/renderer'),
    base: './',
    define: {
        __APP_VERSION__: JSON.stringify(pkg.version)
    },
    resolve: {
        alias: {
            '@renderer': resolve(__dirname, 'src/renderer/src'),
            '@root': resolve(__dirname, '..')
        }
    },
    plugins: [vue()],
    // Tauri expects a fixed dev port and shouldn't have its logs cleared.
    clearScreen: false,
    server: {
        port: 1420,
        strictPort: true
    },
    build: {
        outDir: resolve(__dirname, 'dist-tauri'),
        emptyOutDir: true,
        rollupOptions: {
            input: {
                index: resolve(__dirname, 'src/renderer/index.html'),
                preview: resolve(__dirname, 'src/renderer/preview.html')
            }
        }
    }
})
