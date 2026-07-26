<template>
  <div class="docgen-layout">
    <!-- 左侧：文档类型选择 -->
    <aside class="docgen-sidebar">
      <div class="sidebar-header">
        <h3 class="sidebar-title">选择文档类型</h3>
        <p class="sidebar-subtitle">选择要生成的工程文档类型</p>
      </div>
      <div class="type-list">
        <div
          v-for="t in docTypes"
          :key="t.key"
          class="type-item"
          :class="{ active: selectedType === t.key }"
          @click="selectType(t.key)"
        >
          <div class="type-icon-wrap" :style="{ background: t.bg }">
            <span class="type-emoji">{{ t.icon }}</span>
          </div>
          <div class="type-meta">
            <span class="type-name">{{ t.name }}</span>
            <span class="type-desc">{{ t.desc }}</span>
          </div>
          <el-icon class="type-check" v-if="selectedType === t.key"><Check /></el-icon>
        </div>
      </div>
    </aside>

    <!-- 中间：参数填写 -->
    <main class="docgen-main">
      <div class="docgen-header">
        <div class="header-left">
          <h2 class="page-title">{{ currentTypeName }}</h2>
          <el-breadcrumb separator="/" class="step-breadcrumb">
            <el-breadcrumb-item>选类型</el-breadcrumb-item>
            <el-breadcrumb-item>填参数</el-breadcrumb-item>
            <el-breadcrumb-item>生成</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" :loading="generating" @click="handleGenerate">
            <el-icon><MagicStick /></el-icon>
            {{ generating ? '生成中...' : '开始生成' }}
          </el-button>
        </div>
      </div>

      <!-- 步骤指示器 -->
      <div class="steps-bar">
        <div class="step" :class="{ active: step >= 1, done: step > 1 }">
          <div class="step-num">1</div>
          <span class="step-label">选择类型</span>
        </div>
        <div class="step-line" :class="{ active: step > 1 }"></div>
        <div class="step" :class="{ active: step >= 2, done: step > 2 }">
          <div class="step-num">2</div>
          <span class="step-label">填写参数</span>
        </div>
        <div class="step-line" :class="{ active: step > 2 }"></div>
        <div class="step" :class="{ active: step >= 3, done: step > 3 }">
          <div class="step-num">3</div>
          <span class="step-label">AI 生成</span>
        </div>
        <div class="step-line" :class="{ active: step > 3 }"></div>
        <div class="step" :class="{ active: step >= 4 }">
          <div class="step-num">4</div>
          <span class="step-label">预览导出</span>
        </div>
      </div>

      <!-- 参数表单 -->
      <el-card class="form-card" shadow="never" v-if="step <= 2">
        <template #header>
          <div class="form-card-header">
            <span class="form-card-title">项目参数</span>
            <el-tag size="small" type="info">带 * 为必填</el-tag>
          </div>
        </template>
        <el-form :model="form" label-width="120px" label-position="right">
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="项目名称" required>
                <el-input v-model="form.name" placeholder="例如：XX县污水管网改造工程" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="项目地点" required>
                <el-input v-model="form.location" placeholder="例如：湖南省湘西州" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="工程规模" required>
                <el-input v-model="form.scale" placeholder="例如：DN800管道11公里">
                  <template #append>
                    <el-select v-model="form.scaleUnit" style="width: 90px">
                      <el-option label="公里" value="km" />
                      <el-option label="米" value="m" />
                      <el-option label="㎡" value="m²" />
                      <el-option label="层" value="层" />
                      <el-option label="座" value="座" />
                    </el-select>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="编制阶段" required>
                <el-select v-model="form.stage" placeholder="选择阶段">
                  <el-option label="可研/立项阶段" value="feasibility" />
                  <el-option label="初步设计/报批" value="preliminary" />
                  <el-option label="施工图/招投标" value="construction" />
                  <el-option label="施工阶段" value="building" />
                  <el-option label="结算/审计" value="settlement" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="工程类型">
                <el-select v-model="form.engType" placeholder="选择工程类型">
                  <el-option label="市政管网（给水/排水）" value="pipeline" />
                  <el-option label="道路工程" value="road" />
                  <el-option label="建筑工程" value="building" />
                  <el-option label="水利工程" value="water" />
                  <el-option label="园林绿化" value="landscape" />
                  <el-option label="机电安装" value="mep" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="输出格式">
                <el-radio-group v-model="form.outputFormat">
                  <el-radio value="docx">Word (.docx)</el-radio>
                  <el-radio value="md">Markdown</el-radio>
                  <el-radio value="pdf">PDF</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="补充说明">
            <el-input
              v-model="form.note"
              type="textarea"
              :rows="3"
              placeholder="额外要求，例如：需要包含工程数量表、需要引用湘西信息价等"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="goStep3">
              下一步：生成文档
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- AI 生成中 -->
      <el-card class="gen-card" shadow="never" v-if="step === 3">
        <template #header>
          <div class="gen-header">
            <span class="gen-title">AI 正在生成文档</span>
            <el-tag v-if="genStatus" :type="genDone ? 'success' : 'info'" effect="light">
              {{ genStatus }}
            </el-tag>
          </div>
        </template>
        <div class="gen-progress-wrap">
          <el-progress
            :percentage="genProgress"
            :status="genDone ? 'success' : ''"
            :stroke-width="8"
            striped
            striped-flow
          />
        </div>
        <div class="gen-log">
          <div v-for="(log, i) in genLogs" :key="i" class="log-line" :class="{ new: log.new }">
            <el-icon color="#2563eb"><Check /></el-icon>
            <span>{{ log.text }}</span>
          </div>
        </div>
      </el-card>

      <!-- 预览导出 -->
      <el-card class="preview-card" shadow="never" v-if="step === 4">
        <template #header>
          <div class="preview-header">
            <span class="preview-title">文档预览</span>
            <div class="preview-actions">
              <el-button size="small" @click="step = 2">
                <el-icon><ArrowLeft /></el-icon>
                返回修改
              </el-button>
              <el-button size="small" type="primary" @click="handleExport">
                <el-icon><Download /></el-icon>
                导出 {{ form.outputFormat.toUpperCase() }}
              </el-button>
            </div>
          </div>
        </template>
        <div class="preview-content">
          <div class="preview-placeholder">
            <el-icon :size="64" color="#cbd5e1"><Document /></el-icon>
            <p>文档预览区域</p>
            <p class="preview-hint">AI 生成的文档将在这里实时展示</p>
          </div>
        </div>
      </el-card>
    </main>

    <!-- 右侧：快速信息 -->
    <aside class="docgen-info">
      <el-card class="info-card" shadow="never">
        <template #header>
          <span class="info-title">生成提示</span>
        </template>
        <div class="info-body">
          <div class="info-item" v-for="tip in tips" :key="tip.title">
            <div class="tip-icon">{{ tip.icon }}</div>
            <div class="tip-content">
              <span class="tip-title">{{ tip.title }}</span>
              <span class="tip-text">{{ tip.text }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </aside>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, MagicStick, ArrowRight, ArrowLeft, Download } from '@element-plus/icons-vue'

