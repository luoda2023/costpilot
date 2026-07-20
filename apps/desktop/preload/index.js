/**
 * 造价通 - Electron preload
 * 暴露安全的 IPC API 给渲染进程
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('costpilot', {
  // 服务器通知
  onServerReady: (callback) => ipcRenderer.on('server:ready', (_, url) => callback(url)),
  onServerError: (callback) => ipcRenderer.on('server:error', (_, msg) => callback(msg)),

  // 菜单事件
  onMenuNewProject: (callback) => ipcRenderer.on('menu:new-project', () => callback()),

  // 应用信息
  getVersion: () => process.versions,
  getPlatform: () => process.platform,

  // 文件操作(后续扩展)
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  saveFileDialog: (defaultName) => ipcRenderer.invoke('dialog:saveFile', defaultName),
});
