<template>
  <div class="settings-page">
    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span>AI 服务配置</span></template>
          <el-form :model="form" label-width="120">
            <el-form-item label="Provider">
              <el-select v-model="form.provider" @change="onProviderChange" style="width:100%">
                <el-option v-for="p in providers" :key="p.name" :label="p.name + (p.needs_api_key ? '' : '(本地,无需密钥)')" :value="p.name">
                  <span>{{ p.name }}</span>
                  <span style="float:right;color:#909399;font-size:12px">{{ p.default_model }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="base_url">
              <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
            </el-form-item>
            <el-form-item label="api_key">
              <el-input v-model="form.api_key" type="password" show-password :placeholder="form.provider === 'ollama' ? '本地无需密钥' : 'sk-...'" />
            </el-form-item>
            <el-form-item label="model">
              <el-input v-model="form.model" placeholder="deepseek-chat" />
            </el-form-item>
            <el-form-item label="temperature">
              <el-slider v-model="form.temperature" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
            <el-form-item label="max_tokens">
              <el-input-number v-model="form.max_tokens" :min="256" :max="8192" :step="256" style="width:100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="testConnection" :loading="testing">测试连接</el-button>
              <el-button @click="applyChange" :loading="applying">应用配置(运行时)</el-button>
              <el-button @click="reloadYaml" :loading="reloading">从 config.yaml 重载</el-button>
            </el-form-item>
          </el-form>
          <el-alert v-if="testResult" :title="testResult.msg" :type="testResult.ok ? 'success' : 'error'" closable @close="testResult=null" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span>当前生效配置</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="Provider">{{ current.provider }}</el-descriptions-item>
            <el-descriptions-item label="base_url">{{ current.base_url }}</el-descriptions-item>
            <el-descriptions-item label="model">{{ current.model }}</el-descriptions-item>
            <el-descriptions-item label="api_key">{{ current.api_key_preview || '(未设置)' }}</el-descriptions-item>
            <el-descriptions-item label="temperature">{{ current.temperature }}</el-descriptions-item>
            <el-descriptions-item label="max_tokens">{{ current.max_tokens }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never" style="margin-top:16px">
          <template #header><span>说明</span></template>
          <ul class="notes">
            <li>「应用配置」仅切换本次运行时,不改 config.yaml,重启后还原</li>
            <li>持久化请直接编辑 <code>H:\AI-model\造价通\config.yaml</code> 后点「从 config.yaml 重载」</li>
            <li>api_key 出于安全不回显,保存到 config.yaml 后下次启动自动加载</li>
          </ul>
        </el-card>

        <el-card shadow="never" style="margin-top:16px">
          <template #header><span>知识库 RAG 状态</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="嵌入模型">{{ kb.embedding_model || 'BAAI/bge-m3' }}</el-descriptions-item>
            <el-descriptions-item label="已索引块数">{{ kb.chunks || 0 }}</el-descriptions-item>
            <el-descriptions-item label="已处理文件">{{ kb.files || 0 }}</el-descriptions-item>
          </el-descriptions>
          <el-button style="margin-top:8px" @click="loadKbStats">刷新</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const apiUrl = '/api/v1'

const providers = ref([])
const current = ref({})
const kb = ref({})
const form = reactive({
  provider: 'deepseek',
  base_url: '',
  api_key: '',
  model: '',
  temperature: 0.3,
  max_tokens: 4096,
})

const testing = ref(false)
const applying = ref(false)
const reloading = ref(false)
const testResult = ref(null)

async function loadProviders() {
  const r = await axios.get(apiUrl + '/ai/providers')
  providers.value = r.data
}

async function loadCurrent() {
  const r = await axios.get(apiUrl + '/ai/config')
  current.value = r.data
  form.provider = r.data.provider
  form.base_url = r.data.base_url
  form.model = r.data.model
  form.temperature = r.data.temperature
  form.max_tokens = r.data.max_tokens
}

async function loadKbStats() {
  try {
    const [stats, prog] = await Promise.all([
      axios.get(apiUrl + '/kb/stats'),
      axios.get(apiUrl + '/kb/progress'),
    ])
    kb.value = { ...stats.data, ...prog.data }
  } catch (e) {
    kb.value = { error: '未就绪' }
  }
}

function onProviderChange(name) {
  // 自动回填默认 base_url + model
  const p = providers.value.find(x => x.name === name)
  if (p) {
    form.base_url = p.base_url
    form.model = p.default_model
  }
}

async function testConnection() {
  testing.value = true
  try {
    const r = await axios.post(apiUrl + '/ai/switch', form)
    if (r.data.ok) {
      const t = await axios.post(apiUrl + '/ai/test')
      testResult.value = t.data
    } else {
      testResult.value = { ok: false, msg: r.data.msg }
    }
  } catch (e) {
    testResult.value = { ok: false, msg: e.response?.data?.detail || e.message }
  } finally {
    testing.value = false
  }
}

async function applyChange() {
  applying.value = true
  try {
    const r = await axios.post(apiUrl + '/ai/switch', form)
    if (r.data.ok) {
      ElMessage.success(`已切换: ${r.data.current.provider} / ${r.data.current.model}`)
      await loadCurrent()
    } else {
      ElMessage.error(r.data.msg)
    }
  } finally {
    applying.value = false
  }
}

async function reloadYaml() {
  reloading.value = true
  try {
    await axios.post(apiUrl + '/ai/reload')
    ElMessage.success('config.yaml 已重载')
    await loadCurrent()
  } finally {
    reloading.value = false
  }
}

onMounted(() => {
  loadProviders()
  loadCurrent()
  loadKbStats()
})
</script>

<style scoped>
.settings-page { padding:8px; }
.notes { margin: 0; padding-left: 16px; line-height: 1.8; }
.notes code { background: #f4f4f5; padding: 2px 6px; border-radius: 3px; }
</style>