const route = useRoute()

const selectedType = ref(route.query.type || 'bid')
const step = ref(1)
const generating = ref(false)
const genProgress = ref(0)
const genStatus = ref('')
const genDone = ref(false)
const genLogs = ref([])
const form = reactive({
  name: '',
  location: '',
  scale: '',
  scaleUnit: 'km',
  stage: '',
  engType: '',
  outputFormat: 'docx',
  note: '',
})

const docTypes = [
  { key: 'bid',      name: '投标文件',      icon: '📑', desc: '技术标+商务标',  bg: 'linear-gradient(135deg,#dbeafe,#bfdbfe)' },
  { key: 'proposal', name: '方案说明',      icon: '📋', desc: '比选/优化方案',  bg: 'linear-gradient(135deg,#d1fae5,#a7f3d0)' },
  { key: 'prelim',   name: '初步设计说明',  icon: '📐', desc: '报批/评审稿',   bg: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)' },
  { key: 'draw',     name: '施工图设计说明', icon: '📏', desc: '施工图阶段',   bg: 'linear-gradient(135deg,#fef3c7,#fde68a)' },
  { key: 'feas',     name: '可研报告',      icon: '📊', desc: '立项/报批',    bg: 'linear-gradient(135deg,#fce7f3,#fbcfe8)' },
  { key: 'constr',   name: '施工组织设计',  icon: '📝', desc: '总体/专题',    bg: 'linear-gradient(135deg,#ccfbf1,#99f6e4)' },
  { key: 'contract', name: '合同范本',      icon: '📁', desc: '总包/分包',    bg: 'linear-gradient(135deg,#f1f5f9,#e2e8f0)' },
  { key: 'cost',     name: '概算/目标成本', icon: '💰', desc: '投资估算',     bg: 'linear-gradient(135deg,#ecfdf5,#d1fae5)' },
]

const currentTypeName = computed(() => {
  const t = docTypes.find(d => d.key === selectedType.value)
  return t ? t.name : '文档生成'
})

const tips = [
  { icon: '💡', title: '数据来源',   text: '价格数据来自造价通信息价库，单价可追溯至各地政府发布价' },
  { icon: '📐', title: '规范依据',   text: '文档结构参照行业标准格式谱，章节编号对齐行业惯例' },
  { icon: '🔄', title: '迭代修改',   text: '生成后支持逐章节修改，AI会保持整体风格一致' },
  { icon: '📤', title: '导出格式',   text: '支持导出 Word / Markdown / PDF，保留行业排版格式' },
]

function selectType(key) {
  selectedType.value = key
  step.value = 1
}

function goStep3() {
  if (!form.name || !form.location || !form.scale) {
    ElMessage.warning('请填写必填项（项目名称、地点、规模）')
    return
  }
  step.value = 3
  startGeneration()
}

