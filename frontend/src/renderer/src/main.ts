import { createApp, type Plugin } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

app.use(createPinia() as unknown as Plugin)
app.use(router as unknown as Plugin)
app.use(ElementPlus as unknown as Plugin, { locale: zhCn })

app.mount('#app')
