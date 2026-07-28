<template>
  <el-container class="app-root">
    <!-- 侧边栏导航 -->
    <el-aside class="sidebar" width="220px">
<div class="sidebar-brand">
      <img src="/icon.png" class="brand-icon-img" alt="工程助手" />
      <div class="brand-text">
        <span class="brand-name">工程助手</span>
        <span class="brand-sub">Engineering AI</span>
      </div>
    </div>

      <div class="sidebar-divider"></div>

      <el-menu
        :default-active="activeMenu"
        mode="vertical"
        :collapse="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/workspace">
          <el-icon><HomeFilled /></el-icon>
          <template #title>
            <span class="menu-label">工作台</span>
            <span class="menu-shortcut">Ctrl+1</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/docgen">
          <el-icon><MagicStick /></el-icon>
          <template #title>
<span class="menu-label">文档生成</span>
 <el-tag size="small" type="danger" effect="plain" class="menu-badge">NEW</el-tag>
 <span class="menu-shortcut">Ctrl+5</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/prices">
          <el-icon><TrendCharts /></el-icon>
          <template #title>
            <span class="menu-label">价格库</span>
 <span class="menu-shortcut">Ctrl+3</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/quote">
          <el-icon><Wallet /></el-icon>
          <template #title>
            <span class="menu-label">报价</span>
 <span class="menu-shortcut">Ctrl+4</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/text-gen">
          <el-icon><EditPen /></el-icon>
          <template #title>
            <span class="menu-label">文本编制</span>
 <span class="menu-shortcut">Ctrl+6</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/preview">
          <el-icon><FolderOpened /></el-icon>
          <template #title>
            <span class="menu-label">文件预览</span>
          </template>
        </el-menu-item>
 <el-menu-item index="/chat">
 <el-icon><ChatDotRound /></el-icon>
 <template #title>
 <span class="menu-label">AI 助手</span>
 <span class="menu-shortcut">Ctrl+2</span>
 </template>
 </el-menu-item>
 <el-menu-item index="/settings">
 <el-icon><Setting /></el-icon>
 <template #title><span class="menu-label">AI 配置</span><span class="menu-shortcut">Ctrl+8</span></template>
 </el-menu-item>
 </el-menu>
</el-aside>

 <!-- 主体 -->
    <el-container class="main-area">
      <el-header class="top-bar">
<div class="breadcrumb">
 <el-breadcrumb separator="/">
 <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
 <el-breadcrumb-item>{{ currentPageName }}</el-breadcrumb-item>
 </el-breadcrumb>
 <div class="backend-status" :class="{ online: backendOnline, offline: !backendOnline }">
 <span class="status-dot"></span>
 <span class="status-text">{{ backendOnline ? '已连接' : '断开' }}</span>
 </div>
</div>
        <div class="top-actions">
          <el-button circle size="small" class="action-btn">
            <el-icon><Search /></el-icon>
          </el-button>
          <el-button circle size="small" class="action-btn">
            <el-icon><Bell /></el-icon>
            <el-badge is-dot hidden class="notification-badge"></el-badge>
          </el-button>
          <el-dropdown trigger="click">
            <div class="user-avatar">
              <el-avatar :size="32" class="avatar-circle">U</el-avatar>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- AI 配置守卫 -->
    <AiSetupWizard v-if="!aiConfigured" @configured="aiConfigured = true" />
    <div v-if="aiConfigured === null" class="loading-guard">
      <div class="loading-content">
        <div class="loading-logo">
          <el-icon :size="48" color="#2563eb"><Loading /></el-icon>
        </div>
        <p class="loading-text">正在检查 AI 配置...</p>
      </div>
    </div>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { api, isBackendOnline } from '@/api'
import { useShortcuts } from '@/utils/shortcuts'
import AiSetupWizard from '@/components/AiSetupWizard.vue'

const route = useRoute()
const aiConfigured = ref(null)
const backendOnline = ref(true)
const healthCheckTimer = ref(null)

// 初始化快捷键
const { shortcuts } = useShortcuts()

// 后端健康检查(每 30 秒轮询)
async function checkHealth() {
  try {
    const r = await api.get('/../health')
    backendOnline.value = true
    return r
  } catch {
    backendOnline.value = false
    return null
  }
}

