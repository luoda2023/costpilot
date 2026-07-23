<template>
  <el-container class="app-container">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="logo">
        <el-icon :size="20"><Coin /></el-icon>
        <span>造价通</span>
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
import axios from 'axios'

const route = useRoute()

const activeMenu = computed(() => {
  if (route.path.startsWith('/prices')) return '/prices'
  if (route.path.startsWith('/quote')) return '/quote'
  if (route.path.startsWith('/text-gen')) return '/text-gen'
  if (route.path.startsWith('/preview')) return '/preview'
  if (route.path.startsWith('/chat')) return '/chat'
  if (route.path.startsWith('/settings')) return '/settings'
  return '/workspace'
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
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  background: #1a2332;
  color: white;
  padding: 0 16px;
  height: 48px !important;
  min-height: 48px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  margin-right: 24px;
  white-space: nowrap;
  color: #e8eaed;
}

.top-menu {
  background: transparent;
  border: none !important;
  flex: 1;
}

.top-menu .el-menu-item {
  color: #9aa0a6;
  height: 48px;
  line-height: 48px;
  font-size: 13px;
  padding: 0 14px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.top-menu .el-menu-item:hover {
  color: #e8eaed;
  background: rgba(255,255,255,0.06);
}

.top-menu .el-menu-item.is-active {
  color: white;
  border-bottom-color: #409eff;
  background: transparent;
}

.app-main {
  flex: 1;
  padding: 12px;
  background: #f5f7fa;
  overflow: auto;
}

/* 去除 Element Plus 默认边框 */
.el-menu--horizontal > .el-menu-item:not(.is-disabled):focus,
.el-menu--horizontal > .el-menu-item:not(.is-disabled):hover {
  background: transparent;
}
.el-menu--horizontal {
  border-bottom: none !important;
}
</style>