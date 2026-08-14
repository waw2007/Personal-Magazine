import json
import os


from crawler.crawler import crawl

from filter.news_filter import filter_news

from classifier.classifier import classify_all

from summarizer.summary import generate_all

from changes import detect_new



# ==========================
# 基础路径
# ==========================


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)



NEWS_PATH = os.path.join(
    DATA_DIR,
    "news.json"
)


IMPORTANT_PATH = os.path.join(
    DATA_DIR,
    "important_news.json"
)


PROCESSED_PATH = os.path.join(
    DATA_DIR,
    "processed_news.json"
)




# ==========================
# 保存JSON
# ==========================


def save_json(data,path):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )





# ==========================
# Pipeline
# ==========================


def run_pipeline():


    print("======================")
    print("CampusAI Pipeline启动")
    print("======================")



    # ======================
    # 1 crawler
    # ======================

    print("\n[1] 正在抓取校园信息")


    news = crawl()


    save_json(
        news,
        NEWS_PATH
    )


    print(
        "新闻数量:",
        len(news)
    )





    # ======================
    # 2 filter
    # ======================


    print("\n[2] 正在筛选重要信息")


    important = filter_news(
        news
    )


    save_json(
        important,
        IMPORTANT_PATH
    )


    print(
        "重要信息:",
        len(important)
    )






    # ======================
    # 变更检测：对比已推送 URL，识别新增（首次运行静默建基线）
    # ======================

    new_urls = detect_new(important)
    for item in important:
        item["is_new"] = item.get("url") in new_urls
    print("新增信息:", len(new_urls))

    # ======================
    # 3 classifier
    # ======================


    print("\n[3] 正在分类信息")


    classified = classify_all(
        important
    )


    print(
        "分类完成:",
        len(classified)
    )







    # ======================
    # 4 summary
    # ======================


    print("\n[4] 正在生成摘要")


    processed = generate_all(
        classified
    )


    save_json(
        processed,
        PROCESSED_PATH
    )


    print(
        "摘要完成:",
        len(processed)
    )





    print("\n======================")
    print("Pipeline运行完成")
    print("======================")





if __name__ == "__main__":

    run_pipeline()