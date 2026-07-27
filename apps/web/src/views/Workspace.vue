<template>
  <div class="workspace">
    <!-- 欢迎区 -->
    <section class="hero-section">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-badge">
          <el-icon><Cpu /></el-icon>
          <span>AI 驱动 · 数据有据</span>
        </div>
        <h1 class="hero-title">一句话，生成专业工程文档</h1>
        <p class="hero-subtitle">从投标文件到施工图说明，覆盖可研、初设、方案、施组全流程</p>
        <div class="hero-input-row">
<el-input
 v-model="prompt"
 placeholder="描述你的需求，例如：某DN800污水管网改造工程投标文件..."
 size="large"
 class="hero-input"
 v-auto-halfwidth
 @keyup.enter="handleQuickGen"
 >
            <template #prefix>
              <el-icon color="#94a3b8"><EditPen /></el-icon>
            </template>
          </el-input>
          <el-button
            type="primary"
            size="large"
            class="hero-btn"
            :loading="generating"
            @click="handleQuickGen"
          >
            <el-icon><MagicStick /></el-icon>
            <span>开始生成</span>
          </el-button>
        </div>
        <div class="quick-types">
          <el-tag
            v-for="t in quickTypes"
            :key="t.key"
            class="quick-type-tag"
            :type="t.active ? '' : 'info'"
            effect="plain"
            @click="selectType(t)"
          >
            <span class="type-icon">{{ t.icon }}</span>
            <span>{{ t.label }}</span>
          </el-tag>
        </div>
      </div>
    </section>

    <!-- 下方内容区 -->
    <div class="workspace-body">
      <el-row :gutter="20">
        <!-- 最近文档 -->
        <el-col :xs="24" :lg="14">
          <el-card class="section-card recent-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon color="#2563eb"><Document /></el-icon>
                  <span class="header-title">最近文档</span>
                </div>
                <el-button link type="primary" size="small">查看全部</el-button>
              </div>
            </template>
            <el-table :data="recentDocs" style="width: 100%" :show-header="false" size="small">
              <el-table-column prop="name" label="文档名称" min-width="200">
                <template #default="{ row }">
                  <div class="doc-name-cell">
                    <el-icon color="#2563eb"><Document /></el-icon>
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="类型" width="100" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="typeTagType(row.type)" effect="light">
                    {{ row.type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="date" label="日期" width="110" align="center" />
              <el-table-column label="" width="50" align="center">
                <template #default>
                  <el-button link circle size="small" class="row-action">
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <!-- 文档模板库 -->
        <el-col :xs="24" :lg="10">
          <el-card class="section-card template-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon color="#059669"><Grid /></el-icon>
                  <span class="header-title">模板库</span>
                </div>
                <el-tag size="small" type="success" effect="light">8 类</el-tag>
              </div>
            </template>
            <div class="template-grid">
              <div
                v-for="tpl in templates"
                :key="tpl.key"
                class="template-item"
                @click="goDocGen(tpl.key)"
              >
                <div class="tpl-icon" :style="{ background: tpl.color }">
                  <span class="tpl-icon-text">{{ tpl.icon }}</span>
                </div>
                <div class="tpl-info">
                  <span class="tpl-name">{{ tpl.name }}</span>
                  <span class="tpl-desc">{{ tpl.desc }}</span>
                </div>
                <el-icon class="tpl-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 数据看板 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="12" :sm="6" v-for="stat in stats" :key="stat.label">
          <div class="stat-card" :style="{ borderTopColor: stat.color }">
            <div class="stat-icon-wrap" :style="{ background: stat.bg }">
              <el-icon :size="20" :color="stat.color">{{ stat.icon }}</el-icon>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </div>
          </div>
        </el-col>
 </el-row>
 
<!-- AI 配置状态栏 -->
<el-row :gutter="20" class="stats-row">
 <el-col :span="24">
 <el-card shadow="never" class="config-status-card">
 <div class="config-status-content">
 <div class="config-status-left">
 <el-icon :size="18" :color="aiConfigured ? '#059669' : '#d97706'"><Cpu /></el-icon>
 <span class="config-status-text">
 <strong>AI 服务：</strong>
 <span v-if="aiConfigured" style="color:#059669">已配置</span>
 <span v-else style="color:#d97706">未配置</span>
 </span>
 </div>
 <el-button v-if="!aiConfigured" type="primary" size="small" @click="router.push('/settings')">
 前往配置
 </el-button>
 <el-button v-else type="default" size="small" @click="router.push('/settings')">
 修改配置
 </el-button>
 </div>
 </el-card>
 </el-col>
</el-row>
 </div>
  </div>
</template>

<script setup>
	import { ref, onMounted } from 'vue'
	import { useRouter } from 'vue-router'
	import { ElMessage } from 'element-plus'
	import { api } from '@/api'
	import {
 Cpu, EditPen, MagicStick, Document, Grid, ArrowRight,
 HomeFilled, TrendCharts, Wallet, ChatDotRound, Setting
	} from '@element-plus/icons-vue'
	
	const router = useRouter()
	
	const prompt = ref('')
	const generating = ref(false)
	const aiConfigured = ref(null)
	
	onMounted(async () => {
	  try {
	    const r = await api.get('/ai/config')
	    aiConfigured.value = r?.api_key_set === true
	  } catch {
	    aiConfigured.value = false
	  }
	})

const quickTypes = ref([
  { key: 'bid',    label: '投标文件',   icon: '📑', active: false },
  { key: 'proposal', label: '方案说明',  icon: '📋', active: false },
  { key: 'prelim', label: '初步设计',   icon: '📐', active: false },
  { key: 'draw',   label: '施工图说明',  icon: '📏', active: false },
  { key: 'feas',   label: '可研报告',   icon: '📊', active: false },
  { key: 'constr', label: '施工组织设计', icon: '📝', active: false },
])

const recentDocs = ref([
  { name: 'XX县污水管网改造工程投标文件',   type: '投标文件',   date: '2026-07-20' },
  { name: 'XX水厂扩建初步设计说明',        type: '初步设计',   date: '2026-07-18' },
  { name: 'XX道路施工图设计说明',          type: '施工图说明',  date: '2026-07-15' },
  { name: 'XX泵站专项施工方案',            type: '专项方案',   date: '2026-07-12' },
])

const templates = ref([
  { key: 'bid',     name: '投标文件',      icon: '📑', desc: '技术标+商务标', color: 'linear-gradient(135deg,#dbeafe,#bfdbfe)' },
  { key: 'proposal', name: '方案说明',     icon: '📋', desc: '比选/优化方案',  color: 'linear-gradient(135deg,#d1fae5,#a7f3d0)' },
  { key: 'prelim',  name: '初步设计说明',  icon: '📐', desc: '报批/评审稿',   color: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)' },
  { key: 'draw',    name: '施工图设计说明', icon: '📏', desc: '施工图阶段',   color: 'linear-gradient(135deg,#fef3c7,#fde68a)' },
  { key: 'feas',    name: '可研报告',      icon: '📊', desc: '立项/报批',    color: 'linear-gradient(135deg,#fce7f3,#fbcfe8)' },
  { key: 'constr',  name: '施工组织设计',  icon: '📝', desc: '总体/专题',    color: 'linear-gradient(135deg,#ccfbf1,#99f6e4)' },
  { key: 'contract', name: '合同范本',     icon: '📁', desc: '总包/分包',    color: 'linear-gradient(135deg,#f1f5f9,#e2e8f0)' },
  { key: 'cost',    name: '概算/目标成本', icon: '💰', desc: '投资估算',     color: 'linear-gradient(135deg,#ecfdf5,#d1fae5)' },
])

const stats = ref([
  { label: '已生成文档',  value: '12',   icon: 'Document',    color: '#2563eb', bg: '#dbeafe' },
  { label: '价格库条目',  value: '19.4k', icon: 'TrendCharts', color: '#059669', bg: '#d1fae5' },
  { label: '覆盖专业',    value: '8',    icon: 'Grid',        color: '#7c3aed', bg: '#ede9fe' },
  { label: '文档模板',    value: '8 类', icon: 'FolderOpened', color: '#d97706', bg: '#fef3c7' },
])

function typeTagType(type) {
  const map = { '投标文件': 'danger', '初步设计': '', '施工图说明': 'warning', '专项方案': 'info' }
  return map[type] || ''
}

function selectType(t) {
  quickTypes.value.forEach(q => q.active = false)
  t.active = true
  prompt.value = `请帮我生成一份${t.label}，项目为：`
  router.push('/docgen')
}

function goDocGen(key) {
  router.push(`/docgen?type=${key}`)
}

function handleQuickGen() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请先描述你的需求')
    return
  }
  generating.value = true
  setTimeout(() => {
    generating.value = false
    ElMessage.success('已创建生成任务，跳转到文档生成...')
    router.push('/docgen')
  }, 1200)
}
</script>

