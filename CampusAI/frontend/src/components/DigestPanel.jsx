import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8000'

function DigestPanel() {
  const [digest, setDigest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`${API}/digest`)
        const d = await res.json()
        if (alive) setDigest(d)
      } catch (e) {
        if (alive) setError('无法连接后端，请先启动 uvicorn')
      } finally {
        if (alive) setLoading(false)
      }
    }
    load()
    return () => { alive = false }
  }, [])

  if (loading) return <p className="hint">正在生成今日简报…</p>
  if (error) return <p className="hint error">{error}</p>
  if (!digest) return <p className="hint">暂无简报</p>

  const items = Array.isArray(digest.items) ? digest.items : []

  return (
    <>
      <div className="digest-overview">
        <h2>📰 今日简报</h2>
        <p>{digest.overview}</p>
      </div>

      {items.length === 0 && <p className="hint">今天没有需要特别关注的信息，安心学习 🎉</p>}

      {items.map((it, i) => (
        <article className="card" key={i}>
          <div className="digest-title">
            <span className="digest-num">{i + 1}</span>
            <h3>{it.title}</h3>
          </div>
          {it.why && <p className="reason">🎯 {it.why}</p>}
          {it.action && <p className="digest-action">👉 {it.action}</p>}
          {it.deadline && <p className="deadline">⏰ 截止：{it.deadline}</p>}
        </article>
      ))}
    </>
  )
}

export default DigestPanel
