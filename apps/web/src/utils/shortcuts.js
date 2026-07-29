/**
 * 全局键盘快捷键
 *
 * 用法:
 *   useShortcuts().register(handler)
 *   handler 返回 true 表示已处理
 *
 * 内置快捷键:
 *   Ctrl+1~9 → 切换到对应导航
 *   Ctrl+K   → 聚焦搜索(如果有)
 *   Escape   → 关闭对话框/取消选择
 */
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const shortcuts = [
  { key: '1', ctrl: true, path: '/workspace', desc: '工作台' },
  { key: '2', ctrl: true, path: '/chat', desc: 'AI 助手' },
  { key: '3', ctrl: true, path: '/prices', desc: '价格库' },
  { key: '4', ctrl: true, path: '/quote', desc: '报价生成' },
  { key: '5', ctrl: true, path: '/docgen', desc: '文档生成' },
  { key: '6', ctrl: true, path: '/text-gen', desc: '文本生成' },
  { key: '7', ctrl: true, path: '/preview', desc: '文件预览' },
  { key: '8', ctrl: true, path: '/settings', desc: '系统设置' },
  { key: '9', ctrl: true, path: '/image-gen', desc: '图片生成' },
]

export function useShortcuts() {
  const router = useRouter()
  const handlers = []

  function onKeyDown(e) {
    // 如果焦点在输入框中，不拦截快捷键（Ctrl+Enter 除外）
    const tag = document.activeElement?.tagName
    const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.contentEditable === 'true'

    // 先执行自定义 handlers
    for (const handler of handlers) {
      if (handler(e)) return
    }

    // Ctrl+数字 → 切换页面
    if (e.ctrlKey && !e.shiftKey && !e.altKey && e.key >= '1' && e.key <= '9') {
      const s = shortcuts.find(s => s.key === e.key)
      if (s) {
        e.preventDefault()
        router.push(s.path)
        return
      }
    }

    // Ctrl+K → 打开搜索(如果有)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      // 触发全局搜索事件，组件可以监听
      window.dispatchEvent(new CustomEvent('global-search'))
      e.preventDefault()
      return
    }

    // Escape → 在非输入框时取消
    if (e.key === 'Escape' && !isInput) {
      window.dispatchEvent(new CustomEvent('global-escape'))
      return
    }
  }

  function register(handler) {
    handlers.push(handler)
    return () => {
      const idx = handlers.indexOf(handler)
      if (idx >= 0) handlers.splice(idx, 1)
    }
  }

  onMounted(() => window.addEventListener('keydown', onKeyDown))
  onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

  return { register, shortcuts }
}

/** 在导航栏显示快捷键提示 */
export function shortcutHint(key, ctrl = true) {
  if (ctrl) return 'Ctrl+' + key
  return key
}