<style scoped>
.workspace {
  min-height: 100%;
}

/* ---------- 欢迎区 ---------- */
.hero-section {
  position: relative;
  background: linear-gradient(135deg, var(--brand-900) 0%, var(--brand-700) 60%, #1e40af 100%);
  border-radius: var(--radius-xl);
  padding: var(--space-10) var(--space-8);
  margin-bottom: var(--space-6);
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 80% 20%, rgba(37,99,235,0.25) 0%, transparent 60%),
    radial-gradient(ellipse at 20% 80%, rgba(16,185,129,0.1) 0%, transparent 50%);
  pointer-events: none;
}

.hero-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M0 20L20 0l20 20-20 20z'/%3E%3C/g%3E%3C/svg%3E");
  background-size: 40px 40px;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.15);
  color: var(--brand-300);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 1px;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  margin-bottom: var(--space-5);
}

.hero-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: #fff;
  margin: 0 0 var(--space-3) 0;
  letter-spacing: -0.5px;
  line-height: 1.3;
}

.hero-subtitle {
  font-size: var(--text-md);
  color: var(--gray-400);
  margin: 0 0 var(--space-6) 0;
}

.hero-input-row {
  display: flex;
  gap: var(--space-3);
  max-width: 720px;
}

.hero-input {
  flex: 1;
}

