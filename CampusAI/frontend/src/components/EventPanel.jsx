import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8000'

function EventPanel() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [date, setDate] = useState('')
  const [note, setNote] = useState('')

  const load = async () => {
    try {
      const res = await fetch(`${API}/events`)
      const d = await res.json()
      setEvents(Array.isArray(d.data) ? d.data : [])
    } catch (e) {
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const add = async (e) => {
    e.preventDefault()
    if (!name.trim() || !date) return
    await fetch(`${API}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim(), date, note: note.trim() }),
    })
    setName('')
    setDate('')
    setNote('')
    load()
  }

  const remove = async (id) => {
    await fetch(`${API}/events/${id}`, { method: 'DELETE' })
    load()
  }

  return (
    <>
      <form className="event-form" onSubmit={add}>
        <input className="ef-name" placeholder="事件名（如：四六级笔试）" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="ef-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <input className="ef-note" placeholder="备注（可选）" value={note} onChange={(e) => setNote(e.target.value)} />
        <button className="btn" type="submit">添加</button>
      </form>

      {loading && <p className="hint">加载中…</p>}
      {!loading && events.length === 0 && <p className="hint">还没有事件，用上面的表单添加一个吧</p>}
      {events.map((ev) => (
        <div key={ev.id} className={`event-card ${ev.status} ${ev.urgent ? 'urgent' : ''}`}>
          <div className="event-main">
            <h3 className="event-name">{ev.name}</h3>
            <p className="event-date">{ev.date}{ev.note ? ` · ${ev.note}` : ''}</p>
          </div>
          <div className="event-count">{ev.label}</div>
          <button className="event-del" onClick={() => remove(ev.id)} title="删除">✕</button>
        </div>
      ))}
    </>
  )
}

export default EventPanel
