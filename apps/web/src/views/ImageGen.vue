<template>
  <div class="imagegen-page">
    <el-row :gutter="16">
      <!-- 左侧：模式切换 -->
      <el-col :span="5">
        <el-card shadow="never" class="side-card">
          <template #header><span class="card-title">生成模式</span></template>
          <el-menu :default-active="mode" @select="onModeChange" class="mode-menu">
            <el-menu-item index="text-to-image">
              <el-icon><EditPen /></el-icon>
              <span>文生图</span>
            </el-menu-item>
            <el-menu-item index="image-to-image">
              <el-icon><PictureFilled /></el-icon>
              <span>图生图</span>
            </el-menu-item>
          </el-menu>
        </el-card>
        <el-card shadow="never" class="side-card" style="margin-top:12px">
          <template #header><span class="card-title">生成记录</span></template>
          <div class="history-list" v-if="history.length > 0">
            <div v-for="(item, i) in history" :key="i" class="history-item" @click="scrollToResult(item.id)">
              <el-image :src="item.url" fit="cover" class="history-thumb" />
              <div class="history-info">
                <span class="history-mode">{{ item.mode === 'text-to-image' ? '文生图' : '图生图' }}</span>
                <span class="history-time">{{ item.time }}</span>
              </div>
            </div>
          </div>
          <div v-else class="placeholder">
            <el-empty description="暂无记录" :image-size="40" />
          </div>
        </el-card>
      </el-col>

      <!-- 中间：生成区域 -->
      <el-col :span="14">
        <el-card shadow="never" class="main-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ mode === 'text-to-image' ? '文生图' : '图生图' }}</span>
              <div class="header-actions">
                <el-select v-model="imageSize" size="small" style="width:140px;margin-right:8px">
                  <el-option label="1024×1024" value="1024x1024" />
                  <el-option label="1024×1792" value="1024x1792" />
                  <el-option label="1792×1024" value="1792x1024" />
                </el-select>
                <el-tooltip content="切换模式时自动清空参考图片" placement="top">
                  <el-icon color="#909399" style="cursor:help"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </div>
          </template>

          <!-- 图生图：上传区域 -->
          <div v-if="mode === 'image-to-image'" class="upload-area">
            <el-upload
              ref="uploadRef"
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept="image/jpeg,image/png,image/webp,image/gif"
              :on-change="onFileChange"
              class="image-upload"
            >
              <template #default>
                <div v-if="!referenceImage" class="upload-placeholder">
                  <el-icon :size="40" color="#c0c4cc"><Plus /></el-icon>
                  <p class="upload-text">拖拽或点击上传参考图片</p>
                  <p class="upload-hint">支持 JPG/PNG/WebP/GIF，最大5MB</p>
                </div>
                <div v-else class="upload-preview">
                  <el-image :src="referenceImage" fit="contain" class="preview-img" />
                  <div class="upload-actions">
                    <el-button size="small" type="danger" plain @click.stop="removeFile">重新选择</el-button>
                  </div>
                </div>
              </template>
            </el-upload>
          </div>

          <!-- 提示词输入 -->
          <div class="prompt-area">
            <el-input
              v-model="prompt"
              type="textarea"
              :rows="3"
              placeholder="请输入图片描述提示词，如：湘西州供水管网改造施工示意图，管道铺设，市政工程，简洁风格"
              maxlength="1000"
              show-word-limit
              resize="none"
            />
          </div>

          <!-- 生成按钮 -->
          <div class="action-bar">
            <el-button type="primary" :loading="generating" :disabled="!canGenerate" @click="generateImage" size="large">
              <el-icon v-if="!generating"><MagicStick /></el-icon>
              {{ generating ? '生成中...' : '生成图片' }}
            </el-button>
            <el-button v-if="results.length > 0" @click="clearResults" size="default" :disabled="generating">
              清空结果
            </el-button>
            <span v-if="generating" class="generating-hint">预计耗时 20~60秒</span>
          </div>

          <!-- 生成进度 -->
          <div v-if="generating" class="progress-bar">
            <el-progress :percentage="progress" :stroke-width="4" :status="progress === 100 ? 'success' : undefined" />
            <p class="progress-text">AI 正在生成图片，请稍候...</p>
          </div>
        </el-card>

        <!-- 结果画廊 -->
        <el-card v-if="results.length > 0" shadow="never" class="result-card" style="margin-top:12px">
          <template #header>
            <span class="card-title">生成结果 ({{ results.length }})</span>
          </template>
          <div class="image-grid">
            <div v-for="(item, i) in results" :key="item.id" class="image-grid-item">
              <el-image
                :src="item.url"
                fit="contain"
                class="grid-image"
                :preview-src-list="previewList"
                :initial-index="i"
                hide-on-click-modal
              >
                <template #error>
                  <div class="image-error">
                    <el-icon :size="24"><WarningFilled /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
                <template #placeholder>
                  <div class="image-placeholder">
                    <el-icon :size="24" class="is-loading"><Loading /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="image-item-footer">
                <span class="image-mode-tag">{{ item.mode === 'fallback' ? '文生图(回落)' : mode === 'text-to-image' ? '文生图' : '图生图' }}</span>
                <el-button size="small" text type="primary" :loading="item.downloading" @click="downloadImage(item, i)">
                  <el-icon><Download /></el-icon> 下载
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：使用提示 -->
      <el-col :span="5">
        <el-card shadow="never" class="info-card">
          <template #header><span class="card-title">使用提示</span></template>
          <div class="tips">
            <div class="tip-item">
              <el-tag size="small" type="primary" round>1</el-tag>
              <span>选择生成模式</span>
            </div>
            <div class="tip-item">
              <el-tag size="small" type="primary" round>2</el-tag>
              <span>输入描述提示词</span>
            </div>
            <div class="tip-item">
              <el-tag size="small" type="primary" round>3</el-tag>
              <span>点击"生成图片"</span>
            </div>
            <div class="tip-item">
              <el-tag size="small" type="primary" round>4</el-tag>
              <span>点击图片可放大预览</span>
            </div>
          </div>
        </el-card>
        <el-card shadow="never" class="info-card" style="margin-top:12px">
          <template #header><span class="card-title">提示词技巧</span></template>
          <div class="tips-content">
            <p>• 描述具体场景、风格、元素</p>
            <p>• 图生图：上传参考图+优化描述</p>
            <p>• 如：某市政管网施工横断面图，含管沟开挖、砂垫层、管道安装、回填等工序示意，标注清晰，工程制图风格</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, PictureFilled, Plus, MagicStick, Download, WarningFilled, Loading, InfoFilled } from '@element-plus/icons-vue'
