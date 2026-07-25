<template>
  <div class="ai-setup-wizard">
    <!-- 全屏遮罩 -->
    <div class="wizard-overlay">
      <div class="wizard-card">
        <!-- 顶部 -->
        <div class="wizard-header">
          <div class="wizard-logo">
            <el-icon :size="36" color="#409eff"><Coin /></el-icon>
            <h1>欢迎使用工程助手</h1>
          </div>
          <p class="wizard-subtitle">请先配置 AI 服务，所有功能由 AI 驱动</p>
        </div>

        <!-- 步骤指示器 -->
        <div class="steps">
          <div class="step" :class="{ active: step >= 1, done: step > 1 }">
            <div class="step-circle">1</div>
            <span class="step-label">选择 Provider</span>
          </div>
          <div class="step-line" :class="{ active: step >= 2 }"></div>
          <div class="step" :class="{ active: step >= 2, done: step > 2 }">
            <div class="step-circle">2</div>
            <span class="step-label">填写 API Key</span>
          </div>
          <div class="step-line" :class="{ active: step >= 3 }"></div>
          <div class="step" :class="{ active: step >= 3, done: step > 3 }">
            <div class="step-circle">3</div>
            <span class="step-label">测试连接</span>
          </div>
        </div>

        <!-- 步骤 1: 选择 Provider -->
        <div v-if="step === 1" class="step-content">
          <h3>选择 AI 服务商</h3>
          <div class="provider-grid">
            <div
              v-for="p in providers"
              :key="p.name"
              class="provider-card"
              :class="{ selected: form.provider === p.name }"
              @click="selectProvider(p)"
            >
              <div class="provider-name">{{ p.name }}</div>
              <div class="provider-model">{{ p.default_model }}</div>
              <div v-if="p.note" class="provider-note">{{ p.note }}</div>
              <div v-if="!p.needs_api_key" class="provider-badge">本地</div>
            </div>
          </div>
          <div class="step-actions">
            <el-button type="primary" size="large" @click="step = 2" :disabled="!form.provider">
              下一步
            </el-button>
          </div>
        </div>

        <!-- 步骤 2: 填写 API Key -->
        <div v-if="step === 2" class="step-content">
          <h3>{{ form.provider === 'ollama' ? '本地模型无需 API Key' : '填写 API Key' }}</h3>
          <el-form :model="form" label-width="100" size="large">
            <el-form-item label="Base URL">
              <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
            </el-form-item>
            <el-form-item v-if="form.provider !== 'ollama'" label="API Key">
              <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
            </el-form-item>
            <el-form-item label="Model">
              <el-input v-model="form.model" placeholder="deepseek-chat" />
            </el-form-item>
          </el-form>
          <div class="step-actions">
            <el-button @click="step = 1" size="large">上一步</el-button>
            <el-button type="primary" size="large" @click="step = 3" :disabled="form.provider !== 'ollama' && !form.api_key">
              下一步
            </el-button>
          </div>
        </div>

        <!-- 步骤 3: 测试连接 -->
        <div v-if="step === 3" class="step-content">
          <h3>测试连接</h3>
          <div class="config-summary">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="Provider">{{ form.provider }}</el-descriptions-item>
              <el-descriptions-item label="Base URL">{{ form.base_url }}</el-descriptions-item>
              <el-descriptions-item label="Model">{{ form.model }}</el-descriptions-item>
              <el-descriptions-item label="API Key">{{ form.api_key ? '已设置' : '未设置' }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="step-actions">
            <el-button @click="step = 2" size="large">上一步</el-button>
            <el-button type="primary" size="large" @click="testAndSave" :loading="testing" :disabled="!form.api_key && form.provider !== 'ollama'">
              {{ testing ? '测试中...' : '测试并完成配置' }}
            </el-button>
          </div>
          <el-alert
            v-if="testResult"
            :title="testResult.msg"
            :type="testResult.ok ? 'success' : 'error'"
            :closable="false"
            style="margin-top: 16px"
          />
        </div>

        <!-- 完成状态 -->
        <div v-if="step === 4" class="step-content">
          <div class="done-state">
            <el-icon :size="64" color="#67c23a"><CircleCheck /></el-icon>
            <h2>配置完成！</h2>
            <p>AI 服务已就绪，即将进入系统...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const emit = defineEmits(['configured'])

const apiUrl = '/api/v1'
const step = ref(1)
const providers = ref([])
const testing = ref(false)
const testResult = ref(null)
const form = reactive({
  provider: '',
  base_url: '',
  api_key: '',
  model: '',
})

async function loadProviders() {
  try {
    const r = await axios.get(apiUrl + '/ai/providers')
    providers.value = r.data
    if (r.data.length) {
      const first = r.data[0]
      form.provider = first.name
      form.base_url = first.base_url
      form.model = first.default_model
    }
  } catch (e) {
    ElMessage.error('加载 Provider 列表失败: ' + (e.response?.data?.detail || e.message))
  }
}

function selectProvider(p) {
  form.provider = p.name
  form.base_url = p.base_url
  form.model = p.default_model
  if (!p.needs_api_key) {
    form.api_key = 'local'
  }
}

async function testAndSave() {
  testing.value = true
  testResult.value = null
  try {
    // 先保存配置
    await axios.post(apiUrl + '/ai/switch', {
      provider: form.provider,
      base_url: form.base_url || undefined,
      api_key: form.api_key || undefined,
      model: form.model || undefined,
    })
    // 再测试连接
    const t = await axios.post(apiUrl + '/ai/test')
    testResult.value = t.data
    if (t.data.ok) {
      step.value = 4
      setTimeout(() => emit('configured'), 1500)
    }
  } catch (e) {
    testResult.value = { ok: false, msg: '配置失败: ' + (e.response?.data?.detail || e.message) }
  } finally {
    testing.value = false
  }
}

onMounted(loadProviders)
</script>

<style scoped>
.wizard-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.wizard-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  width: 560px;
  max-width: 90vw;
  padding: 40px;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.wizard-header {
  text-align: center;
  margin-bottom: 32px;
}

.wizard-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.wizard-logo h1 {
  margin: 0;
  font-size: 24px;
  color: #1a2332;
}

.wizard-subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-circle {
  background: #409eff;
  color: #fff;
}

.step.done .step-circle {
  background: #67c23a;
  color: #fff;
}

.step-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.step.active .step-label {
  color: #409eff;
  font-weight: 600;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #e4e7ed;
  margin: 0 8px;
  margin-bottom: 24px;
  transition: all 0.3s;
}

.step-line.active {
  background: #409eff;
}

.step-content {
  min-height: 260px;
}

.step-content h3 {
  font-size: 16px;
  color: #303133;
  margin: 0 0 20px;
}

.provider-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 24px;
}

.provider-card {
  padding: 16px;
  border: 2px solid #ebeef5;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.provider-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64,158,255,0.1);
}

.provider-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.provider-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.provider-model {
  font-size: 12px;
  color: #909399;
}

.provider-note {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
}

.provider-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #67c23a;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.step-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

.config-summary {
  margin-bottom: 20px;
}

.done-state {
  text-align: center;
  padding: 40px 0;
}

.done-state h2 {
  margin: 16px 0 8px;
  color: #303133;
}

.done-state p {
  color: #909399;
  font-size: 14px;
}
</style>