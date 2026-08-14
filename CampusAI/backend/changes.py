import json
import os
from datetime import date


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_PATH = os.path.join(BASE_DIR, "data", "seen.json")


def load_seen():
    """加载 {url: 首次发现日期} 字典；兼容旧版 URL 列表格式。"""
    if not os.path.exists(SEEN_PATH):
        return {}
    with open(SEEN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        # 旧格式：纯 URL 列表，无日期信息
        return {u: None for u in data}
    return data


def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=4)


def detect_new(news):
    """识别新增 URL，同时记录「首次发现日期」并为条目补 date 字段。

    首次运行（无 seen.json）静默建立基线，不标记任何新增，
    避免把历史通知一次性全部弹出来。
    返回新增 URL 集合，并更新 seen.json。
    """
    first_run = not os.path.exists(SEEN_PATH)
    seen = load_seen()
    today = date.today().isoformat()

    new_urls = set()
    for item in news:
        url = item.get("url")
        if not url:
            continue

        if url not in seen:
            seen[url] = today          # 记录首次发现日期
            if not first_run:
                new_urls.add(url)
        elif seen[url] is None:
            seen[url] = today          # 迁移旧数据：无日期的补今天

        # 补 date：优先爬虫从标题前缀提取的日期，否则用首次发现日期
        if not item.get("date"):
            item["date"] = seen.get(url) or today

    save_seen(seen)
    return new_urls
