import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_PATH = os.path.join(BASE_DIR, "data", "seen.json")


def load_seen():
    """加载已推送过的新闻 URL 列表。"""
    if not os.path.exists(SEEN_PATH):
        return []
    with open(SEEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=4)


def detect_new(news):
    """对比已推送的 URL，识别本次新增的新闻。

    首次运行（无 seen.json）静默建立基线，不标记任何新增，
    避免把历史通知一次性全部弹出来。
    返回新增 URL 集合，并更新 seen.json。
    """
    first_run = not os.path.exists(SEEN_PATH)
    seen = set(load_seen())

    if first_run:
        new_urls = set()
    else:
        new_urls = {
            item["url"]
            for item in news
            if item.get("url") and item["url"] not in seen
        }

    seen.update(item["url"] for item in news if item.get("url"))
    save_seen(sorted(seen))
    return new_urls
