import { useState, useEffect, useCallback } from 'react'
import NewsCard from './components/NewsCard'
import EventPanel from './components/EventPanel'
import './App.css'

const API = 'http://127.0.0.1:8000'

const VIEWS = [
  { key: 'recommend', label: '今日推荐', endpoint: '/recommend' },
  { key: 'all', label: '全部', endpoint: '/news' },
  { key: 'important', label: '重要', endpoint: '/important' },
  { key: 'events', label: '倒数日', endpoint: '/events' },
]

const CATEGORIES = ['教务', '奖助学金', '竞赛', '就业', '科研', '其他']

function App() {
  const [view, setView] = useState('recommend')
  const [category, setCategory] = useState('')
  const [query, setQuery] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState(null)
  const [notifEnabled, setNotifEnabled] = useState(
    typeof Notification !== 'undefined' && Notification.permission === 'granted'
  )
  const load = useCallback(async () => {
    if (view === 'events') {
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    try {
      let url
      if (query) {
        url = `${API}/search?q=${encodeURIComponent(query)}`
      } else if (category) {
        url = `${API}/category/${encodeURIComponent(category)}`
      } else {
        url = `${API}${VIEWS.find((v) => v.key === view).endpoint}`
      }
      const res = await fetch(url)
      const data = await res.json()
      setItems(Array.isArray(data.data) ? data.data : [])
    } catch (e) {
      setError('无法连接后端，请先在 backend 目录运行：uvicorn main:app --reload')
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [view, category, query])

  useEffect(() => {
    load()
  }, [load])

  // 每 30 秒轮询状态，检测到新增信息（is_new）则弹系统通知
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API}/status`)
        const s = await res.json()
        setStatus(s)
        if (notifEnabled && Array.isArray(s.new_items)) {
          const notified = JSON.parse(localStorage.getItem('pm-notified') || '[]')
          const fresh = s.new_items.filter((it) => it.url && !notified.includes(it.url))
          for (const it of fresh) {
            new Notification('Personal Magazine 📬', { body: it.title })
          }
          if (fresh.length) {
            load()
          }
          const alive = new Set(s.new_items.map((it) => it.url).filter(Boolean))
          localStorage.setItem('pm-notified', JSON.stringify(
            Array.from(new Set([...notified, ...fresh.map((it) => it.url)])).filter((u) => alive.has(u))
          ))
        }
      } catch (e) {
        /* 轮询失败忽略，下次重试 */
      }
    }
    poll()
    const timer = setInterval(poll, 30000)
    return () => clearInterval(timer)
  }, [notifEnabled, load])

  // 倒数日到期提醒：检查 3 天内的事件，各提醒一次（用 localStorage 去重）
  useEffect(() => {
    const REMIND_DAYS = 3
    const checkReminders = async () => {
      if (!notifEnabled) return
      try {
        const res = await fetch(`${API}/events`)
        const d = await res.json()
        const events = Array.isArray(d.data) ? d.data : []
        const reminded = JSON.parse(localStorage.getItem('pm-reminded') || '[]')
        const due = events.filter(
          (ev) => ev.days_left !== null && ev.days_left >= 0 && ev.days_left <= REMIND_DAYS
        )
        for (const ev of due) {
          if (reminded.includes(ev.id)) continue
          new Notification('倒数日提醒 ⏰', {
            body: `「${ev.name}」${ev.days_left === 0 ? '就是今天！' : `还有 ${ev.days_left} 天`}（${ev.date}）`,
          })
          reminded.push(ev.id)
        }
        // 只保留仍在列表里的事件 id，避免无限累积
        const alive = new Set(events.map((ev) => ev.id))
        localStorage.setItem('pm-reminded', JSON.stringify(reminded.filter((id) => alive.has(id))))
      } catch (e) {
        /* 忽略，下次再试 */
      }
    }
    checkReminders()
    const timer = setInterval(checkReminders, 60000)
    return () => clearInterval(timer)
  }, [notifEnabled])

  const enableNotifications = async () => {
    if (typeof Notification === 'undefined') return
    const p = await Notification.requestPermission()
    setNotifEnabled(p === 'granted')
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Personal Magazine</h1>
        <div className="topbar-meta">
          {status && <span className="status-dot">● 已收录 {status.news_count} 条信息</span>}
          {notifEnabled ? (
            <span className="status-on">🔔 通知已开启</span>
          ) : (
            <button className="btn" onClick={enableNotifications}>🔔 启用通知</button>
          )}
        </div>
      </header>

      <nav className="tabs">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            className={view === v.key && !category && !query ? 'tab active' : 'tab'}
            onClick={() => { setView(v.key); setCategory(''); setQuery('') }}
          >
            {v.label}
          </button>
        ))}
        <select
          className="select"
          value={category}
          onChange={(e) => { setCategory(e.target.value); setQuery('') }}
        >
          <option value="">全部分类</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <input
          className="search"
          placeholder="搜索…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </nav>

      <main className="feed">
        {view === 'events' ? (
          <EventPanel />
        ) : (
          <>
            {loading && <p className="hint">加载中…</p>}
            {error && <p className="hint error">{error}</p>}
            {!loading && !error && items.length === 0 && <p className="hint">暂无信息</p>}
            {items.map((item) => <NewsCard key={item.id} item={item} />)}
          </>
        )}
      </main>
    </div>
  )
}

export default App