import { api } from '@/api'

document.title = '工程助手 - 图片生成'

// ============================================================
// 常量
// ============================================================
const MAX_RESULTS = 20          // 结果列表上限
const MAX_HISTORY = 10          // 历史记录上限
const DOWNLOAD_TIMEOUT = 30000  // 下载超时 (30s)
const STORAGE_KEY = 'img_gen_history'  // localStorage 键

// ============================================================
// 状态
// ============================================================
const mode = ref('text-to-image')
const prompt = ref('')
const imageSize = ref('1024x1024')
const generating = ref(false)
const progress = ref(0)
const results = ref([])         // { id, url, mode, prompt, revised_prompt, downloading }
const history = ref([])         // { id, url, mode, time }
const referenceImage = ref('')  // blob URL (需手动释放)
const referenceFile = ref(null)
const uploadRef = ref(null)
let _idCounter = 0
let _objectUrls = []            // 追踪所有待释放的 blob URL

// 预览列表（缓存，避免每次渲染重建数组）
const previewList = computed(() => results.value.map(r => r.url))

// 是否可以生成
const canGenerate = computed(() => {
  const hasPrompt = prompt.value.trim().length > 0
  if (mode.value === 'text-to-image') return hasPrompt
  return hasPrompt && referenceFile.value !== null
})

// ============================================================
// 模式切换
// ============================================================
function onModeChange(index) {
  mode.value = index
  // 切换到文生图时自动清理参考图片，避免残留
  if (index === 'text-to-image') {
    removeFile()
  }
}

// ============================================================
// 文件上传 & 内存管理
// ============================================================
function onFileChange(uploadFile) {
  const file = uploadFile.raw
  if (!file) return

  // 验证大小
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片文件过大，请控制在5MB以内')
    return
  }

  // 清理旧 blob URL
  removeFile()

  referenceFile.value = file
  referenceImage.value = URL.createObjectURL(file)
  _objectUrls.push(referenceImage.value)
}

function removeFile() {
  if (referenceImage.value) {
    URL.revokeObjectURL(referenceImage.value)
    _objectUrls = _objectUrls.filter(u => u !== referenceImage.value)
  }
  referenceImage.value = ''
  referenceFile.value = null
}

// ============================================================
// 结果管理
// ============================================================
function clearResults() {
  results.value = []
}

