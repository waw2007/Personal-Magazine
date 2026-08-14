// Personal Magazine · Electron 主进程
// 职责：拉起 Python 后端 → 打开主界面 + 桌面小组件 → 系统托盘 + 开机自启
const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, screen, shell } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

const BACKEND_PORT = 8000
const API = `http://127.0.0.1:${BACKEND_PORT}`

const DESKTOP_DIR = __dirname
const FRONTEND_DEV = 'http://127.0.0.1:5173'
const WIDGET_HTML = path.join(DESKTOP_DIR, 'widget', 'index.html')

let mainWindow = null
let widgetWindow = null
let tray = null
let backendProc = null
let quitting = false

// =====================
// 路径解析（区分「开发」与「打包」两种模式）
// =====================

function findBackendDir() {
  const candidates = [
    process.env.PM_BACKEND_DIR,                          // 环境变量优先
    path.join(__dirname, '..', 'backend'),               // 开发：desktop/../backend
    'D:/Code/Personal Magazine/CampusAI/backend',        // 打包：个人机上的项目目录
  ]
  for (const c of candidates) {
    if (c && fs.existsSync(path.join(c, 'main.py'))) return c
  }
  return null
}

function findPython(backendDir) {
  const candidates = [
    path.join(backendDir, 'venv', 'Scripts', 'python.exe'),  // Windows
    path.join(backendDir, 'venv', 'bin', 'python'),           // macOS / Linux
  ]
  for (const c of candidates) if (fs.existsSync(c)) return c
  return process.platform === 'win32' ? 'python' : 'python3'
}

function resolveFrontendEntry() {
  const dev = path.join(__dirname, '..', 'frontend', 'dist', 'index.html')
  if (fs.existsSync(dev)) return dev
  const res = path.join(process.resourcesPath || '', 'frontend-dist', 'index.html')
  if (fs.existsSync(res)) return res
  return null
}

function resolveIcon() {
  const res = path.join(process.resourcesPath || '', 'icon.png')
  if (fs.existsSync(res)) return res
  return path.join(__dirname, 'assets', 'icon.png')
}

// =====================
// 后端
// =====================

function startBackend() {
  const backendDir = findBackendDir()
  if (!backendDir) {
    console.error('[backend] 找不到后端目录，请设置环境变量 PM_BACKEND_DIR')
    return
  }
  const python = findPython(backendDir)
  backendProc = spawn(python, ['-m', 'uvicorn', 'main:app', '--port', String(BACKEND_PORT)], {
    cwd: backendDir,
    stdio: 'ignore',
    windowsHide: true,
  })
  backendProc.on('error', (err) => console.error('[backend] 启动失败:', err.message))
  backendProc.on('exit', () => { backendProc = null })
}

// 轮询 /status 直到后端就绪（最长 timeoutMs）
function waitForBackend(timeoutMs = 20000) {
  return new Promise((resolve) => {
    const start = Date.now()
    const tryOnce = () => {
      fetch(`${API}/status`)
        .then(() => resolve(true))
        .catch(() => {
          if (Date.now() - start > timeoutMs) resolve(false)
          else setTimeout(tryOnce, 500)
        })
    }
    tryOnce()
  })
}

// =====================
// 窗口
// =====================

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 920,
    height: 780,
    title: 'Personal Magazine',
    icon: resolveIcon(),
    webPreferences: {
      preload: path.join(DESKTOP_DIR, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  const entry = resolveFrontendEntry()
  if (entry) {
    mainWindow.loadFile(entry)
  } else {
    mainWindow.loadURL(FRONTEND_DEV)
  }
  // 外部链接（新闻原文、日历导出等）用系统默认浏览器打开，而不是新 Electron 窗口 / 导航走 SPA
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url)
    return { action: 'deny' }
  })
  mainWindow.webContents.on('will-navigate', (e, url) => {
    if (url.startsWith('http')) {
      e.preventDefault()
      shell.openExternal(url)
    }
  })
  // 关闭 = 最小化到托盘（后台常驻）
  mainWindow.on('close', (e) => {
    if (!quitting) { e.preventDefault(); mainWindow.hide() }
  })
  mainWindow.on('closed', () => { mainWindow = null })
}

function createWidgetWindow() {
  const { width, height } = screen.getPrimaryDisplay().workArea
  const w = 320
  const h = 460
  widgetWindow = new BrowserWindow({
    width: w,
    height: h,
    x: width - w - 24,
    y: height - h - 24,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    icon: resolveIcon(),
    webPreferences: {
      preload: path.join(DESKTOP_DIR, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  widgetWindow.setAlwaysOnTop(true, 'screen-saver')
  widgetWindow.loadFile(WIDGET_HTML)
  widgetWindow.on('closed', () => { widgetWindow = null })
}

function showMain() {
  if (!mainWindow) createMainWindow()
  mainWindow.show()
  mainWindow.focus()
}

function toggleWidget() {
  if (!widgetWindow) {
    createWidgetWindow()
  } else if (widgetWindow.isVisible()) {
    widgetWindow.hide()
  } else {
    widgetWindow.show()
  }
}

// =====================
// 托盘
// =====================

function createTray() {
  let image = nativeImage.createFromPath(resolveIcon())
  if (image.isEmpty()) image = nativeImage.createEmpty()
  tray = new Tray(image)
  tray.setToolTip('Personal Magazine')
  const menu = Menu.buildFromTemplate([
    { label: '打开主界面', click: () => showMain() },
    { label: '显示 / 隐藏小组件', click: () => toggleWidget() },
    { type: 'separator' },
    {
      label: '开机自启',
      type: 'checkbox',
      checked: app.getLoginItemSettings().openAtLogin,
      click: (mi) => app.setLoginItemSettings({ openAtLogin: mi.checked }),
    },
    { type: 'separator' },
    { label: '退出', click: () => { quitting = true; app.quit() } },
  ])
  tray.setContextMenu(menu)
  tray.on('double-click', () => showMain())
}

// =====================
// IPC（小组件 → 主进程）
// =====================

ipcMain.on('open-main', () => showMain())
ipcMain.on('hide-widget', () => { if (widgetWindow) widgetWindow.hide() })

// =====================
// 启动
// =====================

async function main() {
  startBackend()
  await waitForBackend()
  createMainWindow()
  createWidgetWindow()
  createTray()
}

const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => showMain())
  app.whenReady().then(main)
  // 关掉所有窗口也不退出，后台常驻（托盘 + 小组件）
  app.on('window-all-closed', () => {})
  app.on('before-quit', () => {
    quitting = true
    if (backendProc) { try { backendProc.kill() } catch (e) {} }
  })
}
