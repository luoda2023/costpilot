/**
 * 全局 API 客户端
 */
import axios from 'axios'

// API 基址 - Electron 通过 vite proxy 转发到本地 FastAPI
const BASE = '/api'

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

// 顶层便捷 API
export const api = {
  get: (url) => http.get(url).then((r) => r.data),
  post: (url, body) => http.post(url, body).then((r) => r.data),
  delete: (url) => http.delete(url).then((r) => r.data),
}

// 业务接口
export const PricesAPI = {
  stats: () => api.get('/v1/prices/stats'),
  specialties: () => api.get('/v1/prices/specialties'),
  list: (params = {}) => api.get('/v1/prices' + (Object.keys(params).length ? '?' + new URLSearchParams(params) : '')),
  search: (q, limit = 20) => api.get(`/v1/prices/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  topics: (topic) => api.get('/v1/prices/topics' + (topic ? `?topic=${encodeURIComponent(topic)}` : '')),
}

export const FeesAPI = {
  list: (params = {}) => api.get('/v1/fees' + (Object.keys(params).length ? '?' + new URLSearchParams(params) : '')),
}

export const TemplatesAPI = {
  types: () => api.get('/v1/templates/types'),
  list: (typeId) => api.get('/v1/templates' + (typeId ? `?type_id=${typeId}` : '')),
  get: (id) => api.get(`/v1/templates/${id}`),
  fields: (id) => api.get(`/v1/templates/${id}/fields`),
}

export const ProjectsAPI = {
  list: () => api.get('/v1/projects'),
  create: (data) => api.post('/v1/projects', data),
  get: (id) => api.get(`/v1/projects/${id}`),
  delete: (id) => api.delete(`/v1/projects/${id}`),
  quantities: (id) => api.get(`/v1/projects/${id}/quantities`),
  addQuantity: (id, data) => api.post(`/v1/projects/${id}/quantities`, data),
}

export const ChatAPI = {
  createSession: (projectId) => api.post('/v1/chat/sessions' + (projectId ? `?project_id=${projectId}` : '')),
  listSessions: () => api.get('/v1/chat/sessions'),
  messages: (sid) => api.get(`/v1/chat/sessions/${sid}/messages`),
  send: (sid, content) => api.post(`/v1/chat/sessions/${sid}/messages`, { content }),
}

// 兼容 main.js 中所引用的 'api'
export default { http, api, PricesAPI, FeesAPI, TemplatesAPI, ProjectsAPI, ChatAPI }
