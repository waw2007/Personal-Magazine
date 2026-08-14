import json
import os
from datetime import datetime, date


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_PATH = os.path.join(BASE_DIR, "data", "events.json")


def load_events():
    if not os.path.exists(EVENTS_PATH):
        return []
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events):
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    return events


def days_left(date_str):
    """距今天数：正数=未来，0=今天，负数=已过；日期格式错误返回 None。"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return (d - date.today()).days


def enrich(event):
    """给事件附加倒数天数、状态、展示文案。"""
    d = days_left(event.get("date"))

    if d is None:
        status = "invalid"
        label = "日期格式错误"
    elif d > 0:
        status = "upcoming"
        label = f"还有 {d} 天"
    elif d == 0:
        status = "today"
        label = "就是今天！"
    else:
        status = "past"
        label = f"已过 {-d} 天"

    urgent = (d is not None) and (0 <= d <= 7)
    return {**event, "days_left": d, "status": status, "label": label, "urgent": urgent}
