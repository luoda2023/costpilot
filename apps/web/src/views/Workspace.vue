<template>
  <div class="workspace" v-loading="loading" element-loading-text="正在加载数据...">
    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="never" class="stat-card">
          <div class="stat-inner">
            <div class="stat-left">
              <div class="stat-label">{{ card.label }}</div>
              <div class="stat-value" :class="card.cls">{{ card.value }}</div>
            </div>
            <div class="stat-icon-wrap" :style="{ background: card.bg }">
              <el-icon :size="22" color="#fff"><component :is="card.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速入口 -->
    <el-card shadow="never" class="section-card">
      <template #header><span class="section-title">快速入口</span></template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="item in quickLinks" :key="item.label">
          <el-button :type="item.type" size="large" class="quick-btn" @click="$router.push(item.path)">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 各专业条数 -->
    <el-card shadow="never" class="section-card">
      <template #header><span class="section-title">专业概览</span></template>
      <div class="specialty-grid">
        <div v-for="(count, name) in stats.by_specialty" :key="name" class="specialty-item">
          <span class="spec-name">{{ name }}</span>
          <span class="spec-count">{{ count }}</span>
        </div>
      </div>
    </el-card>

    <!-- 项目列表 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">最近项目</span>
          <el-button size="small" type="primary" @click="newProjectDialog = true">+ 新建</el-button>
        </div>
      </template>
      <el-table :data="projects" stripe empty-text="暂无项目，点击右上角新建">
        <el-table-column prop="name" label="项目名" min-width="200" />
        <el-table-column prop="region" label="地区" width="100" />
        <el-table-column prop="stage" label="阶段" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag size="small">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="newProjectDialog" title="新建项目" width="500" :close-on-click-modal="false">
      <el-form :model="newProject" label-width="90">
        <el-form-item label="项目名" required>
          <el-input v-model="newProject.name" placeholder="如：某高层住宅 1# 楼估算" />
        </el-form-item>
        <el-form-item label="地区" required>
          <el-select v-model="newProject.region" placeholder="选择" style="width:100%">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段" required>
          <el-radio-group v-model="newProject.stage">
            <el-radio-button value="估算">估算</el-radio-button>
            <el-radio-button value="概算">概算</el-radio-button>
            <el-radio-button value="预算">预算</el-radio-button>
            <el-radio-button value="结算">结算</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="newProject.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newProjectDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { PricesAPI, ProjectsAPI } from '@/api'
import { PriceTag, Location, Folder, Connection, Search, Document, Files, ChatDotRound } from '@element-plus/icons-vue'

const loading = ref(true)
const stats = ref({})
const projects = ref([])
const newProjectDialog = ref(false)
const creating = ref(false)
const newProject = reactive({ name: '', region: '', stage: '估算', note: '' })
const regions = ['北京市','上海市','天津市','重庆市','广东省','浙江省','江苏省','四川省','山东省','湖北省','湖南省','福建省','河北省','河南省','安徽省','江西省']

const statCards = ref([])
const quickLinks = [
  { label: '查询综合单价', icon: Search, path: '/prices', type: 'primary' },
  { label: '生成文本', icon: Document, path: '/text-gen', type: 'success' },
  { label: '预览文件', icon: Files, path: '/preview', type: 'warning' },
  { label: 'AI 助手', icon: ChatDotRound, path: '/chat', type: 'info' },
]

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

async function loadStats() {
  try {
    const r = await PricesAPI.stats()
    stats.value = r
    statCards.value = [
      { label: '总价格条目', value: r.total_prices ?? '-', icon: PriceTag, bg: '#409eff', cls: '' },
      { label: '市政专题', value: r.total_topics ?? '-', icon: Location, bg: '#67c23a', cls: '' },
      { label: '项目数', value: projects.value.length, icon: Folder, bg: '#e6a23c', cls: '' },
      { label: 'API 状态', value: '正常', icon: Connection, bg: '#67c23a', cls: 'ok' },
    ]
  } catch { statCards.value[3] = { label: 'API 状态', value: '异常', icon: Connection, bg: '#f56c6c', cls: 'err' } }
  finally { loading.value = false }
}

async function loadProjects() {
  try { projects.value = await ProjectsAPI.list() } catch {}
}

async function createProject() {
  if (!newProject.name || !newProject.region || !newProject.stage) {
    ElMessage.warning('请填写完整')
    return
  }
  creating.value = true
  try {
    await ProjectsAPI.create({ ...newProject })
    ElMessage.success('项目已创建')
    newProjectDialog.value = false
    newProject.name = ''; newProject.note = ''
    await loadProjects()
  } catch (e) {
    ElMessage.error('创建失败：' + (e.response?.data?.detail || e.message))
  } finally { creating.value = false }
}

onMounted(() => { loadStats(); loadProjects() })
</script>

<style scoped>
.workspace { display:flex; flex-direction:column; gap:14px; }
.stat-row { margin-bottom:0; }
.stat-card { border-radius:8px; }
.stat-inner { display:flex; align-items:center; justify-content:space-between; }
.stat-left { flex:1; }
.stat-label { font-size:13px; color:#909399; margin-bottom:4px; }
.stat-value { font-size:26px; font-weight:700; color:#303133; }
.stat-value.ok { color:#67c23a; }
.stat-value.err { color:#f56c6c; }
.stat-icon-wrap { width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.section-card { border-radius:8px; margin-top:0; }
.section-title { font-size:15px; font-weight:600; color:#303133; }
.card-header { display:flex; justify-content:space-between; align-items:center; }
.quick-btn { width:100%; height:56px; font-size:15px; display:flex; align-items:center; gap:6px; border-radius:8px; }
.specialty-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.specialty-item { display:flex; justify-content:space-between; padding:8px 12px; background:#f5f7fa; border-radius:6px; }
.spec-name { color:#606266; font-size:13px; }
.spec-count { color:#303133; font-weight:600; font-size:14px; }
</style>