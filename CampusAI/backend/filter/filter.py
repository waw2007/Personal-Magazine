def match_keywords(title, keywords):

    score = 0

    matched = []


    for word in keywords:

        if word in title:

            score += 1

            matched.append(word)


    return {

        "score":score,

        "matched":matched

    }



if __name__=="__main__":


    test_title = "关于2026年四六级考试报名通知"


    keywords=[

        "四六级",

        "报名",

        "通知"

    ]


    result = match_keywords(
        test_title,
        keywords
    )


    print(result)