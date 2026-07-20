<template>
  <div class="preview-page">
    <el-row :gutter="16">
      <!-- 左侧:目录树 -->
      <el-col :span="6">
        <el-card shadow="never" class="tree-card">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>资料库目录</span>
              <el-button size="small" @click="loadRoot">刷新</el-button>
            </div>
          </template>
          <el-input v-model="pathInput" placeholder="输入路径，回车进入" @keyup.enter="loadByPath" style="margin-bottom:8px">
            <template #append><el-button @click="loadByPath">进入</el-button></template>
          </el-input>
          <el-tree
            :data="treeData"
            :props="treeProps"
            :load="loadNode"
            lazy
            node-key="path"
            @node-click="onNodeClick"
            highlight-current
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.is_dir"><Folder /></el-icon>
                <el-icon v-else><Document /></el-icon>
                <span :style="{color: data.is_dir ? '#409eff' : '#606266'}">{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧:预览区 -->
      <el-col :span="18">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ currentFile || '请选择文件预览' }}</span>
              <div>
                <el-tag size="small" v-if="currentExt" effect="plain" type="info">{{ currentExt }}</el-tag>
                <el-button size="small" @click="openExternal" :disabled="!currentFile">用系统打开</el-button>
                <el-button size="small" @click="copyPath" :disabled="!currentFile">复制路径</el-button>
              </div>
            </div>
          </template>

          <div v-if="!currentFile" class="placeholder">
            <el-empty description="从左侧目录树选择文件，预览在此显示" />
          </div>

          <div v-else-if="loadingPreview" class="placeholder">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>正在加载预览...</p>
          </div>

          <div v-else>
            <!-- PDF -->
            <VueOfficePDF
              v-if="currentExt === 'pdf'"
              :src="previewUrl"
              class="office-viewer"
              @error="onPreviewError"
            />

            <!-- DOCX -->
            <VueOfficeDocx
              v-else-if="['docx'].includes(currentExt)"
              :src="previewUrl"
              class="office-viewer"
              @error="onPreviewError"
            />

            <!-- XLSX / XLS -->
            <VueOfficeExcel
              v-else-if="['xlsx','xls'].includes(currentExt)"
              :src="previewUrl"
              class="office-viewer"
              @error="onPreviewError"
            />

            <!-- 图片 -->
            <div v-else-if="['jpg','jpeg','png','gif','webp','bmp'].includes(currentExt)" class="img-wrap">
              <img :src="previewUrl" />
            </div>

            <!-- 文本(md/txt/yml/json/csv) -->
            <pre v-else-if="['md','txt','markdown','yml','yaml','json','csv','log'].includes(currentExt)" class="text-preview">{{ textContent }}</pre>

            <!-- 其他兜底 -->
            <div v-else class="placeholder">
              <el-empty :description="'.' + currentExt + ' 格式暂不支持内联预览'">
                <el-button type="primary" @click="openExternal">用系统默认程序打开</el-button>
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
import axios from 'axios'

// 全格式预览组件(必须显式引 /lib/v3 子路径,此包是 v2/v3 双版本)
import VueOfficePDF from '@vue-office/pdf/lib/v3'
import VueOfficeDocx from '@vue-office/docx/lib/v3'
import VueOfficeExcel from '@vue-office/excel/lib/v3'
import '@vue-office/docx/lib/v3/index.css'
import '@vue-office/excel/lib/v3/index.css'

const apiUrl = '/api/v1'
const rootPath = 'H:/AI-model'
const pathInput = ref(rootPath)
const treeData = ref([])
const currentFile = ref('')
const loadingPreview = ref(false)
const textContent = ref('')

const treeProps = { label: 'name', children: 'children', isLeaf: (data) => !data.is_dir }
const currentExt = computed(() => {
  if (!currentFile.value) return ''
  return currentFile.value.split('.').pop().toLowerCase()
})

// 预览 URL - PDF/DOCX/XLSX 走 /preview/file,文本走 /preview/text
const previewUrl = computed(() => {
  if (!currentFile.value) return ''
  if (['md','txt','markdown','yml','yaml','json','csv','log'].includes(currentExt.value)) return ''  // 文本走 textContent
  return apiUrl + '/preview/file?path=' + encodeURIComponent(currentFile.value)
})

async function loadRoot() {
  await loadByPath()
}

async function loadByPath() {
  try {
    const r = await axios.get(apiUrl + '/files/list', { params: { path: pathInput.value } })
    treeData.value = r.data.items
  } catch (e) {
    ElMessage.error('读取目录失败：' + (e.response?.data?.detail || e.message))
  }
}

async function loadNode(node, resolve) {
  if (!node.data || !node.data.is_dir) return resolve([])
  try {
    const r = await axios.get(apiUrl + '/files/list', { params: { path: node.data.path } })
    resolve(r.data.items)
  } catch {
    resolve([])
  }
}

async function onNodeClick(data) {
  if (data.is_dir) return
  currentFile.value = data.path
  loadingPreview.value = true
  textContent.value = ''
  try {
    if (['md','txt','markdown','yml','yaml','json','csv','log'].includes(currentExt.value)) {
      const r = await axios.get(apiUrl + '/preview/text', { params: { path: data.path } })
      textContent.value = r.data
    }
  } finally {
    loadingPreview.value = false
  }
}

function onPreviewError(err) {
  console.error('预览失败', err)
  ElMessage.error('预览失败：' + (err?.message || '未知错误'))
}

function openExternal() {
  if (window.costpilot?.openExternal) {
    window.costpilot.openExternal(currentFile.value)
  } else {
    ElMessage.info(`路径: ${currentFile.value}`)
  }
}

function copyPath() {
  navigator.clipboard.writeText(currentFile.value)
  ElMessage.success('路径已复制')
}

onMounted(loadRoot)
</script>

<style scoped>
.preview-page { background:#fff; padding:8px; border-radius:4px; }
.tree-card { height: 80vh; overflow: auto; }
.tree-node { display:flex; align-items:center; gap:6px; }
.placeholder { padding:60px 0; text-align:center; }
.img-wrap { text-align:center; }
.img-wrap img { max-width:100%; max-height:720px; }
.text-preview {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  max-height: 720px;
  overflow: auto;
  background: #fafafa;
  padding: 12px;
}
.office-viewer {
  width: 100%;
  height: 720px;
  overflow: auto;
}
</style>
