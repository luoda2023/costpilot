<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <div class="session-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">会话</span>
        <el-button size="small" type="primary" @click="newSession" :icon="Plus">新建</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentId }"
          @click="switchSession(s.id)"
        >
          <el-icon :size="14"><ChatDotRound /></el-icon>
          <span class="session-title">{{ s.title || '新会话' }}</span>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="50" />
      </div>
    </div>

    <!-- 右侧聊天区 -->
    <div class="chat-main">
      <div class="message-list" ref="msgListRef">
        <!-- 欢迎页 -->
        <div v-if="!currentId" class="welcome">
          <div class="welcome-icon">
            <el-icon :size="56" color="#409eff"><ChatLineSquare /></el-icon>
          </div>
          <h3>造价通 AI 助手</h3>
          <p class="welcome-desc">查询价格、费率、模板，生成报价和文本</p>
          <div class="welcome-suggestions">
            <div class="suggestion-item" @click="quickAsk('查一下C30混凝土的综合单价')">C30混凝土综合单价</div>
            <div class="suggestion-item" @click="quickAsk('查一下钢质防火门的综合单价')">钢质防火门综合单价</div>
            <div class="suggestion-item" @click="quickAsk('上海地区安全文明施工费费率')">上海安全文明施工费</div>
            <div class="suggestion-item" @click="quickAsk('帮我估算一个10000㎡住宅楼的造价')">10000㎡住宅楼估算</div>
          </div>
          <el-button type="primary" @click="newSession" size="large">开始新对话</el-button>
        </div>

        <template v-else>
          <div v-if="loading" class="loading-wrap">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          </div>

          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="message-row"
            :class="msg.role === 'user' ? 'user-row' : 'assistant-row'"
          >
            <div class="avatar" :class="msg.role">
              <el-icon v-if="msg.role === 'user'" :size="16"><UserFilled /></el-icon>
              <el-icon v-else :size="16" color="#409eff"><Monitor /></el-icon>
            </div>
            <div class="bubble" :class="msg.role">
              <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入框 -->
      <div class="input-area" v-if="currentId">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入问题，Ctrl+Enter 发送"
            :disabled="sending"
            @keydown.enter.ctrl="send"
          />
          <el-button type="primary" :loading="sending" @click="send" circle :icon="Promotion" class="send-btn" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ChatAPI } from '@/api'
import { Plus, ChatDotRound, ChatLineSquare, UserFilled, Monitor, Loading, Promotion } from '@element-plus/icons-vue'

const sessions = ref([])
const currentId = ref(null)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const sending = ref(false)
const msgListRef = ref(null)

function renderMarkdown(text) {
  if (!text) return ''
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/### (.+)/g, '<h4>$1</h4>')
  html = html.replace(/## (.+)/g, '<h3>$1</h3>')
  html = html.replace(/^---+/gm, '<hr>')
  html = html.replace(/\n/g, '<br>')
  html = html.replace(/\|(.+?)\|/g, (m) => {
    const cells = m.split('|').filter(c => c.trim())
    if (cells.length <= 1) return m
    return `<span class="inline-table">${cells.map(c => `<span class="inline-cell">${c.trim()}</span>`).join('')}</span>`
  })
  return html
}

async function loadSessions() {
  try { sessions.value = await ChatAPI.listSessions() } catch {}
}

async function newSession() {
  try {
    const s = await ChatAPI.createSession()
    sessions.value.unshift(s)
    currentId.value = s.id
    messages.value = []
  } catch {}
}

async function quickAsk(text) {
  if (!currentId.value) await newSession()
  if (currentId.value) {
    inputText.value = text
    await send()
  }
}

async function switchSession(id) {
  currentId.value = id
  loading.value = true
  try {
    messages.value = await ChatAPI.messages(id)
    await nextTick()
    scrollToBottom()
  } finally { loading.value = false }
}

async function send() {
  const text = inputText.value.trim()
  if (!text || !currentId.value || sending.value) return
  inputText.value = ''
  sending.value = true
  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'assistant', content: '...', _loading: true })
  await nextTick(); scrollToBottom()
  try {
    const result = await ChatAPI.send(currentId.value, text)
    messages.value[messages.value.length - 1] = result
  } catch (e) {
    messages.value[messages.value.length - 1] = { role: 'assistant', content: `[发送失败] ${e.message || '请检查网络或 AI 配置'}` }
  } finally {
    sending.value = false
    await nextTick(); scrollToBottom()
  }
}

function scrollToBottom() {
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}

watch(currentId, () => { nextTick(scrollToBottom) })
onMounted(loadSessions)
</script>

<style scoped>
.chat-page {
  display: flex; height: calc(100vh - 120px); background: #fff; border-radius: 8px; overflow: hidden;
}

/* 左侧 */
.session-sidebar {
  width: 200px; min-width: 200px; border-right: 1px solid #ebeef5; display: flex; flex-direction: column; background: #fafafa;
}
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #ebeef5;
}
.sidebar-title { font-weight: 600; font-size: 14px; }
.session-list { flex: 1; overflow-y: auto; padding: 6px; }
.session-item {
  display: flex; align-items: center; gap: 6px; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-size: 13px; margin-bottom: 2px; transition: all 0.15s;
}
.session-item:hover { background: #e8f4ff; }
.session-item.active { background: #d9ecff; color: #409eff; }
.session-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 聊天主区 */
.chat-main { flex: 1; display: flex; flex-direction: column; }
.message-list { flex: 1; overflow-y: auto; padding: 20px; }

/* 欢迎页 */
.welcome { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #909399; }
.welcome h3 { margin: 12px 0 6px; color: #303133; font-size: 18px; line-height:1.4; }
.welcome-desc { color: #909399; margin-bottom: 16px; font-size:14px; }
.welcome-suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-bottom: 16px; }
.suggestion-item {
padding: 8px 16px; background: #f0f5ff; border: 1px solid #d9ecff; border-radius: 20px; color: #409eff; cursor: pointer; font-size: 14px; transition: all 0.2s; line-height:1.5;
}
.suggestion-item:hover { background: #409eff; color: #fff; }

/* 消息 */
.loading-wrap { text-align: center; padding: 40px; }
.message-row { display: flex; gap: 10px; margin-bottom: 18px; }
.user-row { flex-direction: row-reverse; }
.avatar {
  width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.avatar.user { background: #409eff; color: #fff; }
.avatar.assistant { background: #f0f2f5; }
.bubble {
  max-width: 72%; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.6;
}
.bubble.user { background: #409eff; color: #fff; border-bottom-right-radius: 2px; }
.bubble.assistant { background: #f0f2f5; color: #303133; border-bottom-left-radius: 2px; }
.bubble.assistant :deep(pre) { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
.bubble.assistant :deep(code) { background: #e8e8e8; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.bubble.assistant :deep(pre code) { background: transparent; padding: 0; }
.bubble.assistant :deep(h3) { font-size: 16px; margin: 8px 0 4px; }
.bubble.assistant :deep(h4) { font-size: 14px; margin: 6px 0 4px; }
.msg-content { word-break: break-word; }

/* 输入区 */
.input-area { border-top: 1px solid #ebeef5; padding: 12px 16px; }
.input-wrapper { display: flex; gap: 10px; align-items: flex-end; }
.input-wrapper :deep(.el-textarea__inner) { border-radius: 8px; }
.send-btn { margin-bottom: 0; flex-shrink: 0; }
</style>