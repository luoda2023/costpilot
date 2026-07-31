<template>
  <div class="ai-setup-wizard">
    <!-- 全屏遮罩 -->
    <div class="wizard-overlay">
      <div class="wizard-card">
        <!-- 顶部 -->
        <div class="wizard-header">
          <div class="wizard-logo">
            <div class="logo-icon">⚙</div>
            <div>
              <h1>AI 服务配置</h1>
              <p class="wizard-subtitle">填写你的 AI 服务信息，即可开始使用</p>
            </div>
          </div>
        </div>

        <!-- 配置表单 -->
        <div class="config-form">
          <div class="form-group">
            <label class="form-label">Base URL <span class="required">*</span></label>
            <el-input
              v-model="form.base_url"
              placeholder="https://api.deepseek.com/v1"
              size="large"
              clearable
            />
            <span class="form-hint">AI 服务的 API 地址</span>
          </div>

          <div class="form-group">
            <label class="form-label">API Key <span class="required">*</span></label>
            <el-input
              v-model="form.api_key"
              type="password"
              show-password
              placeholder="sk-..."
              size="large"
              clearable
            />
            <span class="form-hint">在服务商平台申请的 API 密钥</span>
          </div>

          <div class="form-group">
            <label class="form-label">Model <span class="required">*</span></label>
            <el-input
              v-model="form.model"
              placeholder="deepseek-chat"
              size="large"
              clearable
            />
            <span class="form-hint">要使用的模型名称，如 deepseek-chat / gpt-4o-mini</span>
          </div>

          <div class="form-group">
            <label class="form-label">Temperature</label>
            <el-input
              v-model="form.temperature"
              type="number"
              :min="0"
              :max="2"
              :step="0.1"
              size="large"
            />
            <span class="form-hint"> creativity 创造性程度，0=精确，2=创意，默认 0.3</span>
          </div>
        </div>

<!-- 操作按钮 -->
<div class="form-actions">
<el-button size="large" @click="handleTest" :loading="testing">
 测试连接
</el-button>
<el-button type="primary" size="large" @click="handleSave" :loading="saving">
 保存并进入
</el-button>
</div>

<!-- 免费试用入口 -->
<div class="free-trial">
 <el-divider />
 <p class="trial-hint">没有 API Key？</p>
 <el-button size="small" type="info" plain @click="handleUseFreeTrial" :loading="saving">
 使用内置免费密钥（试用 100 次）
 </el-button>
</div>

        <!-- 测试结果 -->
        <el-alert
          v-if="testResult"
          :title="testResult.msg"
          :type="testResult.ok ? 'success' : 'error'"
          :closable="false"
          style="margin-top: 16px"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const emit = defineEmits(['configured'])

const testing = ref(false)
const saving = ref(false)
const testResult = ref(null)

const form = reactive({
  base_url: '',
  api_key: '',
  model: '',
  temperature: 0.3,
})

// 启动时如果已有配置，自动填入
onMounted(async () => {
  try {
    const r = await api.get('/ai/config')
    if (r.data) {
      form.base_url = r.data.base_url || ''
      form.api_key = ''
      form.model = r.data.model || ''
      form.temperature = r.data.temperature ?? 0.3
    }
  } catch {}
})

async function handleTest() {
  if (!form.base_url || !form.api_key || !form.model) {
    ElMessage.warning('请填写 Base URL、API Key 和 Model')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    await api.post('/ai/switch', {
      provider: 'custom',
      base_url: form.base_url,
      api_key: form.api_key,
      model: form.model,
      temperature: form.temperature,
    })
    const t = await api.post('/ai/test')
    testResult.value = t
  } catch (e) {
    testResult.value = { ok: false, msg: '测试失败: ' + (e.response?.data?.detail || e.message || 'Network Error') }
  } finally {
    testing.value = false
  }
}

async function handleSave() {
 if (!form.base_url || !form.api_key || !form.model) {
 ElMessage.warning('请填写 Base URL、API Key 和 Model')
 return
 }
 saving.value = true
 try {
 await api.post('/ai/switch', {
 provider: 'custom',
 base_url: form.base_url,
 api_key: form.api_key,
 model: form.model,
 temperature: form.temperature,
 })
 ElMessage.success('配置已保存')
 setTimeout(() => emit('configured'), 800)
 } catch (e) {
 ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message || 'Network Error'))
 } finally {
 saving.value = false
 }
}

async function handleUseFreeTrial() {
 saving.value = true
 try {
 // 使用内置免费试用密钥（空配置让后端 fallback 到硬编码 trial key）
 await api.post('/ai/switch', {
 provider: 'custom',
 base_url: '',
 api_key: '',
 model: '',
 temperature: 0.3,
 })
 ElMessage.success('已启用内置免费密钥，开始使用吧！')
 setTimeout(() => emit('configured'), 800)
 } catch (e) {
 // 即使保存失败也放行（后端有 fallback 逻辑）
 ElMessage.warning('已跳过配置，使用内置默认服务')
 setTimeout(() => emit('configured'), 800)
 } finally {
 saving.value = false
 }
}
</script>

<style scoped>
.ai-setup-wizard {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.wizard-overlay {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0f1724 0%, #1e3a5f 60%, #1e40af 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.wizard-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 480px;
  max-width: 92vw;
  padding: 36px;
  animation: slideUp 0.4s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.wizard-header {
  text-align: center;
  margin-bottom: 28px;
}

.wizard-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 6px;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}

.wizard-header h1 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
  font-weight: 700;
}

.wizard-subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin: 6px 0 0;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.required {
  color: #ef4444;
}

.form-hint {
  font-size: 12px;
  color: #94a3b8;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.form-actions .el-button {
 min-width: 120px;
}

.free-trial {
 text-align: center;
 margin-top: 8px;
}
.trial-hint {
 font-size: 13px;
 color: #94a3b8;
 margin: 0 0 8px;
}
</style>