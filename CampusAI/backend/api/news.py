from fastapi import APIRouter

from services.news_service import (
    get_all_news,
    get_news_by_id,
    get_top_news
)


router = APIRouter(
    prefix="/news",
    tags=["校园新闻"]
)



@router.get("/")
def news_list():

    return {
        "count":
        len(get_all_news()),

        "data":
        get_all_news()
    }



@router.get("/{news_id}")
def news_detail(news_id:int):

    news=get_news_by_id(
        news_id
    )


    if news is None:

        return {
            "message":
            "新闻不存在"
        }


    return news




@router.get("/recommend/top")
def recommend():

    return {
        "data":
        get_top_news()
    }