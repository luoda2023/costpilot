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
          <el-icon :size="14"><Message /></el-icon>
          <span class="session-title">{{ s.title || '新会话' }}</span>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧聊天区 -->
    <div class="chat-main">
      <!-- 消息列表 -->
      <div class="message-list" ref="msgListRef">
        <div v-if="!currentId" class="welcome">
          <el-icon :size="48" color="#409eff"><ChatLineSquare /></el-icon>
          <h3>造价通 AI 助手</h3>
          <p>可以问我：查询价格、费率、模板，或生成报价、文本</p>
          <el-button type="primary" @click="newSession">开始新对话</el-button>
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
            <div class="avatar">
              <el-icon v-if="msg.role === 'user'" :size="18"><UserFilled /></el-icon>
              <el-icon v-else :size="18" color="#409eff"><Monitor /></el-icon>
            </div>
            <div class="bubble" :class="msg.role">
              <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入框 -->
      <div class="input-area" v-if="currentId">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入问题，例如：查一下钢质防火门的综合单价"
          :disabled="sending"
          @keydown.enter.ctrl="send"
        />
        <div class="input-actions">
          <span class="hint">Ctrl+Enter 发送</span>
          <el-button type="primary" :loading="sending" @click="send" :icon="Promotion">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ChatAPI } from '@/api'
import {
  Plus, Message, ChatLineSquare, UserFilled,
  Monitor, Loading, Promotion,
} from '@element-plus/icons-vue'

const sessions = ref([])
const currentId = ref(null)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const sending = ref(false)
const msgListRef = ref(null)

// 简易 Markdown 渲染（只处理基本格式，后续可换 marked）
function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 代码块
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  // 加粗
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 换行
  html = html.replace(/\n/g, '<br>')
  return html
}

async function loadSessions() {
  try {
    sessions.value = await ChatAPI.listSessions()
  } catch (e) {
    console.error('加载会话失败', e)
  }
}

async function newSession() {
  try {
    const s = await ChatAPI.createSession()
    sessions.value.unshift(s)
    currentId.value = s.id
    messages.value = []
  } catch (e) {
    console.error('创建会话失败', e)
  }
}

async function switchSession(id) {
  currentId.value = id
  loading.value = true
  try {
    messages.value = await ChatAPI.messages(id)
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('加载消息失败', e)
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = inputText.value.trim()
  if (!text || !currentId.value || sending.value) return

  inputText.value = ''
  sending.value = true

  // 立即显示用户消息
  messages.value.push({ role: 'user', content: text })
  // 占位 AI 回复
  messages.value.push({ role: 'assistant', content: '...', _loading: true })
  await nextTick()
  scrollToBottom()

  try {
    const result = await ChatAPI.send(currentId.value, text)
    // 替换占位
    messages.value[messages.value.length - 1] = result
  } catch (e) {
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: `[发送失败] ${e.message || '请检查网络或 AI 配置'}`,
    }
  } finally {
    sending.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (msgListRef.value) {
    msgListRef.value.scrollTop = msgListRef.value.scrollHeight
  }
}

watch(currentId, () => {
  // 切换会话时滚动到底部
  nextTick(scrollToBottom)
})

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 120px);
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
}

/* 左侧会话列表 */
.session-sidebar {
  width: 220px;
  min-width: 220px;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
}
.sidebar-title {
  font-weight: bold;
  font-size: 14px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}
.session-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  margin-bottom: 2px;
}
.session-item:hover {
  background: #e8f4ff;
}
.session-item.active {
  background: #d9ecff;
  color: #409eff;
}
.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧聊天主区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}
.welcome h3 {
  margin: 12px 0 8px;
  color: #303133;
}
.loading-wrap {
  text-align: center;
  padding: 40px;
}

.message-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.user-row {
  flex-direction: row-reverse;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}
.bubble.user {
  background: #409eff;
  color: #fff;
}
.bubble.assistant {
  background: #f0f2f5;
  color: #303133;
}
.bubble.assistant :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
.bubble.assistant :deep(code) {
  background: #e8e8e8;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}
.bubble.assistant :deep(pre code) {
  background: transparent;
  padding: 0;
}
.msg-content {
  word-break: break-word;
}

/* 输入区 */
.input-area {
  border-top: 1px solid #ebeef5;
  padding: 12px 16px;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.hint {
  color: #c0c4cc;
  font-size: 12px;
}
</style>