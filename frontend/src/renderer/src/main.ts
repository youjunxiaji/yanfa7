import { createApp, type Plugin } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource-variable/inter/wght.css'
import App from './App.vue'
import router from './router'
import './assets/tokens.css'
import './assets/main.css'
import { installErrorReporting } from './api/logs'
import { initTauriBridge } from './shims/tauri-bridge'

// Install the Tauri compatibility shim before mounting so window.electronAPI
// and the persisted theme are ready for component setup. `.finally` ensures
// the app still mounts even if the bridge fails (e.g. outside Tauri).
initTauriBridge().finally(() => {
    const app = createApp(App)

    // 没接住的报错记进「日志」页
    installErrorReporting(app)
    app.use(createPinia() as unknown as Plugin)
    app.use(router as unknown as Plugin)

    app.mount('#app')
})
