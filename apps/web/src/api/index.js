/**
 * 全局 API 客户端
 */
import axios from 'axios'

// 当从 file:// 协议加载时，/api 会变成 file:///api，必须用绝对地址
// 检测当前协议，自动选择 base URL
const isFileProtocol = typeof window !== 'undefined' && window.location.protocol === 'file:'
const API_HOST = 'http://127.0.0.1:8765'
const BASE = isFileProtocol ? `${API_HOST}/api/v1` : '/api/v1'

const http = axios.create({
  baseURL: BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 统一错误处理
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('[API Error]', error.response.status, error.response.data)
    } else {
      console.error('[API Error]', error.message)
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
  search: (q, limit = 20) => api.get(`/prices/search?q=${encodeURIComponent(q)}&limit=${limit}`),
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

// 兼容 main.js 中所引用的 'api'
export default { http, api, PricesAPI, FeesAPI, TemplatesAPI, ProjectsAPI, ChatAPI }
