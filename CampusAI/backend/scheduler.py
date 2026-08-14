import json
import os
from datetime import datetime, timedelta

from crawler.crawler import load_websites


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "data", "site_state.json")

DEFAULT_FREQUENCY_HOURS = 24


# =========================
# 状态持久化（每个网站上次抓取时间）
# =========================

def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)


def _frequency(site):
    return site.get("frequency_hours", DEFAULT_FREQUENCY_HOURS)


# =========================
# 调度判断
# =========================

def due_sites(now=None):
    """返回「到了抓取时间」的网站列表（从未抓过的一律视为到期）。"""
    now = now or datetime.now()
    sites = load_websites()
    state = load_state()

    due = []
    for site in sites:
        last = state.get(site["url"])
        if last is None:
            due.append(site)
            continue
        try:
            last_dt = datetime.fromisoformat(last)
        except ValueError:
            due.append(site)
            continue
        if now - last_dt >= timedelta(hours=_frequency(site)):
            due.append(site)

    return due


def mark_crawled(sites, now=None):
    """记录一组网站本次抓取完成时间。"""
    now = now or datetime.now()
    state = load_state()
    for site in sites:
        state[site["url"]] = now.isoformat()
    save_state(state)


def site_status(now=None):
    """返回每个网站的名称 / 频率 / 上次抓取 / 距下次抓取分钟数（供 /pipeline/status 展示）。"""
    now = now or datetime.now()
    state = load_state()

    out = []
    for site in load_websites():
        last = state.get(site["url"])
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                next_dt = last_dt + timedelta(hours=_frequency(site))
                due_in = max(0, int((next_dt - now).total_seconds() // 60))
            except ValueError:
                last_dt = None
                due_in = 0
        else:
            last_dt = None
            due_in = 0

        out.append({
            "name": site["name"],
            "frequency_hours": _frequency(site),
            "last_run": last_dt.isoformat() if last_dt else None,
            "due_in_minutes": due_in,
        })

    return out