onMounted(async () => {
  // 检查 AI 配置
  try {
    const r = await api.get('/ai/config')
    aiConfigured.value = r?.api_key_set === true
  } catch {
    aiConfigured.value = false
  }

  // 启动健康检查轮询
  await checkHealth()
  healthCheckTimer.value = setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthCheckTimer.value) clearInterval(healthCheckTimer.value)
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/docgen')) return '/docgen'
  if (path.startsWith('/prices')) return '/prices'
  if (path.startsWith('/quote')) return '/quote'
  if (path.startsWith('/text-gen')) return '/text-gen'
  if (path.startsWith('/preview')) return '/preview'
  if (path.startsWith('/chat')) return '/chat'
  if (path.startsWith('/settings')) return '/settings'
  return '/workspace'
})

const pageNameMap = {
  '/workspace': '工作台',
  '/docgen': '文档生成',
  '/prices': '价格库',
  '/quote': '报价',
  '/text-gen': '文本编制',
  '/preview': '文件预览',
  '/chat': 'AI 助手',
  '/settings': '系统设置'
}

const currentPageName = computed(() => {
  let path = route.path
  for (const [prefix, name] of Object.entries(pageNameMap)) {
    if (path.startsWith(prefix)) return name
  }
  return '工作台'
})
</script>

<style>
/* ============================================================
   工程助手 — 全局设计系统
   ============================================================ */

/* ---------- 1. 品牌色板 ---------- */
:root {
  /* 主色系 */
  --brand-900: #0c1929;
  --brand-800: #0f1724;
  --brand-700: #1e3a5f;
  --brand-600: #1d4ed8;
  --brand-500: #2563eb;
  --brand-400: #3b82f6;
  --brand-300: #60a5fa;

  /* 语义色 */
  --success-600: #059669;
  --success-500: #10b981;
  --warning-500: #f59e0b;
  --danger-500: #ef4444;
  --info-500: #6366f1;

  /* 中性色阶 */
  --gray-50:  #f8fafc;
  --gray-100: #f1f5f9;
  --gray-200: #e2e8f0;
  --gray-300: #cbd5e1;
  --gray-400: #94a3b8;
  --gray-500: #64748b;
  --gray-600: #475569;
  --gray-700: #334155;
  --gray-800: #1e293b;
  --gray-900: #0f172a;

  /* 背景 */
  --bg-base: var(--gray-50);
  --bg-surface: #ffffff;
  --bg-sidebar: var(--brand-900);
  --bg-topbar: var(--brand-800);

  /* 文字 */
  --text-primary:   var(--gray-900);
  --text-secondary: var(--gray-600);
  --text-tertiary:  var(--gray-400);
  --text-inverse:   #f1f5f9;

  /* 圆角 */
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* 阴影 */
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.08), 0 4px 10px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 40px rgba(0,0,0,0.12);
  --shadow-brand: 0 4px 14px rgba(37,99,235,0.25);

  /* 间距 */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* 字号 */
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 15px;
  --text-lg: 16px;
  --text-xl: 18px;
  --text-2xl: 22px;
  --text-3xl: 28px;

  /* 过渡 */
  --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  /* 侧边栏 */
  --sidebar-width: 220px;
  --topbar-height: 52px;
}

/* ---------- 2. 基础重置 ---------- */
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

*, *::before, *::after {
  box-sizing: border-box;
}

/* ---------- 3. 全局滚动条 ---------- */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--gray-300); border-radius: var(--radius-full); }
::-webkit-scrollbar-thumb:hover { background: var(--gray-400); }

/* ---------- 4. 布局结构 ---------- */
.app-root {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  z-index: 10;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  margin-top: var(--space-1);
}

.brand-icon-img {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  object-fit: contain;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.brand-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--text-inverse);
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.brand-sub {
  font-size: var(--text-xs);
  color: var(--gray-400);
  letter-spacing: 1px;
  text-transform: uppercase;
  line-height: 1.2;
}

.sidebar-divider {
  height: 1px;
  background: rgba(255,255,255,0.08);
  margin: var(--space-2) var(--space-4);
}

.sidebar-menu {
  flex: 1;
  border: none !important;
  background: transparent;
  overflow-y: auto;
  padding: var(--space-2) 0;
}

.sidebar-menu .el-menu-item,
.sidebar-footer .el-menu-item {
  color: var(--gray-400);
  height: 42px;
  line-height: 42px;
  margin: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  position: relative;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-footer .el-menu-item:hover {
  color: var(--text-inverse);
  background: rgba(255,255,255,0.06);
}

.sidebar-menu .el-menu-item.is-active {
  color: #fff !important;
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500)) !important;
  box-shadow: var(--shadow-brand);
  border-radius: var(--radius-sm);
}

