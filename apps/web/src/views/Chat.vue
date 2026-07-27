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
  <el-button size="small" type="danger" link @click.stop="deleteSession(s.id)" :icon="Delete" style="margin-left:auto;padding:0" />
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
          <h3>工程助手 AI 助手</h3>
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
    <div v-if="msg._loading" class="typing-indicator">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </div>
    <div v-else class="msg-content" v-html="renderMarkdown(msg.content)"></div>
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
 v-auto-halfwidth
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatAPI } from '@/api'
import { Plus, ChatDotRound, ChatLineSquare, UserFilled, Monitor, Loading, Promotion, Delete } from '@element-plus/icons-vue'
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
  } catch (e) {
    ElMessage.error('创建会话失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  }
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

async function deleteSession(id) {
  try {
    await ElMessageBox.confirm('确定删除此会话?', '提示', { type: 'warning' })
    await ChatAPI.deleteSession(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentId.value === id) { currentId.value = null; messages.value = [] }
    ElMessage.success('已删除')
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
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
    const errMsg = e.response?.data?.detail || e.message || '请检查网络或 AI 配置'
    messages.value[messages.value.length - 1] = {
      role: 'assistant',
      content: `**发送失败**：${errMsg}\n\n> 提示：请检查「系统设置」中的 AI 配置是否正确，或确认后端服务是否正常运行。`
    }
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
  display: flex;
  height: calc(100vh - var(--topbar-height) - var(--space-6));
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
  overflow: hidden;
}

/* 左侧会话栏 */
.session-sidebar {
  width: 220px;
  min-width: 220px;
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  background: var(--gray-50);
}

.session-sidebar .sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--gray-200);
}

.sidebar-title {
  font-weight: 700;
  font-size: var(--text-md);
  color: var(--text-primary);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  margin-bottom: 2px;
  transition: all var(--transition-fast);
  color: var(--text-secondary);
}

.session-item:hover {
  background: var(--gray-100);
  color: var(--text-primary);
}

.session-item.active {
  background: #eff6ff;
  color: var(--brand-600);
  font-weight: 600;
}

.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 聊天主区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

/* 欢迎页 */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--space-10);
}

.welcome-icon {
  margin-bottom: var(--space-4);
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}

.welcome h3 {
  margin: 0 0 var(--space-2) 0;
  color: var(--text-primary);
  font-size: var(--text-xl);
  font-weight: 700;
}

.welcome-desc {
  color: var(--text-tertiary);
  margin-bottom: var(--space-6);
  font-size: var(--text-md);
}

.welcome-suggestions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  justify-content: center;
  margin-bottom: var(--space-6);
  max-width: 560px;
}

.suggestion-item {
  padding: var(--space-2) var(--space-4);
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: var(--radius-full);
  color: var(--brand-600);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
  font-weight: 500;
}

.suggestion-item:hover {
  background: var(--brand-500);
  color: #fff;
  border-color: var(--brand-500);
  box-shadow: var(--shadow-brand);
}

/* 消息 */
.loading-wrap {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-tertiary);
}

.message-row {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  animation: msgIn 0.3s ease;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-row {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}

.avatar.user {
  background: linear-gradient(135deg, var(--brand-500), var(--brand-400));
  color: #fff;
  box-shadow: var(--shadow-brand);
}

.avatar.assistant {
  background: var(--gray-200);
  color: var(--text-secondary);
}

.bubble {
  max-width: 76%;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  line-height: 1.7;
}

.bubble.user {
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500));
  color: #fff;
  border-bottom-right-radius: var(--radius-xs);
  box-shadow: var(--shadow-brand);
}

.bubble.assistant {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--gray-200);
  border-bottom-left-radius: var(--radius-xs);
  box-shadow: var(--shadow-xs);
}

.msg-content {
  word-break: break-word;
}

/* 打字动画 */
.typing-indicator {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gray-400);
  animation: typingBounce 1.4s infinite ease-in-out both;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* Markdown 渲染样式 */
.msg-content :deep(p) { margin: 0 0 8px 0; }
.msg-content :deep(p:last-child) { margin-bottom: 0; }
.msg-content :deep(h1),
.msg-content :deep(h2),
.msg-content :deep(h3),
.msg-content :deep(h4) {
  margin: 12px 0 6px;
  color: var(--text-primary);
  font-weight: 700;
}
.msg-content :deep(h1) { font-size: var(--text-xl); }
.msg-content :deep(h2) { font-size: var(--text-lg); border-bottom: 1px solid var(--gray-200); padding-bottom: 4px; }
.msg-content :deep(h3) { font-size: var(--text-md); }
.msg-content :deep(strong) { font-weight: 700; color: var(--text-primary); }
.msg-content :deep(em) { font-style: italic; color: var(--text-secondary); }
.msg-content :deep(a) { color: var(--brand-500); text-decoration: none; }
.msg-content :deep(a:hover) { text-decoration: underline; }
.msg-content :deep(ul),
.msg-content :deep(ol) { margin: 4px 0 8px; padding-left: 20px; }
.msg-content :deep(li) { margin-bottom: 3px; }
.msg-content :deep(hr) { border: none; border-top: 1px solid var(--gray-200); margin: 12px 0; }
.msg-content :deep(blockquote) {
  border-left: 3px solid var(--brand-500);
  margin: 8px 0;
  padding: var(--space-2) var(--space-3);
  background: #eff6ff;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.msg-content :deep(blockquote p) { margin: 0; }

/* Markdown 表格 */
.msg-content :deep(.md-table-wrap) { overflow-x: auto; margin: 8px 0; border-radius: var(--radius-sm); }
.msg-content :deep(.md-table) {
  border-collapse: collapse;
  width: 100%;
  font-size: var(--text-sm);
  border: 1px solid var(--gray-200);
}
.msg-content :deep(.md-table th) {
  background: var(--gray-100);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--gray-200);
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  color: var(--text-primary);
}
.msg-content :deep(.md-table td) {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--gray-200);
}
.msg-content :deep(.md-table tr:nth-child(even)) { background: var(--gray-50); }
.msg-content :deep(.md-table tr:hover) { background: #f0f5ff; }

/* 代码块 */
.msg-content :deep(code) {
  background: var(--gray-100);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-family: 'Consolas', 'Courier New', monospace;
  color: #d63384;
}
.msg-content :deep(pre.code-block) {
  background: #1e293b;
  color: #e2e8f0;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-3) 0;
  font-size: var(--text-xs);
  line-height: 1.6;
}
.msg-content :deep(pre.code-block code) {
  background: transparent;
  padding: 0;
  color: inherit;
  font-size: inherit;
}
.msg-content :deep(pre.code-block .hljs) { background: transparent; }
.msg-content :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin: var(--space-3) 0;
}

/* 输入区 */
.input-area {
  border-top: 1px solid var(--gray-200);
  padding: var(--space-3) var(--space-4) var(--space-4);
  background: var(--bg-surface);
}

.input-wrapper {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--gray-300) !important;
  background: var(--gray-50) !important;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  transition: all var(--transition-fast);
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: var(--brand-500) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
  background: #fff !important;
}

.send-btn {
  flex-shrink: 0;
  background: var(--brand-500) !important;
  border-color: var(--brand-500) !important;
  box-shadow: var(--shadow-brand);
}
</style>