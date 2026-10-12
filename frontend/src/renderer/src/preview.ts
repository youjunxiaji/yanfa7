import { createApp, h } from 'vue'
import '@fontsource-variable/inter/wght.css'
import AppProviders from './components/AppProviders.vue'
import ReportPreviewView from './views/ReportPreviewView.vue'
import './assets/tokens.css'
import './assets/main.css'
import { initTauriBridge } from './shims/tauri-bridge'

const syncDarkClass = (): void => {
    const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', dark)
}
syncDarkClass()
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncDarkClass)

// previewAPI must exist before ReportPreviewView reads its search params.
initTauriBridge().finally(() => {
    const app = createApp({
        render: () => h(AppProviders, null, { default: () => h(ReportPreviewView) })
    })

    app.mount('#app')
})
