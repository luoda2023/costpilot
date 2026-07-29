<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab" type="border-card" class="settings-tabs">
      <el-tab-pane label="📝 文本 AI" name="text">
        <el-row :gutter="20">
          <el-col :span="14">
            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">文本 AI 服务配置</span></template>
              <el-form :model="form" label-width="100" size="default">
                <el-form-item label="Provider">
                  <el-select v-model="form.provider" @change="onProviderChange" style="width:100%">
                    <el-option v-for="p in providers" :key="p.name" :label="p.name + (p.needs_api_key ? '' : ' (本地)')" :value="p.name" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Base URL">
                  <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="API Key">
                  <el-input v-model="form.api_key" type="password" show-password :placeholder="form.provider === 'ollama' ? '本地无需密钥' : 'sk-...'" v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="Model">
                  <el-input v-model="form.model" placeholder="deepseek-chat" v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="Temperature">
                  <el-slider v-model="form.temperature" :min="0" :max="1" :step="0.1" show-input style="width:100%" />
                </el-form-item>
                <el-form-item label="Max Tokens">
                  <el-input-number v-model="form.max_tokens" :min="256" :max="8192" :step="256" style="width:100%" />
                </el-form-item>
                <el-form-item>
                  <div class="form-actions">
                    <el-button type="primary" @click="testConnection" :loading="testing">测试连接</el-button>
                    <el-button @click="applyChange" :loading="applying">应用配置</el-button>
                    <el-button @click="reloadYaml" :loading="reloading">从文件重载</el-button>
                  </div>
                </el-form-item>
              </el-form>
              <el-alert v-if="testResult" :title="testResult.msg" :type="testResult.ok ? 'success' : 'error'" closable @close="testResult=null" />
            </el-card>
          </el-col>

          <el-col :span="10">
            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">当前生效配置</span></template>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="Provider">{{ current.provider }}</el-descriptions-item>
                <el-descriptions-item label="base_url">{{ current.base_url }}</el-descriptions-item>
                <el-descriptions-item label="model">{{ current.model }}</el-descriptions-item>
                <el-descriptions-item label="api_key">{{ current.api_key_preview || '(未设置)' }}</el-descriptions-item>
                <el-descriptions-item label="temperature">{{ current.temperature }}</el-descriptions-item>
                <el-descriptions-item label="max_tokens">{{ current.max_tokens }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="setting-card" v-loading="loadingKb" element-loading-text="加载中...">
              <template #header><span class="card-title">知识库 RAG 状态</span></template>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="嵌入模型">{{ kb.embedding_model || 'BAAI/bge-m3' }}</el-descriptions-item>
                <el-descriptions-item label="已索引块数">{{ kb.chunks || 0 }}</el-descriptions-item>
                <el-descriptions-item label="已处理文件">{{ kb.files || 0 }}</el-descriptions-item>
              </el-descriptions>
              <el-button size="small" style="margin-top:8px" @click="loadKbStats">刷新</el-button>
            </el-card>

            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">说明</span></template>
              <ul class="notes">
                <li>「测试连接」：保存当前配置并测试 AI 服务是否可用</li>
                <li>「应用配置」：保存当前配置到 <code>config.yaml</code>（持久化，重启不丢失）</li>
                <li>「从文件重载」：重新读取 <code>config.yaml</code>（手动编辑文件后使用）</li>
                <li>API Key 不回显，修改后会自动保存到 <code>config.yaml</code></li>
                <li>切换 Provider 时，Base URL 和 Model 会自动填充默认值</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="🎨 图片 AI" name="image">
        <el-row :gutter="20">
          <el-col :span="14">
            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">图片 AI 服务配置</span></template>
              <el-form :model="imageForm" label-width="100" size="default">
                <el-form-item label="Provider">
                  <el-select v-model="imageForm.provider" @change="onImageProviderChange" style="width:100%">
                    <el-option v-for="p in imageProviders" :key="p.name" :label="p.name" :value="p.name" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Base URL">
                  <el-input v-model="imageForm.base_url" placeholder="https://api.openai.com/v1" v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="API Key">
                  <el-input v-model="imageForm.api_key" type="password" show-password placeholder="sk-..." v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="Model">
                  <el-input v-model="imageForm.model" placeholder="dall-e-3" v-auto-halfwidth />
                </el-form-item>
                <el-form-item label="Timeout">
                  <el-input-number v-model="imageForm.timeout" :min="30" :max="300" :step="10" style="width:100%" />
                </el-form-item>
                <el-form-item>
                  <div class="form-actions">
                    <el-button type="primary" @click="applyImageChange" :loading="applyingImage">保存配置</el-button>
                  </div>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="10">
            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">当前图片 AI 配置</span></template>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="Provider">{{ imageCurrent.provider }}</el-descriptions-item>
                <el-descriptions-item label="base_url">{{ imageCurrent.base_url }}</el-descriptions-item>
                <el-descriptions-item label="model">{{ imageCurrent.model }}</el-descriptions-item>
                <el-descriptions-item label="api_key">{{ imageCurrent.api_key_preview || '(未设置)' }}</el-descriptions-item>
                <el-descriptions-item label="timeout">{{ imageCurrent.timeout }}s</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="setting-card">
              <template #header><span class="card-title">图片 AI 说明</span></template>
              <ul class="notes">
                <li>图片 AI 用于在文档生成中生成配图（流程图、示意图等）</li>
                <li>支持 OpenAI DALL-E 3、阿里云通义万相、智谱 CogView</li>
                <li>需在对应平台申请 API Key</li>
                <li>配置保存后立即生效，无需重启服务</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

document.title = '造价通 - 系统设置'

const activeTab = ref('text')
const providers = ref([])
const current = ref({})
const kb = ref({})
const form = reactive({ provider: 'deepseek', base_url: '', api_key: '', model: '', temperature: 0.3, max_tokens: 4096 })
const testing = ref(false); const applying = ref(false); const reloading = ref(false); const testResult = ref(null)
const loadingKb = ref(false)

// 图片 AI
const imageProviders = ref([
  { name: 'openai', base_url: 'https://api.openai.com/v1', default_model: 'dall-e-3' },
  { name: 'qwen', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', default_model: 'wanx-v1' },
  { name: 'zhipu', base_url: 'https://open.bigmodel.cn/api/paas/v4', default_model: 'cogview-3' },
])
const imageCurrent = ref({})
const imageForm = reactive({ provider: 'openai', base_url: '', api_key: '', model: 'dall-e-3', timeout: 120 })
const applyingImage = ref(false)

async function loadProviders() {
  try { providers.value = await api.get('/ai/providers') }
  catch { ElMessage.error('加载 Provider 列表失败') }
}

async function loadCurrent() {
  try {
    const r = await api.get('/ai/config')
    current.value = r
    Object.assign(form, {
      provider: r.provider,
      base_url: r.base_url,
      model: r.model,
      temperature: r.temperature,
      max_tokens: r.max_tokens,
    })
  } catch { ElMessage.error('加载当前配置失败') }
}

async function loadImageConfig() {
  try {
    const r = await api.get('/ai/image-config')
    imageCurrent.value = r
    Object.assign(imageForm, {
      provider: r.provider,
      base_url: r.base_url,
      model: r.model,
      timeout: r.timeout,
    })
  } catch { /* 图片AI配置可能不存在 */ }
}

async function loadKbStats() {
  loadingKb.value = true
  try {
    const [stats, prog] = await Promise.all([api.get('/kb/stats'), api.get('/kb/progress')])
    kb.value = { ...stats, ...prog }
  } catch { kb.value = { error: '未就绪' } }
  finally { loadingKb.value = false }
}

function onProviderChange(name) {
  const p = providers.value.find(x => x.name === name)
  if (p) { form.base_url = p.base_url; form.model = p.default_model }
}

function onImageProviderChange(name) {
  const p = imageProviders.value.find(x => x.name === name)
  if (p) { imageForm.base_url = p.base_url; imageForm.model = p.default_model }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const r = await api.post('/ai/switch', form)
    if (r.ok) {
      const t = await api.post('/ai/test')
      testResult.value = t
    } else {
      testResult.value = { ok: false, msg: r.msg }
    }
  } catch (e) {
    testResult.value = { ok: false, msg: '连接失败: ' + (e.response?.data?.detail || e.message) }
  } finally { testing.value = false }
}

async function applyChange() {
  applying.value = true
  try {
    const r = await api.post('/ai/switch', form)
    if (r.ok) {
      ElMessage.success(`已切换: ${r.current.provider} / ${r.current.model}`)
      await loadCurrent()
    } else {
      ElMessage.error(r.msg)
    }
  } catch (e) {
    ElMessage.error('应用配置失败: ' + (e.response?.data?.detail || e.message))
  } finally { applying.value = false }
}

async function applyImageChange() {
  applyingImage.value = true
  try {
    const r = await api.post('/ai/image-switch', imageForm)
    if (r.ok) {
      ElMessage.success('图片 AI 配置已保存')
      await loadImageConfig()
    } else {
      ElMessage.error(r.msg)
    }
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally { applyingImage.value = false }
}

async function reloadYaml() {
  reloading.value = true
  try {
    await api.post('/ai/reload')
    ElMessage.success('config.yaml 已重载')
    await loadCurrent()
    await loadImageConfig()
  } catch (e) {
    ElMessage.error('重载失败: ' + (e.response?.data?.detail || e.message))
  } finally { reloading.value = false }
}

onMounted(() => { loadProviders(); loadCurrent(); loadImageConfig(); loadKbStats() })
</script>

<style scoped>
.settings-page { padding:8px; }
.settings-tabs { border-radius:8px; }
.setting-card { border-radius:8px; margin-bottom:16px; }
.card-title { font-size:15px; font-weight:600; color: var(--text-primary); line-height:1.5; }
.form-actions { display:flex; gap:10px; }
.notes { margin:0; padding-left:16px; line-height:1.6; font-size:14px; color:#606266; }
.notes code { background:#f4f4f5; padding:2px 6px; border-radius:3px; font-size:13px; }
</style>