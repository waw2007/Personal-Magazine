import json
import os


from crawler.crawler import crawl, crawl_sites
from filter.news_filter import filter_news
from classifier.classifier import classify_all
from summarizer.summary import generate_all
from changes import detect_new


# ==========================
# 基础路径
# ==========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

NEWS_PATH = os.path.join(DATA_DIR, "news.json")
IMPORTANT_PATH = os.path.join(DATA_DIR, "important_news.json")
PROCESSED_PATH = os.path.join(DATA_DIR, "processed_news.json")


# ==========================
# 工具
# ==========================

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_dedup(existing, new, key="url"):
    """按 key 去重合并，new 在前、existing 在后。"""
    seen = set()
    out = []
    for item in new + existing:
        k = item.get(key)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


# ==========================
# Pipeline
# ==========================

def run_pipeline(sites=None):
    """跑一遍抓取流水线。

    sites=None：全量模式 —— 抓所有网站，重新处理全部信息（手动触发 / 首次）。
    sites=子集：增量模式 —— 只抓到期网站，合并进历史，仅对新增 URL 跑分类+摘要。
    """
    print("======================")
    print("CampusAI Pipeline启动", "（全量）" if sites is None else f"（增量 {len(sites)} 个网站）")
    print("======================")

    # ======================
    # 1 crawler（全量 or 子集）
    # ======================
    print("\n[1] 正在抓取校园信息")

    if sites is None:
        raw = crawl()
    else:
        new_raw = crawl_sites(sites)
        raw = merge_dedup(load_json(NEWS_PATH), new_raw)

    save_json(raw, NEWS_PATH)
    print("新闻总数:", len(raw))

    # ======================
    # 2 filter（对合并后的全部 raw 重新打分筛选，成本低）
    # ======================
    print("\n[2] 正在筛选重要信息")

    important = filter_news(raw)
    save_json(important, IMPORTANT_PATH)
    print("重要信息:", len(important))

    # ======================
    # 变更检测：对比已推送 URL，识别新增（首次运行静默建基线）
    # ======================
    new_urls = detect_new(important)
    for item in important:
        item["is_new"] = item.get("url") in new_urls
    print("新增信息:", len(new_urls))

    # ======================
    # 3 分类 + 4 摘要：只处理「尚未有摘要」的 URL
    # ======================
    existing_processed = [] if sites is None else load_json(PROCESSED_PATH)
    existing_urls = {p.get("url") for p in existing_processed}

    to_process = [it for it in important if it.get("url") not in existing_urls]
    print(f"\n[3][4] 需要分类+摘要的新条目: {len(to_process)}")

    classified = classify_all(to_process)
    processed_new = generate_all(classified)

    # 合并：新摘要在前，历史摘要靠后（去重）
    new_urls_set = {p.get("url") for p in processed_new}
    processed = processed_new + [
        p for p in existing_processed if p.get("url") not in new_urls_set
    ]

    # 排序：新增（is_new）优先，其次重要度降序
    processed.sort(key=lambda x: (not x.get("is_new", False), -x.get("importance", 0)))

    # 重排 id
    for i, item in enumerate(processed, start=1):
        item["id"] = i

    save_json(processed, PROCESSED_PATH)
    print("最终已处理信息:", len(processed))

    print("\n======================")
    print("Pipeline运行完成")
    print("======================")


if __name__ == "__main__":
    run_pipeline()
