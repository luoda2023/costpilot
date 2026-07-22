/**
 * 造价通 - Electron 主进程
 * 负责:
 * - 创建 BrowserWindow 并加载 Vue 渲染进程
 * - 拉起 Python FastAPI 子进程
 * - 应用菜单
 */
const { app, BrowserWindow, Menu, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

// 配置
const SERVER_URL = 'http://127.0.0.1:8765';
const SERVER_PORT = 8765;
const isDev = !app.isPackaged;

// 关闭 GPU 硬件加速 - 解决花屏/闪屏问题(部分显卡与 Chromium 渲染冲突)
app.disableHardwareAcceleration();

let mainWindow = null;
let pythonServer = null;

/**
 * 启动 Python FastAPI 子进程
 *
 * 打包后: 用 PyInstaller 产出的 costpilot-server.exe,无需用户装 Python
 * 开发期: 用 python -m uvicorn
 */
function startPythonServer() {
 let cmd, args, cwd;

 if (app.isPackaged) {
 // 打包模式: 跑 costpilot-server.exe (PyInstaller onefile)
 if (process.platform === 'win32') {
 cmd = path.join(process.resourcesPath, 'app', 'costpilot-server.exe');
 args = ['--host', '127.0.0.1', '--port', String(SERVER_PORT)];
 } else {
 // mac/linux 暂未实现PyInstaller 打包,降级到 python3
 cmd = 'python3';
 args = ['-m', 'uvicorn', 'packages.server.api.app:app',
 '--host', '127.0.0.1', '--port', String(SERVER_PORT)];
 }
 cwd = path.join(process.resourcesPath, 'app');
 } else {
 // 开发模式: 直接调 python
 if (process.platform === 'win32') {
 cmd = 'python';
 } else {
 cmd = 'python3';
 }
 args = ['-m', 'uvicorn', 'packages.server.api.app:app',
 '--host', '127.0.0.1', '--port', String(SERVER_PORT)];
 cwd = path.join(__dirname, '..', '..');
 }

 pythonServer = spawn(cmd, args, {
 cwd,
 env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
 stdio: ['ignore', 'pipe', 'pipe'],
 windowsHide: true,
 });

 pythonServer.stdout.on('data', (data) => {
 console.log(`[server] ${data.toString().trim()}`);
 });
 pythonServer.stderr.on('data', (data) => {
 console.error(`[server err] ${data.toString().trim()}`);
 });
 pythonServer.on('exit', (code) => {
 console.log(`Server exited with code ${code}`);
 });
}

/**
 * 健康检查 - 等待 FastAPI 起来
 */
function waitForServer(maxAttempts = 30) {
  return new Promise((resolve, reject) => {
 let attempts = 0;
 const check = () => {
 attempts++;
 const req = http.get(`${SERVER_URL}/health`, (res) => {
 if (res.statusCode === 200) {
 resolve();
 } else if (attempts < maxAttempts) {
 setTimeout(check, 500);
 } else {
 reject(new Error('Server not responding'));
 }
 });
 req.on('error', () => {
 if (attempts < maxAttempts) setTimeout(check, 500);
 else reject(new Error('Server not responding'));
 });
 req.setTimeout(1000, () => {
 req.destroy();
 if (attempts < maxAttempts) setTimeout(check, 500);
 else reject(new Error('Server not responding'));
 });
 };
 check();
  });
}

/**
 * 首次启动确保 config.yaml / 数据库初始目录存在
 * 打包模式: cwd = process.resourcesPath/app, 在此建 data/sqlite 目录
 */
function ensureRuntimeFiles() {
  let baseDir;
  if (app.isPackaged) {
 baseDir = path.join(process.resourcesPath, 'app');
  } else {
 baseDir = path.join(__dirname, '..', '..');
  }
  // 1. config.yaml 不存在则从 config.example.yaml 复制
  const cfgPath = path.join(baseDir, 'config.yaml');
  const cfgExamplePath = path.join(baseDir, 'config.example.yaml');
  if (!fs.existsSync(cfgPath) && fs.existsSync(cfgExamplePath)) {
 fs.copyFileSync(cfgExamplePath, cfgPath);
 console.log('[init] 已从 config.example.yaml 复制为 config.yaml');
  }
  // 2. data/sqlite 目录
  const sqliteDir = path.join(baseDir, 'data', 'sqlite');
  if (!fs.existsSync(sqliteDir)) {
 fs.mkdirSync(sqliteDir, { recursive: true });
 console.log(`[init] 已创建目录 ${sqliteDir}`);
  }
  return baseDir;
}

/**
 * 创建主窗口
 */
function createWindow() {
  mainWindow = new BrowserWindow({
 width: 1440,
 height: 900,
 minWidth: 1024,
 minHeight: 720,
 title: '造价通',
 show: false, // 先隐藏,等 ready-to-show 再显示,消除白屏闪
 backgroundColor: '#f5f7fa',
 webPreferences: {
 preload: path.join(__dirname, '..', 'preload', 'index.js'),
 contextIsolation: true,
 nodeIntegration: false,
 },
  });

  // 窗口准备好再显示,消除花屏
  mainWindow.once('ready-to-show', () => {
 mainWindow.show();
  });

  if (isDev) {
 // 开发模式加载 Vite dev server
 mainWindow.loadURL('http://localhost:5173');
 mainWindow.webContents.openDevTools();
  } else {
 // 生产模式: 后端已挂载前端静态文件,从 http:// 加载, 这样 /api 请求同源正常
 mainWindow.loadURL(`${SERVER_URL}/`);
  }

  // 外部链接用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
 shell.openExternal(url);
 return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
 mainWindow = null;
  });

  // 启动后通知前端服务已就绪
  mainWindow.webContents.on('did-finish-load', async () => {
 try {
 await waitForServer();
 mainWindow.webContents.send('server:ready', SERVER_URL);
 } catch (err) {
 mainWindow.webContents.send('server:error', err.message);
 }
  });
}

