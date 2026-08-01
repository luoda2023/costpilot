<template>
<div class="ai-setup-wizard">
<div class="wizard-overlay">
<div class="wizard-card">
<div class="wizard-header">
<div class="wizard-logo">
<div class="logo-icon">⚡</div>
<div>
<h1>AI 服务已就绪</h1>
<p class="wizard-subtitle">内置免费密钥，开箱即用</p>
</div>
</div>
</div>

<div class="wizard-body">
<el-alert
title="默认配置已启用内置免费试用密钥"
type="success"
:closable="false"
show-icon
style="margin-bottom: 16px"
/>

<div class="default-info">
<div class="info-row">
<span class="info-label">Model</span>
<span class="info-value">{{ config.model || 'hermesAPI' }}</span>
</div>
<div class="info-row">
<span class="info-label">剩余次数</span>
<span class="info-value" :class="remainingClass">
{{ usage?.text_remaining ?? 100 }}/{{ usage?.max_free_calls ?? 100 }} 次
</span>
</div>
</div>

<p class="trial-note">
免费试用 100 次，用完可在「系统设置」中添加自己的 API Key
</p>
</div>

<div class="form-actions">
<el-button size="large" @click="handleOpenSettings">
⚙ 系统设置
</el-button>
<el-button type="primary" size="large" @click="handleStart">
🚀 开始使用
</el-button>
</div>
</div>
</div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api, UsageAPI } from '@/api'

const emit = defineEmits(['configured'])

const config = ref({})
const usage = ref(null)

const remainingClass = computed(() => {
if (!usage.value) return ''
const r = usage.value.text_remaining
if (r > 30) return 'text-success'
if (r > 0) return 'text-warning'
return 'text-danger'
})

onMounted(async () => {
try {
config.value = await api.get('/ai/config')
usage.value = await UsageAPI.get()
} catch { /* 忽略 */ }
})

function handleStart() {
emit('configured')
}

function handleOpenSettings() {
emit('configured')
// 跳转到设置页面
setTimeout(() => {
window.location.hash = '#/settings'
}, 100)
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
margin-bottom: 24px;
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
background: linear-gradient(135deg, #10b981, #34d399);
border-radius: 12px;
display: flex;
align-items: center;
justify-content: center;
font-size: 22px;
color: #fff;
box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
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

.wizard-body {
margin-bottom: 24px;
}

.default-info {
background: #f8fafc;
border: 1px solid #e2e8f0;
border-radius: 8px;
padding: 16px;
margin-bottom: 12px;
}

.info-row {
display: flex;
justify-content: space-between;
align-items: center;
padding: 6px 0;
font-size: 14px;
}

.info-label {
color: #64748b;
font-weight: 500;
}

.info-value {
color: #0f172a;
font-weight: 600;
}

.text-success { color: #10b981; }
.text-warning { color: #f59e0b; }
.text-danger { color: #ef4444; }

.trial-note {
font-size: 13px;
color: #94a3b8;
text-align: center;
margin: 0;
}

.form-actions {
display: flex;
gap: 12px;
justify-content: center;
}

.form-actions .el-button {
min-width: 140px;
}
</style>