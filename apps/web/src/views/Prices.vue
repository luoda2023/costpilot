<template>
  <div class="prices-page">
    <el-tabs v-model="activeTab" type="border-card" class="prices-tabs">
      <!-- 综合单价查询 -->
      <el-tab-pane label="综合单价查询" name="search">
<div class="search-bar">
  <el-input
    v-model="keyword"
    placeholder="输入项目名搜索，如：钢板桩、防火门、C30混凝土..."
    clearable
    @keyup.enter="doSearch"
    class="search-input"
  >
    <template #prefix><el-icon><Search /></el-icon></template>
  </el-input>
  <el-select v-model="filterSpecialty" placeholder="专业" clearable style="width:140px">
    <el-option v-for="s in specialties" :key="s.name" :label="s.name" :value="s.name" />
  </el-select>
  <el-select v-model="filterUnit" placeholder="单位" clearable style="width:100px">
    <el-option v-for="u in units" :key="u" :label="u" :value="u" />
  </el-select>
  <el-button type="primary" @click="doSearch" :loading="loading">查询</el-button>
  <el-button @click="loadList" :disabled="loading">显示全部</el-button>
  <el-button type="success" @click="triggerAiImport" :loading="aiImporting" size="small">AI 导入价格</el-button>
  <el-tag type="info" effect="plain" class="result-tag">{{ results.length }} 条</el-tag>
  <input ref="fileInputRef" type="file" accept=".xlsx,.xls,.csv" style="display:none" @change="onAiImportFile" />