.hero-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-lg) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.15), 0 4px 12px rgba(0,0,0,0.2) !important;
  background: rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(10px);
  padding: var(--space-1);
}

.hero-input :deep(.el-input__inner) {
  color: #fff !important;
  font-size: var(--text-md);
}

.hero-input :deep(.el-input__inner::placeholder) {
  color: var(--gray-400) !important;
}

.hero-btn {
  border-radius: var(--radius-lg) !important;
  font-weight: 600;
  padding: 0 var(--space-8);
  height: 48px;
  font-size: var(--text-md);
}

.quick-types {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-5);
}

.quick-type-tag {
  cursor: pointer;
  border-radius: var(--radius-full) !important;
  padding: var(--space-1) var(--space-3) !important;
  font-size: var(--text-sm) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  background: rgba(255,255,255,0.06) !important;
  color: var(--gray-300) !important;
  transition: all var(--transition-fast);
}

.quick-type-tag:hover {
  background: rgba(255,255,255,0.12) !important;
  color: #fff !important;
  border-color: rgba(255,255,255,0.3) !important;
}

.quick-type-tag.el-tag--info {
  color: var(--gray-400) !important;
}

.type-icon {
  margin-right: var(--space-1);
}

/* ---------- 内容区 ---------- */
.workspace-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.section-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
}

.section-card :deep(.el-card__header) {
  padding: var(--space-4) var(--space-5) !important;
  border-bottom: 1px solid var(--gray-100);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.header-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
}

.doc-name-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.row-action {
  color: var(--gray-400);
  transition: all var(--transition-fast);
}

.row-action:hover {
  color: var(--brand-500);
  background: var(--gray-100);
}

/* ---------- 模板库卡片 ---------- */
.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

.template-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-base);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid transparent;
}

.template-item:hover {
  background: var(--gray-100);
  border-color: var(--gray-200);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.tpl-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.tpl-icon-text {
  line-height: 1;
}

.tpl-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.tpl-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.tpl-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 1px;
}

.tpl-arrow {
  color: var(--gray-400);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.template-item:hover .tpl-arrow {
  color: var(--brand-500);
  transform: translateX(2px);
}

/* ---------- 数据看板 ---------- */
.stats-row {
  margin-top: var(--space-5);
}

.stat-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border-top: 3px solid transparent;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon-wrap {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* ---------- AI 配置引导 ---------- */
.guide-card {
 border: 1px solid #dbeafe;
 background: linear-gradient(135deg, #eff6ff, #f8faff);
 border-radius: var(--radius-lg);
}

.guide-card :deep(.el-card__body) {
 padding: var(--space-4) var(--space-5) !important;
}

.guide-content {
 display: flex;
 align-items: center;
 gap: var(--space-4);
}

.guide-icon-wrap {
 width: 48px;
 height: 48px;
 border-radius: var(--radius-full);
 background: #dbeafe;
 display: flex;
 align-items: center;
 justify-content: center;
 flex-shrink: 0;
}

.guide-text {
 flex: 1;
 display: flex;
 flex-direction: column;
 gap: var(--space-1);
}

.guide-title {
 font-size: var(--text-md);
 font-weight: 700;
 color: var(--brand-700);
}

.guide-desc {
 font-size: var(--text-sm);
 color: var(--text-secondary);
}

/* ---------- 响应式 ---------- */
@media (max-width: 768px) {
  .hero-section {
    padding: var(--space-6) var(--space-4);
  }
  .hero-title {
    font-size: var(--text-xl);
  }
  .hero-input-row {
    flex-direction: column;
  }
  .hero-btn {
    width: 100%;
  }
  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>