"""提醒 Agent：聚合「临近截止的通知 + 到期的倒数日事件」，产出统一待办清单。

核心理念「让信息找人」：不等人打开各栏目去翻，主动把「近期必须行动」的事项
收敛到一处，供前端统一弹通知 + 展示「提醒」面板。

数据来源：
- data/processed_news.json 里带 deadline（YYYY-MM-DD）的通知
- data/events.json 里用户手动维护的倒数日事件
"""

import json
import os
from datetime import date, datetime

from events import load_events, days_left


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed_news.json")


def load_processed():
    if not os.path.exists(PROCESSED_PATH):
        return []
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_deadline(value):
    """解析 deadline 为 date；非 YYYY-MM-DD 或非法返回 None。"""
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def build_reminders(deadline_window=7, event_window=7):
    """聚合待办，按紧迫度升序排序（今天最前，同天「截止」优先于「事件」）。

    返回列表，每项：
        type: "deadline" | "event"
        title / date / days_left / urgent(≤3天) / action / url / category
    """
    today = date.today()
    reminders = []

    # 1. 临近截止的通知（排除已失效 / 已过期）
    for n in load_processed():
        if n.get("invalid") or n.get("expired"):
            continue
        d = _parse_deadline(n.get("deadline"))
        if d is None:
            continue
        days = (d - today).days
        if not (0 <= days <= deadline_window):
            continue
        reminders.append({
            "type": "deadline",
            "title": n.get("title", ""),
            "date": n.get("deadline"),
            "days_left": days,
            "urgent": days <= 3,
            "action": n.get("suggestion") or n.get("summary", ""),
            "url": n.get("url"),
            "category": n.get("category", ""),
        })

    # 2. 到期的倒数日事件
    for e in load_events():
        d = days_left(e.get("date"))
        if d is None or d < 0:
            continue
        if d > event_window:
            continue
        reminders.append({
            "type": "event",
            "title": e.get("name", ""),
            "date": e.get("date"),
            "days_left": d,
            "urgent": d <= 3,
            "action": e.get("note", ""),
            "url": None,
            "category": "事件",
        })

    reminders.sort(key=lambda r: (r["days_left"], 0 if r["type"] == "deadline" else 1))
    return reminders


def get_reminders():
    """返回提醒总览：总数、今天、3 天内（不含今天），以及完整清单。"""
    data = build_reminders()
    today = [r for r in data if r["days_left"] == 0]
    urgent = [r for r in data if 0 < r["days_left"] <= 3]
    return {
        "count": len(data),
        "today": len(today),
        "urgent": len(urgent),
        "data": data,
    }