function resetForm() {
  step.value = 1
  generating.value = false
  genProgress.value = 0
  genStatus.value = ''
  genDone.value = false
  genLogs.value = []
  Object.assign(form, {
    name: '', location: '', scale: '', scaleUnit: 'km',
    stage: '', engType: '', outputFormat: 'docx', note: '',
  })
}

function startGeneration() {
  generating.value = true
  genProgress.value = 0
  genStatus.value = '正在分析需求...'
  genDone.value = false
  genLogs.value = []

  const logs = [
    '读取格式谱模板结构',
    '分析项目参数与工程类型',
    '检索价格信息库数据',
    '匹配当地信息价',
    '生成第一章：总论',
    '生成第二章：建设条件',
    '生成第三章：工程方案',
    '生成第四章：施工组织',
    '生成第五章：投资估算',
    '格式化排版',
  ]

  let i = 0
  const interval = setInterval(() => {
    if (i < logs.length) {
      genLogs.value.push({ text: logs[i], new: true })
      genProgress.value = Math.round(((i + 1) / logs.length) * 100)
      genStatus.value = i < logs.length - 1 ? '正在生成...' : '即将完成'
      i++
    } else {
      clearInterval(interval)
      genDone.value = true
      genStatus.value = '生成完成'
      generating.value = false
      step.value = 4
    }
  }, 600)
}

function handleGenerate() {
  if (step.value <= 2) {
    goStep3()
    return
  }
  startGeneration()
}

function handleExport() {
  ElMessage.success('正在导出 ' + form.outputFormat.toUpperCase() + ' 文件...')
}
</script>

<style scoped>
.docgen-layout {
  display: grid;
  grid-template-columns: 240px 1fr 260px;
  gap: var(--space-5);
  height: calc(100vh - var(--topbar-height) - var(--space-6));
  min-height: 500px;
}

/* ---------- 左侧类型选择 ---------- */
.docgen-sidebar {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: var(--space-5) var(--space-4) var(--space-3);
}

.sidebar-title {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.sidebar-subtitle {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: var(--space-1) 0 0;
}

.type-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2) var(--space-3);
}

.type-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  margin-bottom: var(--space-1);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.type-item:hover {
  background: var(--gray-100);
}

.type-item.active {
  background: #eff6ff;
  border-color: var(--brand-500);
}

.type-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.type-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.type-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.type-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.type-check {
  color: var(--brand-500);
  font-size: 16px;
}

/* ---------- 中间主区 ---------- */
.docgen-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  overflow: hidden;
}

.docgen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.step-breadcrumb {
  margin-top: var(--space-1);
}

.steps-bar {
  display: flex;
  align-items: center;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
  padding: var(--space-4) var(--space-5);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.step-num {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--gray-200);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: 700;
  transition: all var(--transition-base);
}

.step.active .step-num {
  background: var(--brand-500);
  color: #fff;
  box-shadow: var(--shadow-brand);
}

.step.done .step-num {
  background: var(--success-500);
  color: #fff;
}

.step-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}

.step.active .step-label {
  color: var(--text-primary);
  font-weight: 600;
}

.step-line {
  flex: 1;
  height: 2px;
  background: var(--gray-200);
  margin: 0 var(--space-3);
  border-radius: 1px;
  transition: background var(--transition-base);
}

.step-line.active {
  background: var(--brand-500);
}

/* 表单 */
.form-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-card-title {
  font-size: var(--text-md);
  font-weight: 600;
}

.gen-header,
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gen-title,
.preview-title {
  font-size: var(--text-md);
  font-weight: 600;
}

.gen-progress-wrap {
  padding: var(--space-4) 0;
}

.gen-log {
  max-height: 200px;
  overflow-y: auto;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  padding: var(--space-3);
}

.log-line {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  padding: var(--space-1) 0;
  animation: fadeIn 0.3s ease;
}

.log-line.new {
  color: var(--text-primary);
  font-weight: 500;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.preview-content {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-placeholder {
  text-align: center;
  color: var(--text-tertiary);
}

.preview-placeholder p {
  margin: var(--space-3) 0 0;
  font-size: var(--text-md);
}

.preview-hint {
  font-size: var(--text-sm) !important;
}

.preview-actions {
  display: flex;
  gap: var(--space-2);
}

/* ---------- 右侧信息 ---------- */
.docgen-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.info-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
}

.info-title {
  font-size: var(--text-md);
  font-weight: 600;
}

.info-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.info-item {
  display: flex;
  gap: var(--space-3);
}

.tip-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.tip-content {
  display: flex;
  flex-direction: column;
}

.tip-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.tip-text {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 2px;
  line-height: 1.5;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1024px) {
  .docgen-layout {
    grid-template-columns: 200px 1fr;
  }
  .docgen-info {
    display: none;
  }
}

@media (max-width: 768px) {
  .docgen-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  .docgen-sidebar {
    max-height: 160px;
  }
  .type-list {
    display: flex;
    overflow-x: auto;
    gap: var(--space-2);
  }
  .type-item {
    flex-shrink: 0;
  }
}
</style>