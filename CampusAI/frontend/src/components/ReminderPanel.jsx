import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8000'

function ReminderPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`${API}/reminders`)
        const d = await res.json()
        if (alive) setData(d)
      } catch (e) {
        if (alive) setError('无法连接后端，请先启动 uvicorn')
      } finally {
        if (alive) setLoading(false)
      }
    }
    load()
    return () => { alive = false }
  }, [])

  if (loading) return <p className="hint">正在整理待办…</p>
  if (error) return <p className="hint error">{error}</p>
  if (!data) return <p className="hint">暂无提醒</p>

  const items = Array.isArray(data.data) ? data.data : []
  const groups = [
    { key: 'today', label: '今天', test: (r) => r.days_left === 0 },
    { key: 'soon', label: '未来 3 天', test: (r) => r.days_left > 0 && r.days_left <= 3 },
    { key: 'week', label: '未来 7 天', test: (r) => r.days_left > 3 },
  ]
  const typeLabel = (r) => (r.type === 'event' ? '📌 事件' : '⏰ 截止')
  const dayLabel = (r) => (r.days_left === 0 ? '就是今天' : `还有 ${r.days_left} 天`)

  return (
    <>
      <div className="reminder-overview">
        <h2>⏰ 提醒</h2>
        <p>
          {items.length === 0
            ? '未来 7 天没有待办，安心学习 🎉'
            : `未来 7 天共 ${data.count} 件事：今天 ${data.today} 件 · 3 天内 ${data.urgent} 件`}
        </p>
      </div>

      {groups.map((g) => {
        const list = items.filter((r) => g.test(r))
        if (!list.length) return null
        return (
          <section key={g.key} className="reminder-group">
            <h3 className="reminder-group-title">{g.label}</h3>
            {list.map((r, i) => (
              <article className={`card reminder-card${r.urgent ? ' urgent' : ''}`} key={`${g.key}-${i}`}>
                <div className="reminder-top">
                  <span className="reminder-type">{typeLabel(r)}</span>
                  <span className={`reminder-days${r.days_left === 0 ? ' today' : ''}`}>{dayLabel(r)}</span>
                  {r.category && <span className="source">{r.category}</span>}
                </div>
                <h4 className="reminder-title">
                  {r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.title}</a> : r.title}
                </h4>
                {r.date && <p className="event-date">📅 {r.date}</p>}
                {r.action && <p className="reminder-action">👉 {r.action}</p>}
              </article>
            ))}
          </section>
        )
      })}
    </>
  )
}

export default ReminderPanel
