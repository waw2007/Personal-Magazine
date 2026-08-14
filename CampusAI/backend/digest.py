import json
import os

from profile.user_profile import load_profile
from recommender.recommend import recommend_news
from summarizer.deepseek import generate_digest


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed_news.json")


def load_processed():
    if not os.path.exists(PROCESSED_PATH):
        return []
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def daily_digest(top_n=8):
    """生成「今日简报」：决策 Agent 把当天信息收敛成该做的几件事。

    返回 {"overview", "items", "engine", "based_on"}；
    LLM 不可用时降级为直接展示推荐结果。
    """
    news = load_processed()
    profile = load_profile()

    ranked, engine = recommend_news(news, top_n=top_n)
    digest = generate_digest(profile, ranked)

    if digest:
        return {
            "overview": digest.get("overview", ""),
            "items": digest.get("items", []),
            "engine": engine,
            "based_on": len(ranked),
        }

    # 降级兜底：无 LLM 时用推荐结果拼简报
    fallback = [
        {
            "title": it.get("title", ""),
            "why": it.get("reason", ""),
            "action": it.get("suggestion", ""),
            "deadline": it.get("deadline"),
        }
        for it in ranked[:3]
    ]
    return {
        "overview": "今日精选（LLM 未配置，展示推荐结果）",
        "items": fallback,
        "engine": engine,
        "based_on": len(ranked),
    }
