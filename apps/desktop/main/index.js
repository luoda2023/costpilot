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

let mainWindow = null;
let pythonServer = null;

/**
 * 启动 Python FastAPI 子进程
 */
function startPythonServer() {
  let cmd, args;
  if (process.platform === 'win32') {
    cmd = 'python';
    args = ['-m', 'uvicorn', 'packages.server.api.app:app',
            '--host', '127.0.0.1', '--port', String(SERVER_PORT)];
  } else {
    cmd = 'python3';
    args = ['-m', 'uvicorn', 'packages.server.api.app:app',
            '--host', '127.0.0.1', '--port', String(SERVER_PORT)];
  }

  const cwd = app.isPackaged
    ? path.join(process.resourcesPath, 'app')
    : path.join(__dirname, '..', '..');

  pythonServer = spawn(cmd, args, {
    cwd,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  pythonServer.stdout.on('data', (data) => {
    console.log(`[python] ${data.toString().trim()}`);
  });
  pythonServer.stderr.on('data', (data) => {
    console.error(`[python err] ${data.toString().trim()}`);
  });
  pythonServer.on('exit', (code) => {
    console.log(`Python server exited with code ${code}`);
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
 * 创建主窗口
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 720,
    title: '造价通',
    backgroundColor: '#f5f7fa',
    webPreferences: {
      preload: path.join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    // 开发模式加载 Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // 生产模式加载打包后的 HTML
    mainWindow.loadFile(path.join(__dirname, '..', '..', 'web', 'dist', 'index.html'));
  }

  // 外部链接用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 启动后访问服务,保证建立连接
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
