import { useState, useEffect, useCallback } from 'react'
import NewsCard from './components/NewsCard'
import EventPanel from './components/EventPanel'
import DigestPanel from './components/DigestPanel'
import ReminderPanel from './components/ReminderPanel'
import './App.css'

const API = 'http://127.0.0.1:8000'

const VIEWS = [
  { key: 'digest', label: '今日简报', endpoint: '/digest' },
  { key: 'remind', label: '提醒', endpoint: '/reminders' },
  { key: 'recommend', label: '今日推荐', endpoint: '/recommend' },
  { key: 'all', label: '全部', endpoint: '/news' },
  { key: 'important', label: '重要', endpoint: '/important' },
  { key: 'archived', label: '已归档', endpoint: '/news' },
  { key: 'events', label: '倒数日', endpoint: '/events' },
]

const CATEGORIES = ['教务', '奖助学金', '竞赛', '就业', '科研', '其他']

const itemKey = (it) => it.url || String(it.id)

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
  const [readUrls, setReadUrls] = useState(() => JSON.parse(localStorage.getItem('pm-read') || '[]'))
  const [archivedUrls, setArchivedUrls] = useState(() => JSON.parse(localStorage.getItem('pm-archived') || '[]'))

  useEffect(() => { localStorage.setItem('pm-read', JSON.stringify(readUrls)) }, [readUrls])
  useEffect(() => { localStorage.setItem('pm-archived', JSON.stringify(archivedUrls)) }, [archivedUrls])

  const toggleRead = (url) => setReadUrls((prev) =>
    prev.includes(url) ? prev.filter((u) => u !== url) : [...prev, url]
  )
  const toggleArchive = (url) => setArchivedUrls((prev) =>
    prev.includes(url) ? prev.filter((u) => u !== url) : [...prev, url]
  )
  const markAllRead = () => setReadUrls((prev) =>
    Array.from(new Set([...prev, ...items.map(itemKey).filter(Boolean)]))
  )
  const load = useCallback(async () => {
    if (view === 'events' || view === 'digest' || view === 'remind') {
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

  // 提醒 Agent：轮询 /reminders，对「3 天内」的待办弹一条汇总通知（localStorage 去重）
  useEffect(() => {
    const checkReminders = async () => {
      if (!notifEnabled) return
      try {
        const res = await fetch(`${API}/reminders`)
        const d = await res.json()
        const data = Array.isArray(d.data) ? d.data : []
        const key = (r) => r.url || `${r.type}:${r.title}`
        const reminded = JSON.parse(localStorage.getItem('pm-reminders') || '[]')
        const fresh = data.filter((r) => r.urgent && !reminded.includes(key(r)))
        if (!fresh.length) return
        const todayCount = fresh.filter((r) => r.days_left === 0).length
        const title = todayCount > 0
          ? `⏰ 今天有 ${todayCount} 件事要处理`
          : `⏰ 未来 3 天有 ${fresh.length} 件事待办`
        const lines = fresh.slice(0, 3).map((r) =>
          r.days_left === 0 ? `· ${r.title}（今天）` : `· ${r.title}（还有 ${r.days_left} 天）`
        ).join('\n')
        const more = fresh.length > 3 ? `\n…等 ${fresh.length} 件` : ''
        new Notification('Personal Magazine ⏰', { body: `${title}\n${lines}${more}`, tag: 'pm-reminders' })
        const alive = new Set(data.map(key))
        localStorage.setItem('pm-reminders', JSON.stringify(
          Array.from(new Set([...reminded, ...fresh.map(key)])).filter((k) => alive.has(k))
        ))
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

  const visibleItems = view === 'archived'
    ? items.filter((it) => archivedUrls.includes(itemKey(it)))
    : items.filter((it) => !archivedUrls.includes(itemKey(it)))

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
        {view === 'digest' ? (
          <DigestPanel />
        ) : view === 'remind' ? (
          <ReminderPanel />
        ) : view === 'events' ? (
          <EventPanel />
        ) : (
          <>
            {!loading && !error && view !== 'archived' && visibleItems.length > 0 && (
              <div className="feed-toolbar">
                <button className="btn" onClick={markAllRead}>✓ 全部已读</button>
              </div>
            )}
            {loading && <p className="hint">加载中…</p>}
            {error && <p className="hint error">{error}</p>}
            {!loading && !error && visibleItems.length === 0 && (
              <p className="hint">{view === 'archived' ? '暂无归档信息' : '暂无信息'}</p>
            )}
            {visibleItems.map((item) => (
              <NewsCard
                key={item.id}
                item={item}
                isRead={readUrls.includes(itemKey(item))}
                isArchived={archivedUrls.includes(itemKey(item))}
                onToggleRead={toggleRead}
                onToggleArchive={toggleArchive}
              />
            ))}
          </>
        )}
      </main>
    </div>
  )
}

export default App