/**
 * 应用菜单
 */
function createMenu() {
  const template = [
 {
 label: '文件',
 submenu: [
 { label: '新建项目', accelerator: 'CmdOrCtrl+N', click: () => mainWindow?.webContents.send('menu:new-project') },
 { type: 'separator' },
 { label: '退出', accelerator: 'CmdOrCtrl+Q', role: 'quit' },
 ],
 },
 {
 label: '编辑',
 submenu: [
 { role: 'undo', label: '撤销' },
 { role: 'redo', label: '重做' },
 { type: 'separator' },
 { role: 'cut', label: '剪切' },
 { role: 'copy', label: '复制' },
 { role: 'paste', label: '粘贴' },
 ],
 },
 {
 label: '视图',
 submenu: [
 { role: 'reload', label: '刷新' },
 { role: 'toggleDevTools', label: '开发者工具' },
 { type: 'separator' },
 { role: 'resetZoom', label: '重置缩放' },
 { role: 'zoomIn', label: '放大' },
 { role: 'zoomOut', label: '缩小' },
 { type: 'separator' },
 { role: 'togglefullscreen', label: '全屏' },
 ],
 },
 {
 label: '帮助',
 submenu: [
 { label: '关于造价通', click: () => shell.openExternal('https://github.com/costpilot') },
 ],
 },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// 单例锁
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
 if (mainWindow) {
 if (mainWindow.isMinimized()) mainWindow.restore();
 mainWindow.focus();
 }
  });

app.whenReady().then(async () => {
ensureRuntimeFiles(); // 首次启动确保 config.yaml / data/sqlite 就位
if (isDev) {
 // 开发模式 FastAPI 自己 npm dev:server 起, 不用 Electron 再起一遍
 createWindow();
 createMenu();
} else {
 startPythonServer();
 try {
 await waitForServer();
 createWindow();
 createMenu();
 } catch (err) {
 console.error('Failed to start server:', err);
 // 仍创建窗口,显示错误页
 createWindow();
 createMenu();
 mainWindow?.webContents.send('server:error', err.message);
 }
}
});

  app.on('window-all-closed', () => {
 if (process.platform !== 'darwin') {
 if (pythonServer) pythonServer.kill();
 app.quit();
 }
  });

  app.on('activate', () => {
 if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  app.on('before-quit', () => {
 if (pythonServer) {
 pythonServer.kill('SIGTERM');
 }
  });
}