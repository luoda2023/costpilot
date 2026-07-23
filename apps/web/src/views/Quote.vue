<template>
  <div class="quote-page">
    <el-row :gutter="16">
      <!-- 左侧：工程量 -->
      <el-col :span="16">
        <el-card shadow="never" class="quote-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">工程量清单</span>
              <div class="header-actions">
                <el-button size="small" @click="addEmptyRow">+ 添加行</el-button>
                <el-button size="small" @click="fillFromPriceSearch">从价格库匹配</el-button>
                <el-button size="small" type="danger" @click="clearRows" :disabled="!rows.length">清空</el-button>
              </div>
            </div>
          </template>

          <el-form :inline="true" :model="projectInfo" class="proj-form" size="small">
            <el-form-item label="项目名">
              <el-input v-model="projectInfo.name" style="width:200px" />
            </el-form-item>
            <el-form-item label="地区">
              <el-select v-model="projectInfo.region" filterable style="width:140px">
                <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
              </el-select>
            </el-form-item>
            <el-form-item label="阶段">
              <el-radio-group v-model="projectInfo.stage">
                <el-radio-button value="估算">估算</el-radio-button>
                <el-radio-button value="概算">概算</el-radio-button>
                <el-radio-button value="预算">预算</el-radio-button>
                <el-radio-button value="结算">结算</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="计税">
              <el-radio-group v-model="projectInfo.tax_method">
                <el-radio-button value="一般计税">一般计税9%</el-radio-button>
                <el-radio-button value="简易计税">简易计税3%</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>

          <el-table :data="rows" border size="small" max-height="480">
            <el-table-column type="index" width="40" />
            <el-table-column label="项目名称" min-width="200">
              <template #default="{ row }"><el-input v-model="row.item_name" placeholder="例:C30 商品混凝土" size="small" /></template>
            </el-table-column>
            <el-table-column label="专业" width="120">
              <template #default="{ row }">
                <el-select v-model="row.specialty" filterable size="small">
                  <el-option v-for="s in specialties" :key="s.name" :label="s.name" :value="s.name" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="单位" width="70">
              <template #default="{ row }"><el-input v-model="row.unit" placeholder="m³" size="small" /></template>
            </el-table-column>
            <el-table-column label="工程量" width="100">
              <template #default="{ row }"><el-input-number v-model="row.qty" :min="0" :precision="2" :controls="false" size="small" style="width:100%" /></template>
            </el-table-column>
            <el-table-column label="单价" width="120">
              <template #default="{ row }"><el-input-number v-model="row.price" :min="0" :precision="2" :controls="false" size="small" style="width:100%" /></template>
            </el-table-column>
            <el-table-column label="合价" width="110">
              <template #default="{ row }">¥ {{ (row.qty * row.price).toLocaleString('zh-CN', {maximumFractionDigits:2}) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="60">
              <template #default="{ $index }"><el-button size="small" type="danger" link @click="rows.splice($index, 1)">删除</el-button></template>
            </el-table-column>
          </el-table>
          <div v-if="!rows.length" class="empty-tip"><el-empty description="点击 + 添加行 或 从价格库匹配" :image-size="50" /></div>
        </el-card>
      </el-col>

      <!-- 右侧：报价结果 -->
      <el-col :span="8">
        <el-card shadow="never" class="result-card">
          <template #header><span class="card-title">报价结果</span></template>
          <div v-if="!result" class="placeholder"><el-empty description="填写工程量后生成报价" :image-size="50" /></div>
          <div v-else class="result-body">
            <div class="result-block">
              <div class="result-label">一类(分部分项)</div>
              <div class="result-value">¥ {{ result.category1.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}</div>
            </div>
            <div class="result-block">
              <div class="result-label">二类(措施费)</div>
              <div class="result-value">¥ {{ result.category2.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}</div>
              <el-collapse class="sub-collapse">
                <el-collapse-item v-for="(v, k) in result.category2_detail" :key="k" :title="k">
                  ¥ {{ v.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}
                </el-collapse-item>
              </el-collapse>
            </div>
            <div class="result-block">
              <div class="result-label">三类(规费+税金)</div>
              <div class="result-value">¥ {{ result.category3.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}</div>
              <el-collapse class="sub-collapse">
                <el-collapse-item v-for="(v, k) in result.category3_detail" :key="k" :title="k">
                  ¥ {{ v.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}
                </el-collapse-item>
              </el-collapse>
            </div>
            <el-divider />
            <div class="result-block grand">
              <div class="result-label">工程总造价</div>
              <div class="result-value">¥ {{ result.grand_total.toLocaleString('zh-CN', {maximumFractionDigits:2}) }}</div>
            </div>
          </div>
          <div class="action-bar">
            <el-button type="primary" @click="compose" :loading="composing" :disabled="!rows.length" style="width:100%">生成报价</el-button>
            <div class="sub-actions">
              <el-button @click="exportExcel" :loading="exportingX" :disabled="!result" size="small">导出 Excel</el-button>
              <el-button @click="exportWord" :loading="exportingW" :disabled="!result" size="small">导出 Word</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 价格匹配对话框 -->
    <el-dialog v-model="searchDialog" title="从价格库匹配" width="800" :close-on-click-modal="false">
      <div class="dialog-search">
        <el-input v-model="searchKw" placeholder="关键词：钢板桩、防火门、C30..." style="flex:1" @keyup.enter="doSearch" size="small">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button @click="doSearch" size="small">查询</el-button>
      </div>
      <el-table :data="searchResults" max-height="400" @row-dblclick="addFromSearch" size="small">
        <el-table-column prop="specialty" label="专业" width="90" />
        <el-table-column prop="item_name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column prop="price" label="综合单价" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }"><el-button size="small" type="primary" link @click="addFromSearch(row)">加入</el-button></template>
        </el-table-column>
      </el-table>
      <div class="dialog-hint">双击行也可快速加入</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, PricesAPI } from '@/api'

const regions = ['北京市','上海市','天津市','重庆市','广东省','浙江省','江苏省','四川省','山东省','湖北省','湖南省','福建省','河北省','河南省','安徽省','江西省']
const specialties = ref([])
const projectInfo = reactive({ name: '未命名项目', region: '北京市', stage: '预算', tax_method: '一般计税' })
const rows = ref([{ item_name: '', specialty: '', unit: 'm³', qty: 0, price: 0 }])
const result = ref(null)
const composing = ref(false); const exportingX = ref(false); const exportingW = ref(false)
const searchDialog = ref(false); const searchKw = ref(''); const searchResults = ref([])

function addEmptyRow() { rows.value.push({ item_name: '', specialty: '', unit: '', qty: 0, price: 0 }) }
function clearRows() {
  ElMessageBox.confirm('确定清空所有工程量?', '提示', { type: 'warning' }).then(() => { rows.value = []; result.value = null }).catch(() => {})
}
function fillFromPriceSearch() { searchDialog.value = true; if (!searchResults.value.length) doSearch() }
async function doSearch() {
  if (!searchKw.value.trim()) { ElMessage.warning('请输入关键词'); return }
  try { searchResults.value = await PricesAPI.search(searchKw.value.trim(), 30) }
  catch { ElMessage.error('查询失败') }
}
function addFromSearch(row) {
  rows.value.push({ item_name: row.item_name, specialty: row.specialty || '', unit: row.unit, qty: 1, price: parseFloat(row.price.split(' ')[0]) || 0 })
  ElMessage.success(`已加入: ${row.item_name}`)
}
async function compose() {
  if (rows.value.some(r => !r.item_name || r.qty <= 0)) { ElMessage.warning('请完善项目名和工程量'); return }
  composing.value = true
  try {
    result.value = await api.post('/v1/quotes/compose', {
      items: rows.value.map(r => ({ item_name: r.item_name, unit: r.unit, qty: r.qty, price: r.price, specialty: r.specialty, remark: r.remark || null })),
      region: projectInfo.region, stage: projectInfo.stage, tax_method: projectInfo.tax_method,
    })
    ElMessage.success(`组价完成: ¥ ${result.value.grand_total.toLocaleString('zh-CN')}`)
  } catch (e) { ElMessage.error('组价失败: ' + (e.response?.data?.detail || e.message)) }
  finally { composing.value = false }
}
async function exportExcel() {
  exportingX.value = true
  try {
    const r = await api.post('/v1/quotes/export/excel', { items: rows.value.map(r => ({ item_name: r.item_name, unit: r.unit, qty: r.qty, price: r.price, specialty: r.specialty, remark: r.remark || null })), project_info: { ...projectInfo } })
    ElMessage.success(`Excel 已生成 (${r.size_kb} KB)`); window.open('/api' + r.download_url, '_blank')
  } catch { ElMessage.error('导出失败') } finally { exportingX.value = false }
}
async function exportWord() {
  exportingW.value = true
  try {
    const r = await api.post('/v1/quotes/export/word', { items: rows.value.map(r => ({ item_name: r.item_name, unit: r.unit, qty: r.qty, price: r.price, specialty: r.specialty, remark: r.remark || null })), project_info: { ...projectInfo } })
    ElMessage.success(`Word 已生成 (${r.size_kb} KB)`); window.open('/api' + r.download_url, '_blank')
  } catch { ElMessage.error('导出失败') } finally { exportingW.value = false }
}
async function loadSpecialties() { try { specialties.value = await PricesAPI.specialties() } catch {} }
onMounted(loadSpecialties)
</script>

<style scoped>
.quote-page { background:#fff; border-radius:8px; }
.quote-card { border-radius:8px; margin-bottom:0; }
.result-card { border-radius:8px; }
.card-header { display:flex; justify-content:space-between; align-items:center; }
.card-title { font-size:15px; font-weight:600; color:#303133; }
.header-actions { display:flex; gap:6px; }
.proj-form { margin-bottom:10px; padding:8px; background:#fafafa; border-radius:6px; }
.empty-tip { padding:20px 0; }
.placeholder { padding:60px 0; text-align:center; }
.result-body { padding:0 4px; }
.result-block { margin-bottom:14px; }
.result-label { font-size:13px; color:#606266; }
.result-value { font-size:17px; font-weight:700; color:#303133; margin-top:2px; }
.result-block.grand .result-label { font-size:14px; color:#409eff; }
.result-block.grand .result-value { font-size:22px; color:#f56c6c; }
.sub-collapse { margin-top:2px; }
.action-bar { margin-top:12px; display:flex; flex-direction:column; gap:8px; }
.sub-actions { display:flex; gap:8px; }
.sub-actions .el-button { flex:1; }
.dialog-search { display:flex; gap:8px; margin-bottom:12px; }
.dialog-hint { color:#909399; font-size:12px; margin-top:8px; }
</style>