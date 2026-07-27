<template>
  <div class="textgen-page">
    <el-row :gutter="16">
      <!-- 左侧：模板选择 -->
      <el-col :span="5">
        <el-card shadow="never" class="side-card">
          <template #header><span class="card-title">格式谱</span></template>
          <el-menu :default-active="String(selectedTypeId)" @select="onSelectType" class="type-menu">
            <el-menu-item v-for="t in templateTypes" :key="t.id" :index="String(t.id)">
              <el-icon><Document /></el-icon>
              <span>{{ t.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-card>
        <el-card shadow="never" class="side-card" style="margin-top:12px">
          <template #header><span class="card-title">模板列表</span></template>
<el-table :data="templates" v-loading="loadingTemplates" @row-click="onSelectTemplate" highlight-current-row stripe size="small" empty-text="该分类暂无模板">
  <el-table-column prop="name" label="模板名" min-width="120" show-overflow-tooltip />
  <el-table-column label="启用" width="56">
    <template #default="{ row }">
      <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag>
    </template>
  </el-table-column>
</el-table>
        </el-card>
      </el-col>

      <!-- 中间：字段填写 -->
      <el-col :span="10">
        <el-card shadow="never" v-loading="loading" class="main-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ currentTypeName }}</span>
              <el-button size="small" @click="loadFields" :disabled="!selectedTemplate">刷新字段</el-button>
            </div>
          </template>
<div v-if="!selectedTemplate" class="placeholder">
 <el-empty description="请先在左侧选择一个模板" :image-size="60" />
 </div>
 <div v-else>
 <!-- AI 智能填充 -->
 <div class="ai-fill-bar">
 <el-input
 v-model="aiDescription"
 placeholder="输入一句话描述，AI 自动填充所有字段，如：某高层住宅 1# 楼，建筑面积 12000㎡，框架结构"
 size="small"
 clearable
 @keyup.enter="aiFill"
 >
 <template #prefix><el-icon :size="14"><MagicStick /></el-icon></template>
 </el-input>
 <el-button type="primary" size="small" @click="aiFill" :loading="aiFilling" :disabled="!aiDescription.trim()">
 AI 填充
 </el-button>
</div>
	 <el-form :model="fieldValues" label-width="140" label-position="right" size="small">
<el-form-item v-for="f in fields" :key="f.field_key" :label="f.field_label" :required="f.required">
              <el-input v-if="f.field_type === 'text'" v-model="fieldValues[f.field_key]" :placeholder="f.default_value || ''" />
              <el-input-number v-else-if="f.field_type === 'number'" v-model="fieldValues[f.field_key]" style="width:100%" />
              <el-date-picker v-else-if="f.field_type === 'date'" v-model="fieldValues[f.field_key]" type="date" value-format="YYYY-MM-DD" style="width:100%" />
              <el-select v-else-if="f.field_type === 'select'" v-model="fieldValues[f.field_key]" style="width:100%">
                <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
              </el-select>
              <el-input v-else v-model="fieldValues[f.field_key]" type="textarea" :rows="3" :placeholder="f.default_value || ''" />
</el-form-item>
 </el-form>
 </div>
 </el-card>
      </el-col>

      <!-- 右侧：预览 -->
      <el-col :span="9">
        <el-card shadow="never" class="main-card">
<template #header>
  <div class="card-header">
    <span class="card-title">预览</span>
    <div>
      <el-button size="small" type="primary" @click="render" :disabled="!selectedTemplate" :loading="rendering">渲染</el-button>
      <el-button size="small" @click="copyRendered" :disabled="!rendered" :icon="DocumentCopy">复制文本</el-button>
      <el-button size="small" @click="exportDocx" :disabled="!rendered">导出 docx</el-button>
    </div>
  </div>
</template>
          <div v-if="!rendered" class="placeholder">
            <el-empty description="点击渲染生成预览" :image-size="60" />
          </div>
          <div v-else class="rendered-md" v-html="renderedHtml"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { TemplatesAPI, api } from '@/api'

const templateTypes = ref([])
  const selectedTypeId = ref(null)
  const templates = ref([])
  const selectedTemplate = ref(null)
  const fields = ref([])
  const fieldValues = reactive({})
  const loading = ref(false)
  const loadingTemplates = ref(false)
  const rendering = ref(false)
  const rendered = ref(false)
  const renderedHtml = ref('')
  const aiFilling = ref(false)
  const aiDescription = ref('')

const currentTypeName = computed(() => {
  const t = templateTypes.value.find(x => x.id === selectedTypeId.value)
  return t ? t.name : '(未选择)'
})

async function loadTypes() {
  templateTypes.value = await TemplatesAPI.types()
  if (templateTypes.value.length && !selectedTypeId.value) onSelectType(String(templateTypes.value[0].id))
}
async function onSelectType(id) {
  selectedTypeId.value = Number(id)
  loadingTemplates.value = true
  try { templates.value = await TemplatesAPI.list(selectedTypeId.value) }
  finally { loadingTemplates.value = false }
  selectedTemplate.value = null; fields.value = []; rendered.value = false
}
async function onSelectTemplate(row) {
  selectedTemplate.value = row; await loadFields()
}
async function loadFields() {
  if (!selectedTemplate.value) return
  loading.value = true
  try {
    fields.value = await TemplatesAPI.fields(selectedTemplate.value.id)
    Object.keys(fieldValues).forEach(k => delete fieldValues[k])
    fields.value.forEach(f => { fieldValues[f.field_key] = f.default_value || '' })
    rendered.value = false
  } finally { loading.value = false }
}
async function render() {
  if (!selectedTemplate.value) return
  rendering.value = true
  try {
    let md = selectedTemplate.value.content_md || ''
    Object.keys(fieldValues).forEach(k => {
      const v = fieldValues[k] || `__${k}__`
      md = md.replaceAll(`{{${k}}}`, v).replaceAll(`{{ ${k} }}`, v)
    })
    renderedHtml.value = `<pre style="white-space:pre-wrap;font-family:PingFang SC, sans-serif;font-size:13px;line-height:1.8">${escapeHtml(md)}</pre>`
    rendered.value = true
  } finally { rendering.value = false }
}
function escapeHtml(s) { return s.replace(/[&<>]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;' }[c])) }
  function copyRendered() { navigator.clipboard.writeText(renderedHtml.value.replace(/<[^>]+>/g,'')).then(() => ElMessage.success('已复制')) }

async function aiFill() {
  if (!selectedTemplate.value || !aiDescription.value.trim()) return
  aiFilling.value = true
  try {
 const result = await api.post('/ai/fill-fields', {
 fields: fields.value.map(f => ({
 field_key: f.field_key,
 field_label: f.field_label,
 field_type: f.field_type || 'text',
 default_value: f.default_value || '',
 required: f.required || false,
 })),
 description: aiDescription.value.trim(),
 })
 // 填充返回值
 Object.entries(result.values || {}).forEach(([k, v]) => {
 if (fieldValues[k] !== undefined) fieldValues[k] = v
 })
 ElMessage.success('AI 已自动填充字段，请检查并调整')
  } catch (e) {
 ElMessage.error('AI 填充失败: ' + (e.response?.data?.detail || e.message))
  } finally { aiFilling.value = false }
}

async function exportDocx() {
  if (!selectedTemplate.value) { ElMessage.warning('请先选择模板'); return }
  try {
    const payload = { template_id: selectedTemplate.value.id, field_values: fieldValues }
    const r = await (await import('@/api')).api.post('/templates/render', payload)
    ElMessage.success(`docx 已生成 (${r.size_kb} KB)`)
    window.open('/api' + r.download_url, '_blank')
  } catch (e) { ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message)) }
}
onMounted(loadTypes)
</script>

<style scoped>
.textgen-page { background: var(--bg-self); border-radius:8px; padding:8px; }
.side-card { border-radius:8px; }
.main-card { border-radius:8px; }
.card-title { font-size:15px; font-weight:600; color: var(--text-primary); line-height:1.5; }
.card-header { display:flex; justify-content:space-between; align-items:center; }
.type-menu { border-right:none; }
.placeholder { padding:60px 0; text-align:center; }
.rendered-md { max-height:600px; overflow:auto; padding:12px; background: var(--gray-50); border: 1 solid var(--gray-200); border-radius:4px; font-size:14px; line-height:1.6; }
</style>