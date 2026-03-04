import { createApp, type Plugin } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import ReportPreviewView from './views/ReportPreviewView.vue'
import './assets/main.css'

const app = createApp(ReportPreviewView)

app.use(ElementPlus as unknown as Plugin, { locale: zhCn })

app.mount('#app')
