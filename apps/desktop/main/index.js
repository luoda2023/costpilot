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

// 用户数据目录: %APPDATA%/costpilot (卸载重装不丢配置/数据库)
const USER_DATA_DIR = path.join(app.getPath('appData'), 'costpilot');

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
	 env: {
 ...process.env,
 PYTHONIOENCODING: 'utf-8',
 COSTPILOT_DATA_DIR: USER_DATA_DIR, // 告诉 Python 服务端用户数据目录
 },
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
 * 健康检查(已废弃) - 替换为 waitForServerAndNotify
 */
function waitForServer() { return Promise.resolve(); }

/**
 * 首次启动: 确保 config.yaml / 数据库在 USER_DATA_DIR 存在
 * %APPDATA%/costpilot/ 卸载重装不丢
 */
function ensureRuntimeFiles() {
  // 1. 创建用户数据目录
  if (!fs.existsSync(USER_DATA_DIR)) {
    fs.mkdirSync(USER_DATA_DIR, { recursive: true });
    console.log(`[init] 已创建用户数据目录 ${USER_DATA_DIR}`);
  }

  // 2. config.yaml 不存在则从 config.example.yaml 复制
  const cfgPath = path.join(USER_DATA_DIR, 'config.yaml');
  const cfgExamplePath = (() => {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'app', 'config.example.yaml');
    }
    return path.join(__dirname, '..', '..', 'config.example.yaml');
  })();
  if (!fs.existsSync(cfgPath) && fs.existsSync(cfgExamplePath)) {
    fs.copyFileSync(cfgExamplePath, cfgPath);
    console.log(`[init] 已复制 config.example.yaml → ${cfgPath}`);
  }

  // 3. data/sqlite 目录
  const sqliteDir = path.join(USER_DATA_DIR, 'data', 'sqlite');
  if (!fs.existsSync(sqliteDir)) {
    fs.mkdirSync(sqliteDir, { recursive: true });
    console.log(`[init] 已创建数据库目录 ${sqliteDir}`);
  }

  // 4. 种子数据库 造价通.db 不存在则从 extraResources 复制
  const dbPath = path.join(sqliteDir, '造价通.db');
  if (!fs.existsSync(dbPath)) {
    const seedDbPath = (() => {
      if (app.isPackaged) {
        return path.join(process.resourcesPath, 'app', 'data', 'sqlite', '造价通.db');
      }
      return path.join(__dirname, '..', '..', 'data', 'sqlite', '造价通.db');
    })();
    if (fs.existsSync(seedDbPath)) {
      fs.copyFileSync(seedDbPath, dbPath);
      console.log(`[init] 已复制种子数据库 → ${dbPath}`);
    } else {
      console.warn(`[init] 种子数据库不存在: ${seedDbPath}`);
    }
  }
}

/**
 * 创建主窗口 - 立即显示，不等待服务器
 */
function createWindow() {
  mainWindow = new BrowserWindow({
 width: 1440,
 height: 900,
 minWidth: 1024,
 minHeight: 720,
 title: '造价通',
 show: false,
 backgroundColor: '#f5f7fa',
 webPreferences: {
 preload: path.join(__dirname, '..', 'preload', 'index.js'),
 contextIsolation: true,
 nodeIntegration: false,
 },
  });

  // 窗口准备好立即显示，不等服务器
  mainWindow.once('ready-to-show', () => {
 mainWindow.show();
  });

  // 生产模式：先加载本地 splash 页面（瞬间显示），自动轮询服务器
  // 开发模式：直接加载 Vite dev server
  if (isDev) {
 mainWindow.loadURL('http://localhost:5173');
 mainWindow.webContents.openDevTools();
  } else {
 const splashPath = path.join(__dirname, '..', 'splash.html');
 mainWindow.loadFile(splashPath);
  }

  // 外部链接用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
 shell.openExternal(url);
 return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
 mainWindow = null;
  });
}

/**
 * 后台等待服务器就绪，然后通知前端并跳转
 */
function waitForServerAndNotify() {
  let attempts = 0;
  const maxAttempts = 60; // 最长等 30 秒
  const check = () => {
 attempts++;
 const req = http.get(`${SERVER_URL}/health`, (res) => {
 if (res.statusCode === 200) {
 console.log('[app] 后端服务已就绪');
 if (mainWindow && !mainWindow.isDestroyed()) {
 // 通知前端
 mainWindow.webContents.send('server:ready', SERVER_URL);
 // 如果当前还在 splash 页，跳转到真实应用
 mainWindow.loadURL(`${SERVER_URL}/`);
 }
 } else if (attempts < maxAttempts) {
 setTimeout(check, 500);
 }
 });
 req.on('error', () => {
 if (attempts < maxAttempts) {
 setTimeout(check, 500);
 }
 });
 req.setTimeout(1000, () => {
 req.destroy();
 if (attempts < maxAttempts) {
 setTimeout(check, 500);
 }
 });
 };
 check();
}

/**
 * 应用菜单
 */
function createMenu() {
  // 去掉原生菜单栏，用 Vue 前端导航替代
  Menu.setApplicationMenu(null);
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

app.whenReady().then(() => {
ensureRuntimeFiles(); // 首次启动确保 config.yaml / data/sqlite 就位

// 窗口立即显示，不等待服务器
createWindow();
createMenu();

if (!isDev) {
 // 生产模式：后台启动 Python 服务器，前端自己轮询等待
 startPythonServer();
 waitForServerAndNotify();
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