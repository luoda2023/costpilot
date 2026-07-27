<template>
  <div class="preview-page">
    <el-row :gutter="16" style="height:100%">
      <!-- 左侧目录 -->
      <el-col :span="5">
        <el-card shadow="never" class="tree-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">文件目录</span>
              <el-button size="small" @click="loadRoot">刷新</el-button>
            </div>
          </template>
          <el-input v-model="pathInput" placeholder="输入路径回车" size="small" clearable @keyup.enter="loadByPath" style="margin-bottom:8px" v-auto-halfwidth>
            <template #append><el-button size="small" @click="loadByPath">进入</el-button></template>
          </el-input>
          <el-tree
            :data="treeData"
            :props="treeProps"
            :load="loadNode"
            lazy
            node-key="path"
            @node-click="onNodeClick"
            highlight-current
            size="small"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.is_dir" :size="14" color="#e6a23c"><Folder /></el-icon>
                <el-icon v-else :size="14" color="#409eff"><Document /></el-icon>
                <span class="node-label">{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧预览 -->
      <el-col :span="19">
        <el-card shadow="never" class="preview-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ currentFile ? currentFile.split('/').pop() : '选择文件预览' }}</span>
              <div class="header-actions">
                <el-tag size="small" v-if="currentExt" type="info" effect="plain">{{ currentExt }}</el-tag>
                <el-button size="small" @click="openExternal" :disabled="!currentFile">系统打开</el-button>
                <el-button size="small" @click="copyPath" :disabled="!currentFile">复制路径</el-button>
              </div>
            </div>
          </template>

          <div v-if="!currentFile" class="placeholder">
            <el-empty description="从左侧目录选择文件" :image-size="60" />
          </div>
<div v-else-if="loadingPreview" class="placeholder">
  <el-icon class="is-loading" :size="32"><Loading /></el-icon>
  <p style="margin-top:8px;color: var(--text-tertiary)">加载中...</p>
</div>
<div v-else-if="previewError" class="placeholder">
  <el-empty description="预览加载失败">
    <el-button type="primary" @click="openExternal">系统打开</el-button>
  </el-empty>
</div>
          <div v-else class="preview-body">
            <!-- PDF -->
            <VueOfficePDF v-if="currentExt === 'pdf'" :src="previewUrl" class="office-viewer" @error="onPreviewError" />
            <!-- DOCX -->
            <VueOfficeDocx v-else-if="currentExt === 'docx'" :src="previewUrl" class="office-viewer" @error="onPreviewError" />
            <!-- XLSX -->
            <VueOfficeExcel v-else-if="['xlsx','xls'].includes(currentExt)" :src="previewUrl" class="office-viewer" @error="onPreviewError" />
            <!-- 图片 -->
            <div v-else-if="['jpg','jpeg','png','gif','webp','bmp'].includes(currentExt)" class="img-wrap">
              <img :src="previewUrl" />
            </div>
            <!-- 文本 -->
            <pre v-else-if="['md','txt','yml','yaml','json','csv','log'].includes(currentExt)" class="text-preview">{{ textContent }}</pre>
            <!-- 其他 -->
            <div v-else class="placeholder">
              <el-empty :description="'.' + currentExt + ' 暂不支持预览'">
                <el-button type="primary" @click="openExternal">系统打开</el-button>
              </el-empty>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import VueOfficePDF from '@vue-office/pdf/lib/v3'
import VueOfficeDocx from '@vue-office/docx/lib/v3'
import VueOfficeExcel from '@vue-office/excel/lib/v3'
import '@vue-office/docx/lib/v3/index.css'
import '@vue-office/excel/lib/v3/index.css'

const rootPath = 'H:/AI-model'
const pathInput = ref(rootPath)
const treeData = ref([])
const currentFile = ref('')
  const loadingPreview = ref(false)
  const previewError = ref(false)
  const textContent = ref('')
const treeProps = { label: 'name', children: 'children', isLeaf: (data) => !data.is_dir }
const currentExt = computed(() => currentFile.value ? currentFile.value.split('.').pop().toLowerCase() : '')
const previewUrl = computed(() => {
  if (!currentFile.value) return ''
  if (['md','txt','yml','yaml','json','csv','log'].includes(currentExt.value)) return ''
  // file:// 协议下必须用绝对地址，包含完整路径
  const isFileProtocol = typeof window !== 'undefined' && window.location.protocol === 'file:'
  if (isFileProtocol) {
    return 'http://127.0.0.1:8765/api/v1/preview/file?path=' + encodeURIComponent(currentFile.value)
  }
  // http 模式下 baseURL=/api/v1，只需补 /preview/file
  return '/preview/file?path=' + encodeURIComponent(currentFile.value)
})

async function loadRoot() { await loadByPath() }
async function loadByPath() {
  try {
    const r = await api.get('/files/list', { params: { path: pathInput.value } })
    treeData.value = r.items
  } catch (e) { ElMessage.error('读取失败：' + (e.response?.data?.detail || e.message)) }
}
async function loadNode(node, resolve) {
  if (!node.data?.is_dir) return resolve([])
  try {
    const r = await api.get('/files/list', { params: { path: node.data.path } })
    resolve(r.items)
  } catch { resolve([]) }
}
async function onNodeClick(data) {
  if (data.is_dir) return
  currentFile.value = data.path
  loadingPreview.value = true; previewError.value = false; textContent.value = ''
  try {
    if (['md','txt','yml','yaml','json','csv','log'].includes(currentExt.value)) {
      const r = await api.get('/preview/text', { params: { path: data.path } })
      textContent.value = r
    }
  } catch { previewError.value = true }
  finally { loadingPreview.value = false }
}
  function onPreviewError(err) { previewError.value = true; ElMessage.error('预览失败') }
function openExternal() {
  if (window.engineeringAssistant?.openExternal) window.engineeringAssistant.openExternal(currentFile.value)
  else ElMessage.info(`路径: ${currentFile.value}`)
}
function copyPath() { navigator.clipboard.writeText(currentFile.value); ElMessage.success('已复制') }
onMounted(loadRoot)
</script>

<style scoped>
.preview-page { height: 100vh; }
.tree-card { height: 100%; border-radius:8px; overflow:auto; }
.preview-card { height: 100%; border-radius:8px; display: flex; flex-direction: column; }
.preview-card :deep(.el-card__body) { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.card-header { display:flex; justify-content:space-between; align-items:center; }
.card-title { font-size:15px; font-weight:600; color: var(--text-primary); line-height:1.5; }
.header-actions { display:flex; gap:8px; align-items:center; }
.tree-node { display:flex; align-items:center; gap:6px; }
.node-label { font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; line-height:1.5; }
.placeholder { padding:80px 0; text-align:center; }
.preview-body { flex: 1; overflow: auto; }
.img-wrap { text-align:center; flex: 1; display: flex; align-items: center; justify-content: center; }
.img-wrap img { max-width:100%; max-height:100%; border-radius:4px; }
.text-preview { white-space:pre-wrap; font-family:'Courier New',monospace; font-size:13px; line-height:1.6; background: var(--gray-50); padding:12px; margin:0; flex: 1; overflow: auto; }
.office-viewer { flex: 1; min-height: 0; overflow: auto; }
</style>