<template>
  <div class="chat-page">
    <div class="chat-header">
      <div>
        <span class="title">AI 助手</span>
        <el-tag size="small" type="success" v-if="ready" effect="plain">LobeChat 已就绪</el-tag>
        <el-tag size="small" type="warning" v-else effect="plain">正在加载 LobeChat ...</el-tag>
      </div>
      <div>
        <el-tooltip content="LobeChat 在新窗口打开">
          <el-button size="small" @click="openInNew">↗ 新窗口</el-button>
        </el-tooltip>
        <el-tooltip content="刷新 iframe">
        <el-button size="small" @click="reload">⟳ 刷新</el-button>
        </el-tooltip>
        <el-tooltip content="LobeChat 的模型/Key 在它自己的设置页填">
          <el-button size="small" type="primary" link>使用说明</el-button>
        </el-tooltip>
      </div>
    </div>
    <div class="chat-frame-wrap" v-loading="!ready">
      <iframe
        ref="frame"
        :src="lobeUrl"
        class="chat-frame"
        allow="clipboard-read; clipboard-write"
        @load="onLoad"
      />
    </div>

    <!-- 兜底:如果 LobeChat 未启动,给出指引 -->
    <el-dialog v-model="showHelp" title="AI 助手未就绪 - 启动指引" width="600">
      <el-alert type="warning" :closable="false" show-icon
        title="检测到 LobeChat 服务未启动"
        description="造价通的 AI 聊天 UI 采用开源项目 LobeChat 嵌入。请按下列步骤启动,或让运维同学部署一份共享实例。"/>
      <pre class="help-pre">
# 方式 1: Docker 一键启动(推荐)
docker run -d --name lobechat \
  -p 3210:3210 \
  -e OPENAI_API_KEY=sk-your-key \
  -e OPENAI_PROXY_URL=https://api.deepseek.com/v1 \
  -e DEFAULT_AGENT_CONFIG=deepseek \
  lobehub/lobe-chat

# 方式 2: Node 自部署
git clone https://github.com/lobehub/lobe-chat
cd lobe-chat
pnpm install
pnpm dev   # 监听 localhost:3010

# 方式 3: 直接用官方 SaaS
# 访问 https://chat-preview.lobehub.com 在线版,无需部署
</pre>
      <div style="margin-top:12px;color:#606266">
        LobeChat 启动后,在它的"设置 → 语言模型"里填入 base_url 和 api_key,
        即可在造价通内嵌聊天框里使用所有 OpenAI 兼容 API (DeepSeek / 通义 / 智谱 / KIMI / OpenAI)。
      </div>
      <template #footer>
        <el-button @click="showHelp = false">关闭</el-button>
        <el-button type="primary" @click="reload">重试连接</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// LobeChat 地址(优先读后端 config 里的 ai.lobechat_url,否则默认 http://localhost:3210)
const defaultUrl = 'http://localhost:3210'
const lobeUrl = ref(defaultUrl)
const ready = ref(false)
const showHelp = ref(false)
const frame = ref(null)

async function loadLobeUrl() {
  try {
    const r = await axios.get('/api/v1/ai/config')
    // 后端允许在 config.yaml 配 ai.lobechat_url
    if (r.data.lobechat_url) lobeUrl.value = r.data.lobechat_url
  } catch {}
  // 健康探测
  try {
    await fetch(lobeUrl.value, { mode: 'no-cors' })
    ready.value = true
  } catch {
    showHelp.value = true
  }
}

function onLoad() {
  ready.value = true
}

function reload() {
  ready.value = false
  showHelp.value = false
  if (frame.value) frame.value.src = lobeUrl.value
}

function openInNew() {
  window.open(lobeUrl.value, '_blank')
}

onMounted(loadLobeUrl)
</script>

<style scoped>
.chat-page { display:flex; flex-direction:column; height: 80vh; background:#fff; padding:8px; border-radius:4px; }
.chat-header { display:flex; justify-content:space-between; align-items:center; padding: 4px 8px 8px; border-bottom:1px solid #ebeef5; }
.chat-header .title { font-size:14px; font-weight:bold; margin-right:8px; }
.chat-frame-wrap { flex:1; position:relative; margin-top:8px; border:1px solid #ebeef5; border-radius:4px; overflow:hidden; }
.chat-frame { width:100%; height:100%; border:0; display:block; }
.help-pre { background:#f4f4f5; padding:12px; border-radius:4px; font-size:11px; line-height:1.5; overflow:auto; }
</style>
