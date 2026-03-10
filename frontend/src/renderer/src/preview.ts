import { createApp, type Plugin } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import ReportPreviewView from './views/ReportPreviewView.vue'
import './assets/main.css'

function syncDarkClass(): void {
    const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', dark)
}
syncDarkClass()
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncDarkClass)

const app = createApp(ReportPreviewView)

app.use(ElementPlus as unknown as Plugin, { locale: zhCn })

app.mount('#app')