.sidebar-menu .el-menu-item .el-icon {
  color: inherit;
  font-size: 18px;
  margin-right: var(--space-3);
  width: 20px;
  text-align: center;
}

.menu-label {
  font-size: var(--text-sm);
  font-weight: 500;
}
.menu-shortcut {
  font-size: 11px;
  color: var(--text-tertiary, #999);
  margin-left: auto;
  padding-left: 8px;
  opacity: 0.6;
  font-family: monospace;
}
.el-menu-item:hover .menu-shortcut {
  opacity: 1;
}

.menu-badge {
  margin-left: auto;
  font-size: 10px;
  padding: 0 6px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.menu-dot {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
}

.active-dot {
  background: var(--success-500);
  box-shadow: 0 0 6px rgba(16,185,129,0.5);
}

.chat-dot {
  background: var(--brand-400);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: translateY(-50%) scale(1); }
  50% { opacity: 0.6; transform: translateY(-50%) scale(0.8); }
}

.sidebar-footer {
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: var(--space-2) 0;
}

/* ---------- 5. 顶栏 ---------- */
.main-area {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: var(--topbar-height) !important;
  min-height: var(--topbar-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.breadcrumb {
 display: flex;
 align-items: center;
}

.backend-status {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 16px;
  font-size: 12px;
  font-family: monospace;
}
.backend-status .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.backend-status.online .status-dot {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34,197,94,0.4);
}
.backend-status.offline .status-dot {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239,68,68,0.4);
  animation: pulse 1.5s infinite;
}
.backend-status .status-text {
  color: var(--text-tertiary, #999);
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  color: var(--gray-500);
  font-size: var(--text-sm);
}

.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--text-primary);
  font-weight: 500;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.action-btn {
  color: var(--gray-500);
  border: none;
}

.action-btn:hover {
  color: var(--brand-500);
  background: var(--gray-100);
}

.notification-badge {
  top: 4px;
  right: 4px;
}

.user-avatar {
  cursor: pointer;
  margin-left: var(--space-2);
}

.avatar-circle {
  background: linear-gradient(135deg, var(--brand-500), var(--brand-400));
  color: #fff;
  font-weight: 600;
  font-size: var(--text-sm);
}

/* ---------- 6. 主内容区 ---------- */
.app-main {
  flex: 1;
  padding: var(--space-6);
  background: var(--bg-base);
  overflow-y: auto;
  overflow-x: hidden;
}

/* ---------- 7. 页面过渡动画 ---------- */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all var(--transition-base);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ---------- 8. Element Plus 全局覆盖 ---------- */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--gray-200) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all var(--transition-base);
}

.el-card:hover {
  box-shadow: var(--shadow-md) !important;
}

.el-card__body {
  padding: var(--space-5) !important;
}

.el-table {
  border-radius: var(--radius-lg) !important;
  overflow: hidden;
}

.el-table th.el-table__cell {
  background: var(--gray-100) !important;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: var(--text-sm);
}

.el-table td.el-table__cell {
  font-size: var(--text-sm);
}

.el-tag {
  border-radius: var(--radius-sm) !important;
  font-weight: 500;
}

.el-button {
  border-radius: var(--radius-sm) !important;
  font-weight: 500;
}

.el-button--primary {
  background: var(--brand-500) !important;
  border-color: var(--brand-500) !important;
  box-shadow: var(--shadow-brand);
}

.el-button--primary:hover {
  background: var(--brand-600) !important;
  border-color: var(--brand-600) !important;
}

.el-dialog {
  border-radius: var(--radius-xl) !important;
}

.el-dialog__header {
  border-bottom: 1px solid var(--gray-200);
  padding: var(--space-5) var(--space-6) !important;
}

.el-dialog__body {
  padding: var(--space-6) !important;
}

.el-form-item__label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.el-input__inner {
  border-radius: var(--radius-sm) !important;
}

.el-select {
  width: 100%;
}

.el-empty__description p {
  font-size: var(--text-md);
  color: var(--text-tertiary);
}

/* ---------- 9. 加载/守卫 ---------- */
.loading-guard {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: linear-gradient(135deg, var(--brand-900), var(--brand-700));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
  color: var(--gray-300);
}

.loading-logo {
  margin-bottom: var(--space-6);
}

.loading-text {
  margin-top: var(--space-4);
  font-size: var(--text-md);
  letter-spacing: 1px;
}

/* 全局组件级过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-base);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>