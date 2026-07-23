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
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// 初始化 markdown-it 渲染器（html: false 防止 XSS）
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="code-block"><code class="hljs language-${lang}">${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch {}
    }
    // 无语言识别，自动检测
    try {
      const result = hljs.highlightAuto(str)
      return `<pre class="code-block"><code class="hljs">${result.value}</code></pre>`
    } catch {}
    return `<pre class="code-block"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 自定义引用样式
md.renderer.rules.blockquote_open = () => '<blockquote class="md-quote">\n'
md.renderer.rules.table_open = () => '<div class="md-table-wrap"><table class="md-table">\n'
md.renderer.rules.table_close = () => '</table></div>\n'

const sessions = ref([])
const currentId = ref(null)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const sending = ref(false)
const msgListRef = ref(null)

function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
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
  if (!currentId.value) {
    try { await newSession() } catch { ElMessage.error('创建会话失败'); return }
  }
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
  max-width: 76%; padding: 12px 16px; border-radius: 8px; font-size: 14px; line-height: 1.6;
}
.bubble.user { background: #409eff; color: #fff; border-bottom-right-radius: 2px; }
.bubble.assistant { background: #f0f2f5; color: #303133; border-bottom-left-radius: 2px; }
.msg-content { word-break: break-word; }

/* 消息内容中的 Markdown 样式 */
.msg-content :deep(p) { margin: 0 0 8px 0; }
.msg-content :deep(p:last-child) { margin-bottom: 0; }
.msg-content :deep(h1),
.msg-content :deep(h2),
.msg-content :deep(h3),
.msg-content :deep(h4) { margin: 12px 0 6px; color: #1a2332; font-weight: 600; }
.msg-content :deep(h1) { font-size: 18px; }
.msg-content :deep(h2) { font-size: 16px; }
.msg-content :deep(h3) { font-size: 15px; }
.msg-content :deep(h4) { font-size: 14px; }
.msg-content :deep(strong) { font-weight: 600; color: #1a2332; }
.msg-content :deep(em) { font-style: italic; }
.msg-content :deep(a) { color: #409eff; text-decoration: none; }
.msg-content :deep(a:hover) { text-decoration: underline; }
.msg-content :deep(ul),
.msg-content :deep(ol) { margin: 4px 0 8px; padding-left: 20px; }
.msg-content :deep(li) { margin-bottom: 2px; }
.msg-content :deep(hr) { border: none; border-top: 1px solid #e0e0e0; margin: 12px 0; }
.msg-content :deep(blockquote) {
  border-left: 3px solid #409eff; margin: 8px 0; padding: 6px 12px; background: rgba(64,158,255,0.05); border-radius: 0 4px 4px 0;
}
.msg-content :deep(blockquote p) { margin: 0; }

/* 表格 */
.msg-content :deep(.md-table-wrap) { overflow-x: auto; margin: 8px 0; }
.msg-content :deep(.md-table) {
  border-collapse: collapse; width: 100%; font-size: 13px; border: 1px solid #e0e0e0;
}
.msg-content :deep(.md-table th) {
  background: #f5f7fa; padding: 6px 10px; border: 1px solid #e0e0e0; text-align: left; font-weight: 600; white-space: nowrap;
}
.msg-content :deep(.md-table td) {
  padding: 6px 10px; border: 1px solid #e0e0e0;
}
.msg-content :deep(.md-table tr:nth-child(even)) { background: #fafafa; }
.msg-content :deep(.md-table tr:hover) { background: #f0f5ff; }

/* 代码 */
.msg-content :deep(code) {
  background: #e8e8e8; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-family: 'Consolas','Courier New',monospace;
}
.msg-content :deep(pre.code-block) {
  background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; overflow-x: auto; margin: 8px 0; font-size: 12px; line-height: 1.5;
}
.msg-content :deep(pre.code-block code) {
  background: transparent; padding: 0; color: inherit; font-size: inherit;
}
.msg-content :deep(pre.code-block .hljs) { background: transparent; }
.msg-content :deep(img) {
  max-width: 100%; border-radius: 4px; margin: 8px 0;
}

/* 输入区 */
.input-area { border-top: 1px solid #ebeef5; padding: 8px 16px 0; }
.input-wrapper { display: flex; gap: 10px; }
.input-wrapper :deep(.el-textarea__inner) { border-radius: 8px; }
.send-btn { flex-shrink: 0; }
</style>