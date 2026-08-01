<template>
<div class="settings-page">
<el-tabs v-model="activeTab" type="border-card" class="settings-tabs">
<el-tab-pane label="💬 AI 服务" name="text">
<el-row :gutter="20">
<el-col :span="16">
<!-- 默认内置配置 -->
<el-card shadow="never" class="setting-card">
<template #header>
<div class="card-header">
<span class="card-title">⭐ 默认配置（内置免费试用）</span>
<el-tag v-if="usage" :type="usage.text_remaining > 10 ? 'success' : (usage.text_remaining > 0 ? 'warning' : 'danger')" size="small">
{{ usage.text_remaining }}/{{ usage.max_free_calls }} 次
</el-tag>
</div>
</template>
<el-descriptions :column="1" border size="small">
<el-descriptions-item label="Model">{{ defaultConfig.model }}</el-descriptions-item>
<el-descriptions-item label="Base URL">{{ defaultConfig.base_url }}</el-descriptions-item>
<el-descriptions-item label="API Key">{{ defaultConfig.api_key_preview || '(内置)' }}</el-descriptions-item>
<el-descriptions-item label="Temperature">{{ defaultConfig.temperature }}</el-descriptions-item>
<el-descriptions-item label="Max Tokens">{{ defaultConfig.max_tokens }}</el-descriptions-item>
</el-descriptions>
<div class="card-actions">
<el-button size="small" type="primary" @click="testConnection" :loading="testing">测试连接</el-button>
<el-button size="small" @click="reloadYaml" :loading="reloading">刷新</el-button>
</div>
<el-alert v-if="testResult" :title="testResult.msg" :type="testResult.ok ? 'success' : 'error'" closable @close="testResult=null" style="margin-top:12px" />
</el-card>

<!-- 自定义配置列表 -->
<el-card shadow="never" class="setting-card">
<template #header>
<div class="card-header">
<span class="card-title">自定义 AI 配置</span>
<el-button size="small" type="primary" @click="showAddDialog = true">+ 新增</el-button>
</div>
</template>

<div v-if="customConfigs.length === 0" class="empty-hint">
暂无自定义配置，点击「+ 新增」添加你自己的 AI 服务
</div>

<div v-for="cfg in customConfigs" :key="cfg.id" class="custom-config-item">
<div class="config-info">
<div class="config-model">
<el-icon :size="16"><Monitor /></el-icon>
<strong>{{ cfg.model }}</strong>
</div>
<div class="config-url">{{ cfg.base_url }}</div>
<div class="config-key">API Key: {{ cfg.api_key || '(未设置)' }}</div>
</div>
<div class="config-actions">
<el-button size="small" circle @click="editCustomConfig(cfg)" :icon="Edit" />
<el-button size="small" circle @click="deleteCustomConfig(cfg.id)" :icon="Delete" type="danger" plain />
</div>
</div>
</el-card>
</el-col>

<el-col :span="8">
<el-card shadow="never" class="setting-card">
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
<li>默认配置内置了免费试用密钥，可直接使用</li>
<li>免费试用限制 <strong>100 次</strong>，用完请添加自己的 API Key</li>
<li>点击「+ 新增」可添加任意 OpenAI 兼容的 AI 服务</li>
<li>API Key 保存后不回显，修改需重新输入</li>
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
<el-descriptions-item label="base_url">{{ imageCurrent.base_url }}</el-descriptions-item>
<el-descriptions-item label="model">{{ imageCurrent.model }}</el-descriptions-item>
<el-descriptions-item label="api_key">{{ imageCurrent.api_key_preview || '(未设置)' }}</el-descriptions-item>
<el-descriptions-item label="timeout">{{ imageCurrent.timeout }}s</el-descriptions-item>
</el-descriptions>
</el-card>

<el-card shadow="never" class="setting-card">
<template #header><span class="card-title">图片 AI 说明</span></template>
<ul class="notes">
<li>图片 AI 用于在文档生成中生成配图</li>
<li>支持 OpenAI DALL-E 3 / 通义万相 / 智谱 CogView 等</li>
<li>需在对应平台申请 API Key</li>
</ul>
</el-card>
</el-col>
</el-row>
</el-tab-pane>
</el-tabs>

<!-- 新增/编辑自定义配置对话框 -->
<el-dialog v-model="showAddDialog" :title="editingId ? '编辑自定义配置' : '新增自定义 AI 配置'" width="500px">
<el-form :model="editForm" label-width="100" size="default">
<el-form-item label="Model" required>
<el-input v-model="editForm.model" placeholder="gpt-4o-mini / deepseek-chat" />
</el-form-item>
<el-form-item label="Base URL" required>
<el-input v-model="editForm.base_url" placeholder="https://api.openai.com/v1" />
</el-form-item>
<el-form-item label="API Key" required>
<el-input v-model="editForm.api_key" type="password" show-password placeholder="sk-..." />
</el-form-item>
<el-form-item label="Temperature">
<el-slider v-model="editForm.temperature" :min="0" :max="1" :step="0.1" show-input style="width:100%" />
</el-form-item>
<el-form-item label="Max Tokens">
<el-input-number v-model="editForm.max_tokens" :min="256" :max="8192" :step="256" style="width:100%" />
</el-form-item>
<el-form-item label="Timeout">
<el-input-number v-model="editForm.timeout" :min="30" :max="300" :step="10" style="width:100%" />
</el-form-item>
</el-form>
<template #footer>
<el-button @click="showAddDialog = false">取消</el-button>
<el-button type="primary" @click="saveCustomConfig" :loading="savingCustom">保存</el-button>
</template>
</el-dialog>
</div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, UsageAPI, CustomAIConfigAPI } from '@/api'
import { Monitor, Edit, Delete } from '@element-plus/icons-vue'

