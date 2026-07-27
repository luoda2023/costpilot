/**
 * v-auto-halfwidth 指令
 * 
 * 自动将输入框中的全角数字、英文、标点符号转为半角
 * 中文字符不受影响
 * 
 * 用法:
 *   <el-input v-model="xxx" v-auto-halfwidth />
 *   <input v-model="xxx" v-auto-halfwidth />
 *   <el-input-number v-model="xxx" v-auto-halfwidth />
 */
import { toHalfWidth } from '@/utils/format'

/**
 * 获取实际的输入 DOM 元素
 * Element Plus 的 el-input 会生成多层嵌套
 */
function getInputElement(el) {
  // 如果是 el-input 的根元素，找内部的 input/textarea
  const input = el.querySelector('input, textarea')
  if (input) return input
  // 原生 input
  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return el
  return el
}

/**
 * 转换输入值并更新 v-model
 */
function handleInput(el, binding, vnode) {
  const inputEl = getInputElement(el)
  if (!inputEl) return

  const original = inputEl.value
  const converted = toHalfWidth(original)

  if (original !== converted) {
    inputEl.value = converted
    // 触发 input 事件，让 v-model 更新
    inputEl.dispatchEvent(new Event('input', { bubbles: true }))
  }
}

export default {
  mounted(el, binding, vnode) {
    // 监听 input 事件（实时输入时转换）
    el.addEventListener('input', () => handleInput(el, binding, vnode))
    // 监听 blur 事件（离开输入框时再转换一次，防止遗漏）
    el.addEventListener('blur', () => handleInput(el, binding, vnode))
  },
  unmounted(el) {
    // 指令销毁时，event listener 会自动被 GC 清理
  },
}