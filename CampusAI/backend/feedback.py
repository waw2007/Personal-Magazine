"""用户反馈学习：记录「已读 / 归档」行为，反向调整推荐权重（让推荐越用越懂你）。

反馈信号（前端卡片上的「✓ 已读」「归档」按钮触发）：
- read / unread       已读 +1 / 撤销 -1（正向：感兴趣）
- archive / unarchive 归档 +1 / 撤销 -1（负向：不感兴趣）

按「分类」与「关键词」两个维度累计计数，推荐时据此放大/缩小相关条目的权重。
增益设了封顶，避免个别行为无限放大，只做「轻微但持续」的个性化修正。
"""

import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "feedback.json")

# 每条反馈的增益（封顶值见 _dim_factor）
READ_BOOST = 0.04        # 每条「已读」+4%（最多累计 10 条 → +0.4）
ARCHIVE_PENALTY = 0.08   # 每条「归档」-8%（最多累计 5 条 → -0.4）

MAX_FACTOR = 1.6
MIN_FACTOR = 0.5


def load_feedback():
    if not os.path.exists(FEEDBACK_PATH):
        return {"categories": {}, "keywords": {}}
    with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feedback(fb):
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(fb, f, ensure_ascii=False, indent=4)


def record_feedback(category, keywords, action):
    """记录一次反馈。action ∈ {read, unread, archive, unarchive}。"""
    read_delta = 1 if action == "read" else (-1 if action == "unread" else 0)
    archive_delta = 1 if action == "archive" else (-1 if action == "unarchive" else 0)
    if read_delta == 0 and archive_delta == 0:
        return

    fb = load_feedback()

    def _apply(bucket, key):
        if not key:
            return
        entry = bucket.setdefault(key, {"read": 0, "archive": 0})
        entry["read"] = max(0, entry.get("read", 0) + read_delta)
        entry["archive"] = max(0, entry.get("archive", 0) + archive_delta)

    if category:
        _apply(fb.setdefault("categories", {}), category)
    for kw in keywords or []:
        _apply(fb.setdefault("keywords", {}), kw)

    save_feedback(fb)


def _dim_factor(stat):
    """单个维度（分类或关键词）的增益，有封顶。"""
    if not stat:
        return 0.0
    f = READ_BOOST * min(stat.get("read", 0), 10)
    f -= ARCHIVE_PENALTY * min(stat.get("archive", 0), 5)
    return f


def feedback_factor(news, fb=None):
    """返回该条目的反馈因子（1.0 中性；>1 上调，<1 下调），夹在 [MIN, MAX]。"""
    if fb is None:
        fb = load_feedback()
    factor = 1.0

    cat_stat = fb.get("categories", {}).get(news.get("category"))
    factor += _dim_factor(cat_stat)

    for kw in news.get("keywords", []) or []:
        factor += _dim_factor(fb.get("keywords", {}).get(kw))

    return max(MIN_FACTOR, min(MAX_FACTOR, factor))


def get_feedback_summary():
    """返回当前学到的权重（供 /feedback 查看，也便于验证学习效果）。"""
    return load_feedback()
