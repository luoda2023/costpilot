import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'highlight.js/styles/github-dark.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import autoHalfWidth from './directives/autoHalfWidth'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册全局指令：自动转换全角→半角
app.directive('auto-halfwidth', autoHalfWidth)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
