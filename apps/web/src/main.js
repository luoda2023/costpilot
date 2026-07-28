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

// ============================================================
// 全局错误处理 — 防止白屏、静默崩溃
// ============================================================

// 1. Vue 渲染错误
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err)
  console.error('  组件:', instance?.$options?.name || instance?.__name || '未知')
  console.error('  信息:', info)
  // 不弹窗打断用户，但 console 能定位问题
}

// 2. 未捕获 Promise 异常
window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  console.error('[Unhandled Promise]', reason?.message || reason)
  // 避免静默失败
  if (reason?.response?.status === 503) {
    // AI 服务不可用，已在 API 层提示
  } else if (reason?.message?.includes('timeout')) {
    // 超时已在 API 层处理
  } else {
    console.warn('[Unhandled Promise] 未处理的异步错误:', reason?.message || reason)
  }
  event.preventDefault()
})

// 3. 全局普通异常
window.addEventListener('error', (event) => {
  console.error('[Global Error]', event.message, event.filename, event.lineno)
  // 防止页面崩溃
  event.preventDefault()
})

app.mount('#app')