document.title = '造价通 - 系统设置'

const activeTab = ref('text')
const defaultConfig = ref({})
const usage = ref(null)
const customConfigs = ref([])
const kb = ref({})
const testing = ref(false)
const reloading = ref(false)
const testResult = ref(null)
const loadingKb = ref(false)

// 新增/编辑对话框
const showAddDialog = ref(false)
const editingId = ref(null)
const savingCustom = ref(false)
const editForm = reactive({
model: '',
base_url: '',
api_key: '',
temperature: 0.3,
max_tokens: 4096,
timeout: 120,
})

// 图片 AI
const imageCurrent = ref({})
const imageForm = reactive({ provider: 'openai', base_url: '', api_key: '', model: 'dall-e-3', timeout: 120 })
const applyingImage = ref(false)

async function loadDefaultConfig() {
try {
const r = await api.get('/ai/config')
defaultConfig.value = r
} catch { /* 忽略 */ }
}

async function loadUsage() {
try {
usage.value = await UsageAPI.get()
} catch { /* 忽略 */ }
}

async function loadCustomConfigs() {
try {
customConfigs.value = await CustomAIConfigAPI.list()
} catch { /* 忽略 */ }
}

async function loadKbStats() {
loadingKb.value = true
try {
const [stats, prog] = await Promise.all([api.get('/kb/stats'), api.get('/kb/progress')])
kb.value = { ...stats, ...prog }
} catch { kb.value = { error: '未就绪' } }
finally { loadingKb.value = false }
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
} catch { /* 忽略 */ }
}

async function testConnection() {
testing.value = true
testResult.value = null
try {
const t = await api.post('/ai/test')
testResult.value = t
} catch (e) {
testResult.value = { ok: false, msg: '连接失败: ' + (e.response?.data?.detail || e.message) }
} finally { testing.value = false }
}

async function reloadYaml() {
reloading.value = true
try {
await api.post('/ai/reload')
ElMessage.success('配置已重载')
await loadDefaultConfig()
await loadUsage()
await loadImageConfig()
} catch (e) {
ElMessage.error('重载失败: ' + (e.response?.data?.detail || e.message))
} finally { reloading.value = false }
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

// 新增/编辑自定义配置
function editCustomConfig(cfg) {
editingId.value = cfg.id
editForm.model = cfg.model
editForm.base_url = cfg.base_url
editForm.api_key = '' // 不回显
editForm.temperature = cfg.temperature
editForm.max_tokens = cfg.max_tokens
editForm.timeout = cfg.timeout
showAddDialog.value = true
}

async function saveCustomConfig() {
if (!editForm.model || !editForm.base_url) {
ElMessage.warning('请填写 Model 和 Base URL')
return
}
if (!editingId.value && !editForm.api_key) {
ElMessage.warning('请填写 API Key')
return
}
savingCustom.value = true
try {
if (editingId.value) {
await CustomAIConfigAPI.update(editingId.value, editForm)
ElMessage.success('已更新')
} else {
await CustomAIConfigAPI.create(editForm)
ElMessage.success('已新增')
}
showAddDialog.value = false
editingId.value = null
resetEditForm()
await loadCustomConfigs()
} catch (e) {
ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
} finally { savingCustom.value = false }
}

async function deleteCustomConfig(id) {
try {
await ElMessageBox.confirm('确定删除此配置？', '提示', { type: 'warning' })
await CustomAIConfigAPI.delete(id)
ElMessage.success('已删除')
await loadCustomConfigs()
} catch (e) {
if (e !== 'cancel') ElMessage.error('删除失败')
}
}

function resetEditForm() {
editForm.model = ''
editForm.base_url = ''
editForm.api_key = ''
editForm.temperature = 0.3
editForm.max_tokens = 4096
editForm.timeout = 120
}

onMounted(() => {
loadDefaultConfig()
loadUsage()
loadCustomConfigs()
loadImageConfig()
loadKbStats()
})
</script>

<style scoped>
.settings-page { padding: 8px; }
.settings-tabs { border-radius: 8px; }
.setting-card { border-radius: 8px; margin-bottom: 16px; }
.card-title { font-size: 15px; font-weight: 600; color: var(--text-primary); line-height: 1.5; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-actions { margin-top: 12px; display: flex; gap: 8px; }
.form-actions { display: flex; gap: 10px; }
.notes { margin: 0; padding-left: 16px; line-height: 1.6; font-size: 14px; color: #606266; }
.notes code { background: #f4f4f5; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
.empty-hint { color: #999; text-align: center; padding: 24px; font-size: 14px; }

.custom-config-item {
display: flex;
justify-content: space-between;
align-items: flex-start;
padding: 12px 16px;
border: 1px solid var(--gray-200);
border-radius: 8px;
margin-bottom: 8px;
transition: all 0.2s;
}
.custom-config-item:hover {
border-color: var(--brand-500);
background: #f8faff;
}
.config-info { flex: 1; min-width: 0; }
.config-model { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.config-model strong { font-size: 15px; color: var(--text-primary); }
.config-url { font-size: 12px; color: #999; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.config-key { font-size: 12px; color: #bbb; }
.config-actions { display: flex; gap: 4px; margin-left: 12px; flex-shrink: 0; }
</style>