import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8000'

const emptyForm = {
  name: '',
  url: '',
  type: 'other',
  frequency_hours: '12',
  keywords: '',
  content_selector: '',
}

function SitesPanel() {
  const [sites, setSites] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null) // 正在编辑的下标，null 表示新增

  const load = async () => {
    try {
      const res = await fetch(`${API}/websites`)
      const d = await res.json()
      setSites(Array.isArray(d.data) ? d.data : [])
    } catch (e) {
      setSites([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.name.trim() || !form.url.trim()) return
    const body = {
      name: form.name.trim(),
      url: form.url.trim(),
      type: form.type.trim() || 'other',
      frequency_hours: parseInt(form.frequency_hours, 10) || 12,
      keywords: form.keywords.split(/[,，、\s]+/).filter(Boolean),
      content_selector: form.content_selector.trim(),
    }
    if (editing === null) {
      await fetch(`${API}/websites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    } else {
      await fetch(`${API}/websites/${editing}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    }
    setForm(emptyForm)
    setEditing(null)
    load()
  }

  const remove = async (index) => {
    const s = sites.find((x) => x.index === index)
    if (!window.confirm(`确定删除「${s ? s.name : ''}」？`)) return
    await fetch(`${API}/websites/${index}`, { method: 'DELETE' })
    load()
  }

  const edit = (index) => {
    const s = sites.find((x) => x.index === index)
    if (!s) return
    setEditing(index)
    setForm({
      name: s.name,
      url: s.url,
      type: s.type,
      frequency_hours: String(s.frequency_hours),
      keywords: (s.keywords || []).join('、'),
      content_selector: s.content_selector || '',
    })
  }

  return (
    <>
      <form className="sites-form" onSubmit={submit}>
        <input className="sf-name" placeholder="网站名称（如：软件学院官网）" value={form.name} onChange={set('name')} />
        <input className="sf-url" placeholder="网址（https://…）" value={form.url} onChange={set('url')} />
        <input className="sf-type" placeholder="类型（如 college）" value={form.type} onChange={set('type')} />
        <input className="sf-freq" type="number" min="1" placeholder="频率(小时)" value={form.frequency_hours} onChange={set('frequency_hours')} />
        <input className="sf-kw" placeholder="关键词（逗号分隔）" value={form.keywords} onChange={set('keywords')} />
        <input className="sf-cs" placeholder="正文选择器（可选，如 #Content1）" value={form.content_selector} onChange={set('content_selector')} />
        <button className="btn" type="submit">{editing === null ? '添加网站' : '保存修改'}</button>
        {editing !== null && (
          <button className="btn" type="button" onClick={() => { setEditing(null); setForm(emptyForm) }}>取消</button>
        )}
      </form>

      {loading && <p className="hint">加载中…</p>}
      {!loading && sites.length === 0 && <p className="hint">还没有监控网站，用上面的表单添加一个吧</p>}
      {sites.map((s) => (
        <div key={s.index} className="site-card">
          <div className="site-main">
            <h3 className="site-name">
              {s.name} <span className="site-type">({s.type})</span>
            </h3>
            <p className="site-url">{s.url}</p>
            <p className="site-meta">
              频率 {s.frequency_hours}h · 关键词 {(s.keywords || []).join('、') || '—'}
              {s.content_selector ? ` · 选择器 ${s.content_selector}` : ''}
            </p>
          </div>
          <div className="site-actions">
            <button className="mini-btn" onClick={() => edit(s.index)}>编辑</button>
            <button className="mini-btn" onClick={() => remove(s.index)}>删除</button>
          </div>
        </div>
      ))}
    </>
  )
}

export default SitesPanel
