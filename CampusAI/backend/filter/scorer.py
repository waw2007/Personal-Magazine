high_priority = {

    "四六级":5,
    "报名":5,
    "截止":5,
    "考试":5,
    "申请":4,
    "比赛":4,
    "竞赛":4,
    "选课":4,
    "奖学金":4

}


medium_priority = {

    "通知":1,
    "公告":1,
    "安排":1,
    "调整":1

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