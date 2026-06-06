import { createApp, type Plugin } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { initTauriBridge } from './shims/tauri-bridge'

// Install the Tauri compatibility shim before mounting so window.electronAPI
// and the persisted theme are ready for component setup. `.finally` ensures
// the app still mounts even if the bridge fails (e.g. outside Tauri).
initTauriBridge().finally(() => {
    const app = createApp(App)

    app.use(createPinia() as unknown as Plugin)
    app.use(router as unknown as Plugin)
    app.use(ElementPlus as unknown as Plugin, { locale: zhCn })

    app.mount('#app')
})
