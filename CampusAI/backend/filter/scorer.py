high_priority = {

    "四六级":5,
    "报名":5,
    "截止":5,
    "考试":5,
    "申请":4,
    "比赛":4,
    "竞赛":4,
    "选课":4,
    "奖学金":4,
    # 新来源关键词（研究生院 / 创新创业 / 教学运行保障）
    "推免":5,
    "免试":5,
    "保研":5,
    "补缓考":5,
    "缓考":4,
    "复试":4,
    "录取":4,
    "大赛":4

}


medium_priority = {

    "通知":1,
    "公告":1,
    "安排":1,
    "调整":1,
    "招生":2,
    "公示":2,
    "名单":2

}



def calculate_score(title):

    score = 0


    matched=[]


    for word,value in high_priority.items():

        if word in title:

            score += value

            matched.append(word)



    for word,value in medium_priority.items():

        if word in title:

            score += value

            matched.append(word)



    return score,matched