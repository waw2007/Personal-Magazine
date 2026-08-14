const CATEGORY_CLASS = {
  教务: 'cat-edu',
  奖助学金: 'cat-award',
  竞赛: 'cat-race',
  就业: 'cat-job',
  科研: 'cat-research',
  其他: 'cat-other',
}

function NewsCard({ item, isRead, isArchived, onToggleRead, onToggleArchive }) {
  const catClass = CATEGORY_CLASS[item.category] || 'cat-other'
  const high = item.importance >= 5
  const key = item.url || String(item.id)

  return (
    <article className={`card ${isRead ? 'read' : ''}`}>
      <div className="card-top">
        <span className={`badge ${catClass}`}>{item.category}</span>
        <span className="source">{item.source}</span>
        {item.date && <span className="date">📅 {item.date}</span>}
        {isRead && <span className="read-tag">已读</span>}
        <span className={`importance ${high ? 'high' : ''}`}>重要度 {item.importance}</span>
      </div>

      <h2 className="title">
        <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a>
      </h2>

      <p className="summary">{item.summary}</p>

      {item.deadline && <p className="deadline">⏰ 截止：{item.deadline}</p>}

      {item.reason && <p className="reason">🎯 推荐理由：{item.reason}</p>}

      <div className="card-bottom">
        <div className="keywords">
          {(item.keywords || []).map((k) => <span key={k} className="kw">#{k}</span>)}
        </div>
        <div className="card-actions">
          <button className="mini-btn" onClick={() => onToggleRead(key)}>
            {isRead ? '标为未读' : '✓ 已读'}
          </button>
          <button className="mini-btn" onClick={() => onToggleArchive(key)}>
            {isArchived ? '恢复' : '归档'}
          </button>
          <a className="link" href={item.url} target="_blank" rel="noreferrer">查看原文 →</a>
        </div>
      </div>
    </article>
  )
}

export default NewsCard
