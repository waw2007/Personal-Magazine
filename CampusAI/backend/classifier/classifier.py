# classifier.py


# ==========================
# 新闻分类器
# ==========================


def classify_one(news):


    title = news.get(
        "title",
        ""
    )


    category = "其他"



    # 教务类

    if any(
        word in title
        for word in [
            "选课",
            "考试",
            "培养",
            "课程",
            "教学"
        ]
    ):

        category="教务"



    # 奖学金

    elif any(
        word in title
        for word in [
            "奖学金",
            "奖励",
            "评优"
        ]
    ):

        category="奖助学金"




    # 比赛

    elif any(
        word in title
        for word in [
            "比赛",
            "竞赛",
            "获奖"
        ]
    ):

        category="竞赛"



    # 就业

    elif any(
        word in title
        for word in [
            "招聘",
            "就业",
            "实习"
        ]
    ):

        category="就业"



    # 科研

    elif any(
        word in title
        for word in [
            "科研",
            "论文",
            "博士",
            "研究生"
        ]
    ):

        category="科研"



    news["category"] = category


    return news





# ==========================
# 批量分类
# ==========================


def classify_all(news_list):


    result=[]


    for news in news_list:


        item = classify_one(
            news.copy()
        )


        result.append(
            item
        )


    return result