<template>
  <div class="text-gen-page">
    <el-row :gutter="16">
      <!-- 左侧：模板选择 -->
      <el-col :span="6">
        <el-card shadow="never">
          <template #header><span>8 类格式谱</span></template>
          <el-menu :default-active="String(selectedTypeId)" @select="onSelectType">
            <el-menu-item v-for="t in templateTypes" :key="t.id" :index="String(t.id)">
              <el-icon><Document /></el-icon>
              <span>{{ t.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 中间：字段填写 -->
      <el-col :span="10">
        <el-card shadow="never" v-loading="loading">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ currentTypeName }} - 字段填写</span>
              <el-button size="small" @click="loadFields" :disabled="!selectedTemplate">刷新字段</el-button>
            </div>
          </template>
          <div v-if="!selectedTemplate" class="placeholder">
            <el-empty description="请先在右侧选择一个具体模板" />
          </div>
          <el-form v-else :model="fieldValues" label-width="140" label-position="right">
            <el-form-item
              v-for="f in fields"
              :key="f.field_key"
              :label="f.field_label"
              :required="f.required"
            >
              <el-input
                v-if="f.field_type === 'text'"
                v-model="fieldValues[f.field_key]"
                :placeholder="f.default_value || ''"
              />
              <el-input-number
                v-else-if="f.field_type === 'number'"
                v-model="fieldValues[f.field_key]"
                style="width:100%"
              />
              <el-date-picker
                v-else-if="f.field_type === 'date'"
                v-model="fieldValues[f.field_key]"
                type="date"
                value-format="YYYY-MM-DD"
                style="width:100%"
              />
              <el-select
                v-else-if="f.field_type === 'select'"
                v-model="fieldValues[f.field_key]"
                style="width:100%"
              >
                <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
              </el-select>
              <el-input
                v-else
                v-model="fieldValues[f.field_key]"
                type="textarea"
                :rows="3"
                :placeholder="f.default_value || ''"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：预览与模板列表 -->
      <el-col :span="8">
        <el-card shadow="never" class="preview-card">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>渲染预览</span>
              <div>
                <el-button size="small" type="primary" @click="render" :disabled="!selectedTemplate">渲染</el-button>
                <el-button size="small" @click="exportDocx" :disabled="!rendered">导出 docx</el-button>
              </div>
            </div>
          </template>
          <div v-if="!rendered" class="placeholder">
            <el-empty description="点击 渲染 按钮，生成文档预览" />
          </div>
          <div v-else class="rendered-md" v-html="renderedHtml"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 模板选择列表(底部) -->
    <el-card shadow="never" class="template-list-card">
      <template #header><span>{{ currentTypeName }} - 模板列表</span></template>
      <el-table :data="templates" @row-click="onSelectTemplate" highlight-current-row stripe>
        <el-table-column prop="name" label="模板名" min-width="200" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="启用" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { TemplatesAPI } from '@/api'

const templateTypes = ref([])
const selectedTypeId = ref(null)
const templates = ref([])
const selectedTemplate = ref(null)
const fields = ref([])
const fieldValues = reactive({})
const loading = ref(false)
const rendered = ref(false)
const renderedHtml = ref('')

const currentTypeName = computed(() => {
  const t = templateTypes.value.find((x) => x.id === selectedTypeId.value)
  return t ? t.name : '(未选择)'
})

async function loadTypes() {
  templateTypes.value = await TemplatesAPI.types()
  if (templateTypes.value.length && !selectedTypeId.value) {
    onSelectType(String(templateTypes.value[0].id))
  }
}

async function onSelectType(id) {
  selectedTypeId.value = Number(id)
  templates.value = await TemplatesAPI.list(selectedTypeId.value)
  selectedTemplate.value = null
  fields.value = []
  rendered.value = false
}

async function onSelectTemplate(row) {
  selectedTemplate.value = row
  await loadFields()
}

async function loadFields() {
  if (!selectedTemplate.value) return
  loading.value = true
  try {
    fields.value = await TemplatesAPI.fields(selectedTemplate.value.id)
    // 清空字段值
    Object.keys(fieldValues).forEach((k) => delete fieldValues[k])
    fields.value.forEach((f) => {
      fieldValues[f.field_key] = f.default_value || ''
    })
    rendered.value = false
  } finally {
    loading.value = false
  }
}

async function render() {
  if (!selectedTemplate.value) return
  // MVP 阶段：本地 Markdown 占位替换渲染
  let md = selectedTemplate.value.content_md || ''
  Object.keys(fieldValues).forEach((k) => {
    const v = fieldValues[k] || `__${k}__`
    md = md.replaceAll(`{{${k}}}`, v).replaceAll(`{{ ${k} }}`, v)
  })
  // 转 HTML(简化版;生产用 markdown-it)
  renderedHtml.value = `<pre style="white-space:pre-wrap;font-family:PingFang SC, sans-serif">${escapeHtml(md)}</pre>`
  rendered.value = true
  ElMessage.success('已渲染（MVP 阶段简化）')
}

function escapeHtml(s) {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&', '<': '<', '>': '>' }[c]))
}

async function exportDocx() {
  if (!selectedTemplate.value) {
    ElMessage.warning('请先选择一个模板')
    return
  }
  try {
    const payload = {
      template_id: selectedTemplate.value.id,
      field_values: fieldValues,
    }
    const r = (await import('@/api')).api.post('/v1/templates/render', payload)
    const data = await r
    ElMessage.success(`docx 已生成 (${data.size_kb} KB)`)
    window.open('/api' + data.download_url, '_blank')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadTypes)
</script>

<style scoped>
.text-gen-page { display:flex; flex-direction:column; gap:16px; }
.placeholder { padding:60px 0; text-align:center; }
.rendered-md { max-height:600px; overflow:auto; padding:12px; background:#fafafa; border:1px solid #ebeef5; }
.template-list-card { margin-top:16px; }
</style>