</div>
        <el-table :data="results" v-loading="loading" stripe height="calc(100vh - 220px)" class="price-table" empty-text="暂无数据，请点击查询或显示全部">
          <el-table-column prop="specialty" label="专业" width="100" />
          <el-table-column prop="item_name" label="项目名称" min-width="240" show-overflow-tooltip />
          <el-table-column prop="unit" label="单位" width="70" />
          <el-table-column prop="price" label="综合单价" min-width="200" show-overflow-tooltip />
          <el-table-column prop="region" label="地区" width="90" />
          <el-table-column prop="source_file" label="来源" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <!-- 市政专题 -->
      <el-tab-pane label="市政专题" name="topics">
        <div class="search-bar">
          <el-select v-model="topicFilter" placeholder="选择专题" clearable style="width:220px">
            <el-option v-for="t in topics" :key="t" :label="t" :value="t" />
          </el-select>
          <el-button @click="loadTopics" :loading="topicLoading">查询</el-button>
          <el-tag type="info" class="result-tag">{{ topicResults.length }} 条</el-tag>
        </div>
        <el-table :data="topicResults" v-loading="topicLoading" stripe height="calc(100vh - 220px)" class="price-table" empty-text="暂无数据">
          <el-table-column prop="topic" label="专题" width="160" />
          <el-table-column prop="item_name" label="项目名称" min-width="240" show-overflow-tooltip />
          <el-table-column prop="unit" label="单位" width="70" />
          <el-table-column prop="price" label="综合单价" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source_file" label="来源" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <!-- 费率表 -->
      <el-tab-pane label="规费/措施费/税金" name="fees">
        <div class="search-bar">
          <el-select v-model="feeRegion" placeholder="选择地区" clearable style="width:160px">
            <el-option v-for="r in feeRegions" :key="r" :label="r" :value="r" />
          </el-select>
          <el-select v-model="feeType" placeholder="费用类型" clearable style="width:140px">
            <el-option label="税金" value="税金" />
            <el-option label="规费" value="规费" />
            <el-option label="措施费" value="措施费" />
          </el-select>
          <el-button @click="loadFees" :loading="feeLoading">查询</el-button>
          <el-tag type="info" class="result-tag">{{ feeRates.length }} 条</el-tag>
        </div>
        <el-table :data="feeRates" v-loading="feeLoading" stripe height="calc(100vh - 220px)" class="price-table" empty-text="暂无数据">
          <el-table-column prop="region" label="地区" width="100" />
          <el-table-column prop="fee_type" label="类型" width="90" />
          <el-table-column prop="fee_subitem" label="子项" min-width="200" />
          <el-table-column label="费率" width="100">
            <template #default="{ row }">
              <el-tag :type="row.fee_type === '税金' ? 'danger' : row.fee_type === '规费' ? 'warning' : 'success'" size="small">
                {{ (row.rate * 100).toFixed(2) }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="calc_base" label="计算基数" min-width="200" />
          <el-table-column prop="source_file" label="来源" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { PricesAPI, FeesAPI, api } from '@/api'
import * as XLSX from 'xlsx'

const activeTab = ref('search')
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const specialties = ref([])
const units = ref([])
const filterSpecialty = ref('')
const filterUnit = ref('')

const topics = ['管道铺设与修复', '深基坑开挖与支护', '钢板桩', '降水工程', '桩基与地基处理']
const topicFilter = ref('')
const topicResults = ref([])
const topicLoading = ref(false)

const feeRegions = ['全国', '北京市', '上海市', '天津市', '重庆市', '广东省', '浙江省', '江苏省']
const feeRegion = ref('')
const feeType = ref('')
const feeRates = ref([])
const feeLoading = ref(false)
const aiImporting = ref(false)
const fileInputRef = ref(null)

async function doSearch() {
  if (!keyword.value.trim() && !filterSpecialty.value && !filterUnit.value) { return loadList() }
  loading.value = true
  try { results.value = await PricesAPI.search(keyword.value.trim(), filterSpecialty.value || undefined, filterUnit.value || undefined) }
  catch { results.value = [] }
  finally { loading.value = false }
}

async function loadList() {
  loading.value = true
  try { results.value = await PricesAPI.list({ limit: 200, specialty: filterSpecialty.value || undefined, unit: filterUnit.value || undefined }) }
  catch { results.value = [] }
  finally { loading.value = false }
}

async function loadTopics() {
  topicLoading.value = true
  try { topicResults.value = await PricesAPI.topics(topicFilter.value) }
  catch { topicResults.value = [] }
  finally { topicLoading.value = false }
}

async function loadFees() {
  feeLoading.value = true
  const params = {}
  if (feeRegion.value) params.region = feeRegion.value
  if (feeType.value) params.fee_type = feeType.value
  try { feeRates.value = await FeesAPI.list(params) }
  catch { feeRates.value = [] }
  finally { feeLoading.value = false }
}

async function loadSpecialties() {
  try { specialties.value = await PricesAPI.specialties() } catch {}
  try {
 const all = await PricesAPI.list({ limit: 500 })
 units.value = [...new Set(all.map(x => x.unit).filter(Boolean))].sort()
  } catch {}
}

function triggerAiImport() { fileInputRef.value?.click() }

async function onAiImportFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  aiImporting.value = true
  try {
 const data = await file.arrayBuffer()
 const wb = XLSX.read(data, { type: 'array' })
 const ws = wb.Sheets[wb.SheetNames[0]]
 const json = XLSX.utils.sheet_to_json(ws, { defval: '' })
 if (!json.length) { ElMessage.warning('文件为空，请检查'); return }

 // 转文本让 AI 理解
 const headers = Object.keys(json[0]).join(',')
 const sampleRows = json.slice(0, 20).map(r => Object.values(r).join(',')).join('\n')
 const tableText = `表头: ${headers}\n数据:\n${sampleRows}`

 ElMessage.info('AI 正在理解表格...')
 const parsed = await api.post('/v1/ai/parse-table', {
 content: tableText,
 source_type: 'auto',
 target_fields: ['item_name', 'specialty', 'unit', 'qty', 'price'],
 })

 if (!parsed.rows || !parsed.rows.length) {
 ElMessage.warning('AI 未能解析表格数据')
 return
 }

 // 提取价格数据
 const prices = parsed.rows
 .filter(r => r.item_name && r.price)
 .map(r => ({
 item_name: r.item_name,
 specialty: r.specialty || '',
 unit: r.unit || '',
 price: r.price,
 region: '',
 source_file: 'AI 智能导入',
 }))

 if (!prices.length) { ElMessage.warning('AI 未识别到价格数据'); return }

 // 将价格追加到显示列表
 results.value.unshift(...prices)
 ElMessage.success(`AI 识别完成，导入 ${prices.length} 条价格`)
  } catch (err) {
 ElMessage.error('AI 导入失败: ' + (err.message || '格式错误'))
  } finally {
 aiImporting.value = false
 e.target.value = ''
  }
}

onMounted(() => { loadList(); loadTopics(); loadFees(); loadSpecialties() })
</script>

<style scoped>
.prices-page { background:#fff; border-radius:8px; }
.prices-tabs { border-radius:8px; }
.prices-tabs :deep(.el-tabs__item) { font-size:14px; line-height:1.5; }
.search-bar { display:flex; gap:10px; align-items:center; margin-bottom:14px; flex-wrap:wrap; }
.search-input { flex:1; min-width:280px; }
.result-tag { flex-shrink:0; }
.price-table { width:100%; }
</style>