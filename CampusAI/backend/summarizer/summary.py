import json
import os

from .deepseek import summarize_news


def generate_summary(news, index):
    title = news.get("title", "")
    source = news.get("source", "")
    category = news.get("category", "其他")
    keywords = news.get("matched", [])

    # 尝试用 LLM 生成摘要与建议
    ai = summarize_news(title, keywords, category, source)

    if ai:
        summary = ai.get("summary") or "该通知涉及校园相关事项，请关注具体内容。"
        suggestion = ai.get("suggestion") or "请查看原文确认具体时间和要求"
        deadline = ai.get("deadline")
    else:
        summary = "该通知涉及校园相关事项，请关注具体内容。"
        suggestion = "请查看原文确认具体时间和要求"
        deadline = None

    return {
        # 新闻编号
        "id": index,
        # 基础信息
        "title": title,
        "url": news.get("url", ""),
        "source": source,
        # 重要程度
        "importance": news.get("importance", news.get("score", 0)),
        # 命中的关键词
        "keywords": keywords,
        # 新闻分类
        "category": category,
        # LLM 摘要（无 key / 失败时降级为占位文案）
        "summary": summary,
        "suggestion": suggestion,
        "deadline": deadline,
        # 发布日期（标题前缀提取，或首次发现日期兜底）
        "date": news.get("date", ""),
        # 是否本次新发现（用于前端通知去重）
        "is_new": news.get("is_new", False),
    }


def generate_all(news_list):
    result = []
    for index, news in enumerate(news_list, start=1):
        result.append(generate_summary(news, index))
    return result


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    path = os.path.join(BASE_DIR, "data", "important_news.json")
    with open(path, "r", encoding="utf-8") as f:
        news = json.load(f)

    processed = generate_all(news)

    save_path = os.path.join(BASE_DIR, "data", "processed_news.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=4)

    print("生成摘要:", len(processed), "条")
    print("保存完成:", save_path)
