from datetime import date

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


def _time_factor(date_str):
    """时间衰减因子：越新的信息权重越高。

    - 7 天内：1.0
    - 8-14 天：0.9
    - 15-30 天：0.8
    - 30 天以上：0.5
    无日期信息按 30 天处理。
    """
    if not date_str:
        return 0.5
    try:
        days = (date.today() - date.fromisoformat(str(date_str)[:10])).days
    except (ValueError, TypeError):
        return 0.5

    if days <= 7:
        return 1.0
    if days <= 14:
        return 0.9
    if days <= 30:
        return 0.8
    return 0.5


# LLM 批量打分前，先用关键词硬匹配缩小候选，避免输入/输出过长导致截断
CANDIDATE_LIMIT = 20


def recommend_news(news_list, top_n=5):
    """为每条新闻计算推荐分并排序，返回 (top_n 条, 打分引擎)。

    - 优先用 LLM 语义打分（rank_news）
    - 无 key / 调用失败时退化为关键词硬匹配
    - 候选超过 CANDIDATE_LIMIT 时先关键词预筛，控制 LLM 输入规模
    返回的每条结果保留完整字段（title/url/summary/... 供前端渲染），
    额外附加 recommend_score 与 reason。
    """
    profile = load_profile()

    # 过滤已失效链接（失效检测），不进入推荐
    news_list = [n for n in news_list if not n.get("invalid")]

    # 候选预筛：信息量较大时先用关键词缩小到 CANDIDATE_LIMIT
    if len(news_list) > CANDIDATE_LIMIT:
        pre = []
        for n in news_list:
            s, _ = _keyword_score(n, profile)
            pre.append((s, n))
        pre.sort(key=lambda x: x[0], reverse=True)
        candidates = [n for _, n in pre[:CANDIDATE_LIMIT]]
    else:
        candidates = news_list

    ranked = rank_news(profile, candidates)
    engine = "llm" if ranked else "keyword"

    result = []
    for news in candidates:
        item = dict(news)

        if ranked and news.get("id") in ranked:
            score, reason = ranked[news["id"]]
        else:
            score, reasons = _keyword_score(news, profile)
            reason = "、".join(reasons) if reasons else "综合重要性"

        item["recommend_score"] = round(score * _time_factor(news.get("date")), 1)
        item["reason"] = reason
        result.append(item)

    result.sort(key=lambda x: x["recommend_score"], reverse=True)
    return result[:top_n], engine
