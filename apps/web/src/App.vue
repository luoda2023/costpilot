<template>
  <el-container class="app-container">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="logo">
        <el-icon :size="24"><Coin /></el-icon>
        <span>造价通 CostPilot</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        router
        class="top-menu"
      >
        <el-menu-item index="/workspace">
          <el-icon><HomeFilled /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/prices">
          <el-icon><PriceTag /></el-icon>
          <span>价格库</span>
        </el-menu-item>
        <el-menu-item index="/quote">
          <el-icon><Coin /></el-icon>
          <span>报价生成</span>
        </el-menu-item>
        <el-menu-item index="/text-gen">
          <el-icon><Document /></el-icon>
          <span>文本生成</span>
        </el-menu-item>
        <el-menu-item index="/preview">
          <el-icon><FolderOpened /></el-icon>
          <span>文件预览</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
      <div class="header-right">
        <el-tag size="small" :type="serverStatus === 'ok' ? 'success' : 'danger'">
          {{ serverStatus === 'ok' ? 'API 已连接' : 'API 未连接' }}
        </el-tag>
      </div>
    </el-header>

    <!-- 主体 -->
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'

const route = useRoute()
const serverStatus = ref('unknown')

const activeMenu = computed(() => {
  if (route.path.startsWith('/prices')) return '/prices'
  if (route.path.startsWith('/quote')) return '/quote'
  if (route.path.startsWith('/text-gen')) return '/text-gen'
  if (route.path.startsWith('/preview')) return '/preview'
  if (route.path.startsWith('/chat')) return '/chat'
  if (route.path.startsWith('/settings')) return '/settings'
  return '/workspace'
})

async function checkServer() {
  try {
    const r = await api.get('/health')
    if (r.data?.status === 'ok') serverStatus.value = 'ok'
  } catch {
    serverStatus.value = 'error'
  }
}

onMounted(() => {
  checkServer()
  // 监听 electron 服务端通知
  if (window.costpilot) {
    window.costpilot.onServerReady(() => checkServer())
    window.costpilot.onServerError(() => { serverStatus.value = 'error' })
  }
})
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.app-container {
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  background: #2c3e50;
  color: white;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  margin-right: 40px;
  white-space: nowrap;
}

.top-menu {
  background: transparent;
  border: none;
  flex: 1;
}

.top-menu .el-menu-item {
  color: #c0c4cc;
}

.top-menu .el-menu-item.is-active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.header-right {
  margin-left: auto;
}

.app-main {
  padding: 16px;
  background: #f5f7fa;
  overflow: auto;
}
</style>
