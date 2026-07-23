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
          <el-button type="primary" @click="doSearch" :loading="loading">查询</el-button>
          <el-button @click="loadList">显示全部</el-button>
          <el-tag type="info" effect="plain" class="result-tag">{{ results.length }} 条</el-tag>
        </div>
        <el-table :data="results" v-loading="loading" stripe height="calc(100vh - 220px)" class="price-table">
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
          <el-button @click="loadTopics">查询</el-button>
          <el-tag type="info" class="result-tag">{{ topicResults.length }} 条</el-tag>
        </div>
        <el-table :data="topicResults" stripe height="calc(100vh - 220px)" class="price-table">
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
          <el-button @click="loadFees">查询</el-button>
          <el-tag type="info" class="result-tag">{{ feeRates.length }} 条</el-tag>
        </div>
        <el-table :data="feeRates" stripe height="calc(100vh - 220px)" class="price-table">
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
import { PricesAPI, FeesAPI } from '@/api'

const activeTab = ref('search')
const keyword = ref('')
const results = ref([])
const loading = ref(false)

const topics = ['管道铺设与修复', '深基坑开挖与支护', '钢板桩', '降水工程', '桩基与地基处理']
const topicFilter = ref('')
const topicResults = ref([])

const feeRegions = ['全国', '北京市', '上海市', '天津市', '重庆市', '广东省', '浙江省', '江苏省']
const feeRegion = ref('')
const feeType = ref('')
const feeRates = ref([])

async function doSearch() {
  if (!keyword.value.trim()) { return loadList() }
  loading.value = true
  try { results.value = await PricesAPI.search(keyword.value.trim()) }
  finally { loading.value = false }
}

async function loadList() {
  loading.value = true
  try { results.value = await PricesAPI.list({ limit: 200 }) }
  finally { loading.value = false }
}

async function loadTopics() {
  topicResults.value = await PricesAPI.topics(topicFilter.value)
}

async function loadFees() {
  const params = {}
  if (feeRegion.value) params.region = feeRegion.value
  if (feeType.value) params.fee_type = feeType.value
  feeRates.value = await FeesAPI.list(params)
}

onMounted(() => { loadList(); loadTopics(); loadFees() })
</script>

<style scoped>
.prices-page { background:#fff; border-radius:8px; }
.prices-tabs { border-radius:8px; }
.search-bar { display:flex; gap:10px; align-items:center; margin-bottom:14px; flex-wrap:wrap; }
.search-input { flex:1; min-width:280px; }
.result-tag { flex-shrink:0; }
.price-table { width:100%; }
</style>