function scrollToResult(id) {
  // 找到对应结果卡片，滚动到可视区域
  const el = document.querySelector(`[data-result-id="${id}"]`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

// ============================================================
// AI 图片生成
// ============================================================
async function generateImage() {
  if (!canGenerate.value) return

  generating.value = true
  progress.value = 10

  try {
    let resp

    if (mode.value === 'text-to-image') {
      resp = await api.post('/ai/generate-image', {
        prompt: prompt.value,
        size: imageSize.value,
      })
      progress.value = 80
    } else {
      const formData = new FormData()
      formData.append('image', referenceFile.value)
      formData.append('prompt', prompt.value)
      formData.append('size', imageSize.value)
      resp = await api.post('/ai/image-to-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      progress.value = 80
    }

    if (resp.ok) {
      const url = resp.url || (resp.b64 ? `data:image/png;base64,${resp.b64}` : '')
      if (url) {
        const id = ++_idCounter
        // 添加到结果列表（头部插入）
        results.value.unshift({
          id,
          url,
          mode: resp.mode || mode.value,
          prompt: prompt.value,
          revised_prompt: resp.revised_prompt || '',
          downloading: false,
        })
        // 限制结果列表上限
        if (results.value.length > MAX_RESULTS) {
          results.value = results.value.slice(0, MAX_RESULTS)
        }

        // 添加到历史
        addHistory({ id, url, mode: mode.value, time: new Date().toLocaleTimeString() })

        progress.value = 100
        ElMessage.success('图片生成成功！')
      } else {
        ElMessage.error('图片生成失败：未返回图片URL')
      }
    } else {
      ElMessage.error(resp.msg || '图片生成失败')
    }
  } catch (e) {
    const msg = e?.response?.data?.msg || e.message || '请求失败'
    ElMessage.error('图片生成失败: ' + msg)
  } finally {
    generating.value = false
    setTimeout(() => { progress.value = 0 }, 2000)
  }
}

// ============================================================
// 历史记录（localStorage 持久化）
// ============================================================
function addHistory(item) {
  history.value.unshift(item)
  if (history.value.length > MAX_HISTORY) {
    history.value = history.value.slice(0, MAX_HISTORY)
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
  } catch {
    // localStorage 满了，忽略
  }
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      history.value = JSON.parse(raw).slice(0, MAX_HISTORY)
    }
  } catch {
    // 解析失败，忽略
  }
}

// ============================================================
// 图片下载
// ============================================================
async function downloadImage(item, index) {
  if (item.downloading) return
  item.downloading = true

  try {
    // 带超时的 fetch
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT)
    const resp = await fetch(item.url, { signal: controller.signal })
    clearTimeout(timeoutId)

    const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `AI生成图片_${index + 1}.png`
    a.click()
    // 释放临时 blob URL
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
  } catch {
    // 跨域或失败时降级为新窗口打开
    ElMessage.info('图片已在新窗口打开，请右键另存为')
    window.open(item.url, '_blank')
  } finally {
    item.downloading = false
  }
}

// ============================================================
// 生命周期
// ============================================================
loadHistory()

onUnmounted(() => {
  // 清理所有 blob URL，防止内存泄漏
  _objectUrls.forEach(url => URL.revokeObjectURL(url))
  _objectUrls = []
})
</script>

<style scoped>
.imagegen-page {
  padding: 0;
  height: 100%;
}

.side-card :deep(.el-card__body) {
  padding: 8px;
}

.mode-menu {
  border-right: none;
}

.mode-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.mode-menu .el-menu-item.is-active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  align-items: center;
}

.main-card {
  min-height: 300px;
}

.upload-area {
  margin-bottom: 16px;
}

.image-upload {
  width: 100%;
}

.upload-placeholder {
  text-align: center;
  padding: 40px 0;
}

.upload-text {
  margin: 12px 0 4px;
  font-size: 14px;
  color: #606266;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.upload-preview {
  position: relative;
  text-align: center;
  padding: 16px;
}

.preview-img {
  max-height: 240px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.upload-actions {
  margin-top: 12px;
}

.prompt-area {
  margin-bottom: 16px;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.generating-hint {
  font-size: 12px;
  color: #909399;
}

.progress-bar {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  font-size: 13px;
  color: #909399;
  margin: 8px 0 0;
}

.result-card {
  min-height: 100px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.image-grid-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.image-grid-item:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.grid-image {
  width: 100%;
  height: 240px;
  display: block;
  background: #f5f7fa;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 240px;
  color: #c0c4cc;
  gap: 8px;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
}

.image-item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fafafa;
  border-top: 1px solid #e4e7ed;
}

.image-mode-tag {
  font-size: 12px;
  color: #909399;
}

.info-card :deep(.el-card__body) {
  padding: 16px;
}

.tips {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

.tips-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.tips-content p {
  margin: 0;
}

.placeholder {
  padding: 20px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  gap: 8px;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  flex-shrink: 0;
}

.history-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  min-width: 0;
}

.history-mode {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
}

.history-time {
  font-size: 11px;
  color: #909399;
}
</style>