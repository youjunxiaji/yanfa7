import { resolve } from 'path'
import { defineConfig } from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import pkg from './package.json'

export default defineConfig({
    main: {
        build: {
            externalizeDeps: {
                exclude: ['electron-store']
            }
        }
    },
    preload: {
        build: {
            rollupOptions: {
                input: {
                    index: resolve(__dirname, 'src/preload/index.ts'),
                    preview: resolve(__dirname, 'src/preload/preview.ts')
                }
            }
        }
    },
    renderer: {
        define: {
            __APP_VERSION__: JSON.stringify(pkg.version)
        },
        resolve: {
            alias: {
                '@renderer': resolve('src/renderer/src'),
                '@root': resolve('../')
            }
        },
        plugins: [vue()],
        build: {
            rollupOptions: {
                input: {
                    index: resolve(__dirname, 'src/renderer/index.html'),
                    preview: resolve(__dirname, 'src/renderer/preview.html')
                }
            }
        }
    }
})
