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
            <div v-for="(item, i) in history" :key="i" class="history-item" @click="viewHistory(item)">
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
            <el-button v-if="results.length > 0" @click="clearResults" size="default">
              清空结果
            </el-button>
          </div>

          <!-- 生成进度 -->
          <div v-if="generating" class="progress-bar">
            <el-progress :percentage="progress" :status="progress === 100 ? 'success' : undefined" :stroke-width="4" />
            <p class="progress-text">AI 正在生成图片，请稍候...</p>
          </div>
        </el-card>

        <!-- 结果画廊 -->
        <el-card v-if="results.length > 0" shadow="never" class="result-card" style="margin-top:12px">
          <template #header>
            <span class="card-title">生成结果 ({{ results.length }})</span>
          </template>
          <div class="image-grid">
            <div v-for="(item, i) in results" :key="i" class="image-grid-item">
              <el-image
                :src="item.url"
                fit="contain"
                class="grid-image"
                :preview-src-list="results.map(r => r.url)"
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
                <el-button size="small" text type="primary" @click="downloadImage(item.url, i)">
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, PictureFilled, Plus, MagicStick, Download, WarningFilled, Loading } from '@element-plus/icons-vue'
import { api } from '@/api'

document.title = '造价通 - 图片生成'

const mode = ref('text-to-image')
const prompt = ref('')
const imageSize = ref('1024x1024')
const generating = ref(false)
const progress = ref(0)
const results = ref([])
const history = ref([])
const referenceImage = ref('')
const referenceFile = ref(null)
const uploadRef = ref(null)

const canGenerate = computed(() => {
  if (mode.value === 'text-to-image') {
    return prompt.value.trim().length > 0
  }
  return prompt.value.trim().length > 0 && referenceFile.value !== null
})

function onModeChange(index) {
  mode.value = index
}

function onFileChange(uploadFile) {
  const file = uploadFile.raw
  if (!file) return

  // 验证大小
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片文件过大，请控制在5MB以内')
    return
  }

  referenceFile.value = file
  // 生成预览URL
  referenceImage.value = URL.createObjectURL(file)
}

function removeFile() {
  if (referenceImage.value) {
    URL.revokeObjectURL(referenceImage.value)
  }
  referenceImage.value = ''
  referenceFile.value = null
}

function clearResults() {
  results.value = []
}

async function generateImage() {
  if (!canGenerate.value) return

  generating.value = true
  progress.value = 10

  try {
    let resp

    if (mode.value === 'text-to-image') {
      // 文生图
      resp = await api.post('/ai/generate-image', {
        prompt: prompt.value,
        size: imageSize.value,
      })
      progress.value = 80
    } else {
      // 图生图
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
        results.value.unshift({
          url,
          mode: resp.mode || mode.value,
          prompt: prompt.value,
          revised_prompt: resp.revised_prompt || '',
        })
        // 添加到历史
        history.value.unshift({
          url,
          mode: mode.value,
          time: new Date().toLocaleTimeString(),
        })
        // 限制历史记录数量
        if (history.value.length > 10) {
          history.value = history.value.slice(0, 10)
        }
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

async function downloadImage(url, index) {
  try {
    const resp = await fetch(url)
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `AI生成图片_${index + 1}.png`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch {
    // 如果跨域下载失败，直接打开新窗口
    window.open(url, '_blank')
  }
}

function viewHistory(item) {
  // 点击历史记录，查看该图片
  const idx = results.value.findIndex(r => r.url === item.url)
  if (idx >= 0) {
    // 已经存在结果中
  }
}
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