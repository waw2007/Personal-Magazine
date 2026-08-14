import json
import os

from .scorer import calculate_score


keywords = [
    "通知",
    "公告",
    "报名",
    "考试",
    "比赛",
    "竞赛",
    "申请",
    "截止",
    "奖学金"
]


def filter_news(news):

    result = []

    for item in news:

        title = item["title"]

        score,matched = calculate_score(title)


        if score >=3:

            item["score"] = score

            item["matched"] = matched

            result.append(item)


    return sorted(
    result,
    key=lambda x:x["score"],
    reverse=True
)


if __name__ == "__main__":


    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


    NEWS_PATH = os.path.join(
        BASE_DIR,
        "data",
        "news.json"
    )


    with open(
        NEWS_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        news = json.load(f)



    important = filter_news(news)



    print(
        "发现重要信息:",
        len(important)
    )



    for item in important[:20]:

        print("----------------")

        print(
            item["title"]
        )

        print(
            item["matched"]
        )