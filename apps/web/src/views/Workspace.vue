<template>
  <div class="workspace" v-loading="loading" element-loading-text="正在加载数据...">
    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">总价格条目</div>
            <div class="stat-value">{{ stats.total_prices ?? '-' }}</div>
            <el-icon class="stat-icon"><PriceTag /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">市政专题</div>
            <div class="stat-value">{{ stats.total_topics ?? '-' }}</div>
            <el-icon class="stat-icon"><Location /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">项目数</div>
            <div class="stat-value">{{ projects.length }}</div>
            <el-icon class="stat-icon"><Folder /></el-icon>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">API 状态</div>
            <div class="stat-value" :class="serverOk ? 'ok' : 'err'">
              {{ serverOk ? '正常' : '异常' }}
            </div>
            <el-icon class="stat-icon"><Connection /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速入口 -->
    <el-card shadow="never" class="quick-card">
      <template #header>
        <span>快速入口</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="6">
          <el-button type="primary" size="large" style="width:100%" @click="$router.push('/prices')">
            <el-icon><Search /></el-icon>&nbsp;查询综合单价
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="success" size="large" style="width:100%" @click="$router.push('/text-gen')">
            <el-icon><Document /></el-icon>&nbsp;生成文本
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="warning" size="large" style="width:100%" @click="$router.push('/preview')">
            <el-icon><Files /></el-icon>&nbsp;预览文件
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="info" size="large" style="width:100%" @click="$router.push('/chat')">
            <el-icon><ChatDotRound /></el-icon>&nbsp;问 AI 助手
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 各专业条数 -->
    <el-card shadow="never" class="quick-card">
      <template #header>
        <span>各专业价格条数</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="(count, name) in stats.by_specialty" :key="name" class="specialty-cell">
          <el-tag type="info" size="large" effect="plain">
            {{ name }} : {{ count }}
          </el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- 项目列表 -->
    <el-card shadow="never" class="quick-card">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>最近项目</span>
          <el-button type="primary" size="small" @click="newProjectDialog = true">新建项目</el-button>
        </div>
      </template>
      <el-table :data="projects" stripe empty-text="暂无项目，点击右上角 新建项目">
        <el-table-column prop="name" label="项目名" min-width="200" />
        <el-table-column prop="region" label="地区" width="120" />
        <el-table-column prop="stage" label="阶段" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="newProjectDialog" title="新建项目" width="500">
      <el-form :model="newProject" label-width="100">
        <el-form-item label="项目名" required>
          <el-input v-model="newProject.name" placeholder="例如：某高层住宅 1# 楼估算" />
        </el-form-item>
        <el-form-item label="地区" required>
          <el-select v-model="newProject.region" placeholder="选择项目所在地" style="width:100%">
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { PricesAPI, ProjectsAPI } from '@/api'

const loading = ref(true)
const stats = ref({})
const projects = ref([])
const serverOk = ref(false)
const newProjectDialog = ref(false)
const creating = ref(false)
const newProject = reactive({ name: '', region: '', stage: '估算', note: '' })
const regions = ['北京市', '上海市', '天津市', '重庆市', '广东省', '浙江省', '江苏省', '四川省', '山东省', '湖北省', '湖南省', '福建省', '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省', '安徽省', '江西省', '河南省', '海南省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '内蒙古', '广西', '宁夏', '新疆', '西藏']

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

async function loadStats() {
  try {
 const r = await PricesAPI.stats()
 stats.value = r
 serverOk.value = true
  } catch (e) {
 serverOk.value = false
  } finally {
 loading.value = false
  }
}

async function loadProjects() {
  try {
    projects.value = await ProjectsAPI.list()
  } catch (e) {
    // 项目加载失败不致命，静默
  }
}

async function createProject() {
  if (!newProject.name || !newProject.region || !newProject.stage) {
    ElMessage.warning('请填写完整：名称 / 地区 / 阶段')
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
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadStats()
  loadProjects()
})
</script>

<style scoped>
.workspace { display:flex; flex-direction:column; gap:16px; }

.stat-row { margin-bottom: 0; }

.stat-card {
  position: relative;
  padding: 4px 0;
}
.stat-label { font-size: 14px; color: #909399; }
.stat-value { font-size: 28px; font-weight: bold; margin-top: 8px; color: #303133; }
.stat-value.ok { color: #67c23a; }
.stat-value.err { color: #f56c6c; }
.stat-icon {
  position: absolute;
  right: 0;
  top: 0;
  font-size: 40px;
  opacity: 0.15;
  color: #409eff;
}

.quick-card { margin-top: 16px; }
.specialty-cell { padding: 6px 0; }
</style>
