/**
 * 全局 API 客户端
 *
 * 增强功能:
 * 1. 统一错误处理 — 网络错误/超时/服务端错误全部友好提示
 * 2. 请求重试 — 网络波动自动重试(最多 3 次)
 * 3. 离线检测 — 后端不可用时提示用户
 * 4. 请求/响应日志 — 开发调试
 */
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'

// 当从 file:// 协议加载时，/api 会变成 file:///api，必须用绝对地址
const isFileProtocol = typeof window !== 'undefined' && window.location.protocol === 'file:'
const API_HOST = 'http://127.0.0.1:8765'
const BASE = isFileProtocol ? `${API_HOST}/api/v1` : '/api/v1'

const http = axios.create({
  baseURL: BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  // 最大重试次数
  retry: 3,
  retryDelay: 1000,
})

// 后端是否在线
let _isBackendOnline = true
export function isBackendOnline() { return _isBackendOnline }

// 网络错误是否正在提示(防刷屏)
let _notifying = false
function notifyOffline() {
  if (_notifying) return
  _notifying = true
  _isBackendOnline = false
  ElNotification({
    title: '连接失败',
    message: '无法连接到后端服务 (127.0.0.1:8765)，请检查服务是否启动',
    type: 'error',
    duration: 0,
    showClose: true,
  })
  setTimeout(() => { _notifying = false }, 5000)
}

function notifyOnline() {
  if (_isBackendOnline) return
  _isBackendOnline = true
  ElNotification({
    title: '已恢复连接',
    message: '后端服务已重新连接',
    type: 'success',
    duration: 3000,
  })
}

// 请求拦截器：自动附加 Content-Type
http.interceptors.request.use(
  (config) => {
    // 如果是 FormData 上传文件，让浏览器自动设置 Content-Type
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    if (import.meta.env.DEV) {
      console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params || '')
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理 + 自动重试
http.interceptors.response.use(
  (response) => {
    // 能收到响应说明后端在线
    notifyOnline()
    return response
  },
  async (error) => {
    const config = error.config

    // 超时处理
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      // 重试逻辑
      if (config && config.retry > 0) {
        config.retry--
        if (import.meta.env.DEV) console.warn(`[API] 超时重试 (剩余${config.retry}次): ${config.url}`)
        await new Promise(r => setTimeout(r, config.retryDelay))
        return http(config)
      }
      ElMessage.error('请求超时，请检查网络或后端服务状态')
      notifyOffline()
      return Promise.reject(error)
    }

    // 网络错误(后端未启动/断网)
    if (!error.response) {
      notifyOffline()
      // 重试逻辑
      if (config && config.retry > 0) {
        config.retry--
        if (import.meta.env.DEV) console.warn(`[API] 网络错误重试 (剩余${config.retry}次): ${config.url}`)
        await new Promise(r => setTimeout(r, config.retryDelay))
        return http(config)
      }
      // 静默返回，让具体业务页面自行处理
      return Promise.reject(error)
    }

    // 服务端返回错误
    const status = error.response.status
    const data = error.response.data || {}
    const detail = data.detail || ''

    if (import.meta.env.DEV) {
      console.error(`[API Error] ${status} ${config?.url}`, detail)
    }

    // 不同状态码的友好提示
    if (status === 404) {
      // 404 不弹全局提示，由业务页面自行处理
    } else if (status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else if (status === 413) {
      ElMessage.error('文件过大，请上传 10MB 以内的文件')
    } else if (status === 422) {
      // 参数校验错误，由业务页面处理
    } else if (status === 503) {
      ElMessage.error('AI 服务暂不可用，请检查 API 配置')
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误，请稍后重试')
    }

    return Promise.reject(error)
  }
)

// 顶层便捷 API — 支持 params 透传
export const api = {
  get: (url, config) => http.get(url, config).then((r) => r.data),
  post: (url, body, config) => http.post(url, body, config).then((r) => r.data),
  delete: (url) => http.delete(url).then((r) => r.data),
}

// 业务接口
export const PricesAPI = {
  stats: () => api.get('/prices/stats'),
  specialties: () => api.get('/prices/specialties'),
  list: (params = {}) => api.get('/prices', { params }),
  search: (q, specialty, unit, limit = 20) => {
    const params = { q, limit }
    if (specialty) params.specialty = specialty
    if (unit) params.unit = unit
    return api.get('/prices/search', { params })
  },
  topics: (topic) => api.get('/prices/topics' + (topic ? `?topic=${encodeURIComponent(topic)}` : '')),
}

export const FeesAPI = {
  list: (params = {}) => api.get('/fees', { params }),
}

export const TemplatesAPI = {
  types: () => api.get('/templates/types'),
  list: (typeId) => api.get('/templates' + (typeId ? `?type_id=${typeId}` : '')),
  get: (id) => api.get(`/templates/${id}`),
  fields: (id) => api.get(`/templates/${id}/fields`),
}

export const ProjectsAPI = {
  list: () => api.get('/projects'),
  create: (data) => api.post('/projects', data),
  get: (id) => api.get(`/projects/${id}`),
  delete: (id) => api.delete(`/projects/${id}`),
  quantities: (id) => api.get(`/projects/${id}/quantities`),
  addQuantity: (id, data) => api.post(`/projects/${id}/quantities`, data),
}

export const ChatAPI = {
 createSession: (projectId) => api.post('/chat/sessions' + (projectId ? `?project_id=${projectId}` : '')),
 listSessions: () => api.get('/chat/sessions'),
 messages: (sid) => api.get(`/chat/sessions/${sid}/messages`),
 send: (sid, content) => api.post(`/chat/sessions/${sid}/messages`, { content }),
 deleteSession: (sid) => api.delete(`/chat/sessions/${sid}`),
}

export const DocGenAPI = {
 outline: (docType, stage, engType) => api.get('/ai/doc-gen/outline', { params: { doc_type: docType, stage, eng_type: engType || 'default' } }),
 generateSection: (data) => api.post('/ai/doc-gen/section', data),
}

export const ImageGenAPI = {
  generate: (data) => api.post('/ai/generate-image', data),
  imageToImage: (formData) => api.post('/ai/image-to-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }),
}

// 兼容 main.js 中所引用的 'api'
export default { http, api, PricesAPI, FeesAPI, TemplatesAPI, ProjectsAPI, ChatAPI, DocGenAPI, ImageGenAPI, isBackendOnline }