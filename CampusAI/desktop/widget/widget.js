// 桌面小组件：展示「临近提醒 + 最新信息」，点击跳转主界面，每 60 秒自动刷新
const API = 'http://127.0.0.1:8000'

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

async function load() {
  try {
    const [remRes, newsRes] = await Promise.all([
      fetch(`${API}/reminders`),
      fetch(`${API}/latest`),
    ])
    const rem = await remRes.json()
    const news = await newsRes.json()
    renderReminders(Array.isArray(rem.data) ? rem.data : [])
    renderLatest(Array.isArray(news.data) ? news.data : [])
  } catch (e) {
    document.getElementById('reminders').innerHTML = '<li class="muted">后端未连接</li>'
    document.getElementById('latest').innerHTML = '<li class="muted">后端未连接</li>'
  }
}

function renderReminders(items) {
  const el = document.getElementById('reminders')
  const urgent = items.filter((r) => r.days_left <= 3)
  if (!urgent.length) {
    el.innerHTML = '<li class="muted">近期无待办 🎉</li>'
    return
  }
  el.innerHTML = urgent.slice(0, 4).map((r) => {
    const d = r.days_left === 0 ? '今天' : `${r.days_left} 天后`
    const dot = r.days_left === 0 ? ' today' : ''
    return `<li><span class="dot${dot}"></span><span class="t">${escapeHtml(r.title)}</span><span class="d">${d}</span></li>`
  }).join('')
}

function renderLatest(items) {
  const el = document.getElementById('latest')
  if (!items.length) {
    el.innerHTML = '<li class="muted">暂无新信息</li>'
    return
  }
  el.innerHTML = items.slice(0, 5).map((it) =>
    `<li><span class="t">${escapeHtml(it.title)}</span></li>`
  ).join('')
}

// 点击内容区 → 打开主界面
document.getElementById('body').addEventListener('click', () => {
  if (window.electronAPI) window.electronAPI.openMain()
})
document.getElementById('close').addEventListener('click', (e) => {
  e.stopPropagation()
  if (window.electronAPI) window.electronAPI.hideWidget()
})

load()
setInterval(load, 60000)
