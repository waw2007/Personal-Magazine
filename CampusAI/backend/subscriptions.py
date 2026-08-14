"""关键词订阅：用户自定义「关注主题」，命中即高亮 + 主动推送。

数据存 data/subscriptions.json（列表 [{id, keyword}]），与倒数日事件同样的 CRUD 模式。
命中判定：标题 / 摘要 / 关键词标签中任一包含关注词（不区分大小写）。
"""

import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUB_PATH = os.path.join(BASE_DIR, "data", "subscriptions.json")
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed_news.json")


def load_subscriptions():
    if not os.path.exists(SUB_PATH):
        return []
    with open(SUB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_subscriptions(subs):
    with open(SUB_PATH, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=4)
    return subs


def load_processed():
    if not os.path.exists(PROCESSED_PATH):
        return []
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_subscriptions():
    subs = load_subscriptions()
    return {"count": len(subs), "data": subs}


def add_subscription(keyword):
    """添加关注词；空词或已存在返回 None，否则返回新增项。"""
    keyword = (keyword or "").strip()
    if not keyword:
        return None
    subs = load_subscriptions()
    if any(s.get("keyword") == keyword for s in subs):
        return None
    new_id = max([s.get("id", 0) for s in subs], default=0) + 1
    item = {"id": new_id, "keyword": keyword}
    subs.append(item)
    save_subscriptions(subs)
    return item


def remove_subscription(sub_id):
    """按 id 删除关注词；删到返回 True，否则 False。"""
    subs = load_subscriptions()
    before = len(subs)
    subs = [s for s in subs if s.get("id") != sub_id]
    save_subscriptions(subs)
    return len(subs) != before


def _matched_keywords(text, subs):
    """返回 text 命中的所有关注词（大小写不敏感）。"""
    lowered = text.lower()
    return [s["keyword"] for s in subs if s.get("keyword") and s["keyword"].lower() in lowered]


def matching_news():
    """返回命中任一关注词的信息（排除失效/过期），附带 matched 字段，按重要度降序。"""
    subs = load_subscriptions()
    keywords = [s["keyword"] for s in subs if s.get("keyword")]
    if not keywords:
        return {"count": 0, "data": [], "subscriptions": []}

    out = []
    for n in load_processed():
        if n.get("invalid") or n.get("expired"):
            continue
        text = " ".join([
            str(n.get("title", "")),
            str(n.get("summary", "")),
            " ".join(n.get("keywords", []) or []),
        ])
        matched = _matched_keywords(text, subs)
        if matched:
            out.append({**n, "matched": matched})

    out.sort(key=lambda n: n.get("importance", 0), reverse=True)
    return {"count": len(out), "data": out, "subscriptions": keywords}
