from profile.user_profile import load_profile
from summarizer.deepseek import rank_news


def _keyword_score(news, profile):
    """规则兜底：基于兴趣词的硬匹配打分（LLM 不可用时的降级方案）。"""
    text = (
        str(news.get("title", ""))
        + str(news.get("keywords", []))
    )
    score = news.get("importance", 0)
    reason = []
    for interest in profile.get("interests", []):
        if interest in text:
            score += 5
            reason.append("匹配兴趣:" + interest)
    return score, reason


def recommend_news(news_list, top_n=5):
    """为每条新闻计算推荐分并排序，返回 (top_n 条, 打分引擎)。

    - 优先用 LLM 语义打分（rank_news）
    - 无 key / 调用失败时退化为关键词硬匹配
    返回的每条结果保留完整字段（title/url/summary/... 供前端渲染），
    额外附加 recommend_score 与 reason。
    """
    profile = load_profile()

    ranked = rank_news(profile, news_list)
    engine = "llm" if ranked else "keyword"

    result = []
    for news in news_list:
        item = dict(news)

        if ranked and news.get("id") in ranked:
            score, reason = ranked[news["id"]]
        else:
            score, reasons = _keyword_score(news, profile)
            reason = "、".join(reasons) if reasons else "综合重要性"

        item["recommend_score"] = score
        item["reason"] = reason
        result.append(item)

    result.sort(key=lambda x: x["recommend_score"], reverse=True)
    return result[:top_n], engine
