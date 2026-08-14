import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed_news.json"
)



def load_news():

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def get_all_news():

    news = load_news()

    return news



def get_news_by_id(news_id):

    news = load_news()


    for item in news:

        if item["id"] == news_id:

            return item


    return None



def get_top_news(limit=5):

    news = load_news()


    return sorted(
        news,
        key=lambda x:x["importance"],
        reverse=True
    )[:limit]