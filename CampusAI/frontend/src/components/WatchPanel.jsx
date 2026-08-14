import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8000'

function WatchPanel() {
  const [subs, setSubs] = useState([])
  const [items, setItems] = useState([])
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [subsRes, watchRes] = await Promise.all([
        fetch(`${API}/subscriptions`),
        fetch(`${API}/watch`),
      ])
      const sd = await subsRes.json()
      const wd = await watchRes.json()
      setSubs(Array.isArray(sd.data) ? sd.data : [])
      setItems(Array.isArray(wd.data) ? wd.data : [])
    } catch (e) {
      setSubs([])
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const add = async (e) => {
    e.preventDefault()
    if (!keyword.trim()) return
    await fetch(`${API}/subscriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: keyword.trim() }),
    })
    setKeyword('')
    load()
  }

  const remove = async (id) => {
    await fetch(`${API}/subscriptions/${id}`, { method: 'DELETE' })
    load()
  }

  return (
    <>
      <form className="event-form" onSubmit={add}>
        <input
          className="ef-name"
          placeholder="关注关键词（如：保研 / 四六级 / 数学建模）"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
        <button className="btn" type="submit">添加关注</button>
      </form>

      {subs.length > 0 && (
        <div className="watch-tags">
          {subs.map((s) => (
            <span key={s.id} className="watch-tag">
              #{s.keyword}
              <button className="watch-del" onClick={() => remove(s.id)} title="取消关注">✕</button>
            </span>
          ))}
        </div>
      )}

      {loading && <p className="hint">加载中…</p>}
      {!loading && items.length === 0 && (
        <p className="hint">
          {subs.length === 0 ? '还没有关注词，先添加一个吧' : '暂无命中关注词的信息'}
        </p>
      )}
      {items.map((it) => (
        <article className="card" key={it.url || it.id}>
          <div className="card-top">
            <span className="watch-hit">🔍 命中：{(it.matched || []).join('、')}</span>
            <span className="source">{it.source}</span>
            {it.date && <span className="date">📅 {it.date}</span>}
          </div>
          <h2 className="title">
            <a href={it.url} target="_blank" rel="noreferrer">{it.title}</a>
          </h2>
          <p className="summary">{it.summary}</p>
          {it.deadline && <p className="deadline">⏰ 截止：{it.deadline}</p>}
        </article>
      ))}
    </>
  )
}

export default WatchPanel
