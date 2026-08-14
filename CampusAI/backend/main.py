from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import asyncio
import threading
from datetime import datetime, timedelta
from contextlib import asynccontextmanager


from recommender.recommend import recommend_news
from pipeline import run_pipeline
from scheduler import due_sites, mark_crawled, site_status
from crawler.crawler import load_websites

from profile.user_profile import load_profile

from events import load_events, save_events, enrich

from digest import daily_digest

from pydantic import BaseModel


# =========================
# 定时抓取（每天自动跑 pipeline）
# =========================

_pipeline_lock = threading.Lock()
_pipeline_state = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "last_crawled": [],
}


def _run_pipeline_safe(sites=None):
    """在独立线程里跑 pipeline，锁防止并发。

    sites=None：全量抓取（手动触发）；sites=子集：增量抓取（定时调度）。
    """
    if not _pipeline_lock.acquire(blocking=False):
        return  # 已有任务在跑
    try:
        _pipeline_state["running"] = True
        run_pipeline(sites)
        # 记录抓取时间：全量时标记所有网站，增量时只标记本次抓取的网站
        crawled = sites if sites is not None else load_websites()
        mark_crawled(crawled)
        _pipeline_state["last_crawled"] = [s["name"] for s in crawled]
        _pipeline_state["last_result"] = "success"
    except Exception as e:
        _pipeline_state["last_result"] = f"error: {e}"
    finally:
        _pipeline_state["running"] = False
        _pipeline_state["last_run"] = datetime.now().isoformat()
        _pipeline_lock.release()


async def _scheduled_loop():
    """每分钟检查一次，抓取到期的网站（按各自 frequency_hours 频率）。"""
    while True:
        await asyncio.sleep(60)
        if _pipeline_state["running"]:
            continue
        due = due_sites()
        if due:
            threading.Thread(target=_run_pipeline_safe, args=(due,), daemon=True).start()


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(_scheduled_loop())
    yield
    task.cancel()


app = FastAPI(

    title="Campus AI Assistant",

    description="校园信息智能助手 MVP",

    version="0.6",

    lifespan=lifespan

)


# =========================
# CORS（允许前端跨域访问）
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =========================
# 数据读取
# =========================


def load_processed_news():


    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )


    path = os.path.join(

        BASE_DIR,

        "data",

        "processed_news.json"

    )


    if not os.path.exists(path):

        return []


    with open(

        path,

        "r",

        encoding="utf-8"

    ) as f:

        return json.load(f)




# =========================
# 首页
# =========================


@app.get("/")
def home():

    return {

        "message":
        "Campus AI Assistant is running",

        "version":
        "0.6"

    }



# =========================
# 状态
# =========================


@app.get("/status")
def status():


    news = load_processed_news()


    return {

        "system":
        "online",

        "news_count":
        len(news),

        "new_count":
        len([n for n in news if n.get("is_new")]),

        "new_items":
        [
            {"url": n.get("url"), "title": n.get("title")}
            for n in news
            if n.get("is_new")
        ],

        "version":
        "0.6"

    }





# =========================
# 全部新闻
# =========================


@app.get("/news")
def get_news():


    news = load_processed_news()


    return {

        "count":
        len(news),

        "data":
        news

    }




# =========================
# 重要新闻
# =========================


@app.get("/important")
def get_important():


    news = load_processed_news()


    important = [

        item

        for item in news

        if item.get(
            "importance",
            0
        ) >= 8

    ]


    return {

        "count":
        len(important),

        "data":
        important

    }




# =========================
# 搜索
# =========================


@app.get("/search")
def search_news(

    q: str = Query(
        ...,
        description="搜索关键词"
    )

):


    news = load_processed_news()


    result=[]


    for item in news:


        text = (

            item.get(
                "title",
                ""
            )

            +

            str(
                item.get(
                    "keywords",
                    ""
                )
            )

            +

            item.get(
                "summary",
                ""
            )

        )


        if q in text:


            result.append(item)



    return {

        "keyword":
        q,

        "count":
        len(result),

        "data":
        result

    }





# =========================
# 最新信息
# =========================


@app.get("/latest")
def latest_news():


    news = load_processed_news()


    return {

        "count":
        len(news[:5]),

        "data":
        news[:5]

    }
# =========================
# 个性化推荐
# =========================


@app.get("/recommend")
def recommend():


    news = load_processed_news()


    result, engine = recommend_news(
        news
    )


    return {

        "message":
        "今日校园推荐",


        "profile":
        load_profile(),


        "engine":
        engine,


        "count":
        len(result),


        "data":
        result

    }
# =========================
# 今日简报
# =========================

@app.get("/digest")
def get_digest():
    return daily_digest()


# =========================
# 分类查看
# =========================

@app.get("/category/{category}")
def category_news(category: str):


    news = load_processed_news()


    result = []


    for item in news:

        if item.get("category") == category:

            result.append(item)


    return {

        "category": category,

        "count": len(result),

        "data": result

    }


# =========================
# 事件倒数日
# =========================

class EventIn(BaseModel):
    name: str
    date: str
    note: str = ""


@app.get("/events")
def get_events():
    evs = load_events()
    data = [enrich(e) for e in evs]

    def sort_key(e):
        dl = e["days_left"]
        if dl is None:
            return (2, 0)
        if dl < 0:
            return (1, dl)
        return (0, dl)

    data.sort(key=sort_key)
    return {"count": len(data), "data": data}


@app.post("/events")
def add_event(body: EventIn):
    evs = load_events()
    new_id = max([e.get("id", 0) for e in evs], default=0) + 1
    event = {
        "id": new_id,
        "name": body.name.strip(),
        "date": body.date.strip(),
        "note": body.note.strip(),
    }
    if not event["name"] or not event["date"]:
        return {"message": "name 和 date 必填"}
    evs.append(event)
    save_events(evs)
    return {"message": "已添加", "data": enrich(event)}


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    evs = load_events()
    before = len(evs)
    evs = [e for e in evs if e.get("id") != event_id]
    save_events(evs)
    if len(evs) == before:
        return {"message": "事件不存在"}
    return {"message": "已删除"}


# =========================
# 手动触发抓取 / 状态查询
# =========================

@app.post("/pipeline/run")
def trigger_pipeline():
    if _pipeline_state["running"]:
        return {"message": "pipeline 已在运行中"}
    threading.Thread(target=_run_pipeline_safe, daemon=True).start()
    return {"message": "pipeline 已开始运行"}


@app.get("/pipeline/status")
def pipeline_status():
    return {
        **_pipeline_state,
        "sites": site_status(),
    }