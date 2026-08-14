from profile.user_profile import load_profile



def calculate_score(news):


    profile = load_profile()


    score = news.get(
        "importance",
        0
    )


    reason = []



    text = (

        news.get(
            "title",
            ""
        )

        +

        str(
            news.get(
                "keywords",
                []
            )
        )

    )



    for interest in profile["interests"]:


        if interest in text:


            score += 5


            reason.append(
                "匹配兴趣:"+interest
            )



    return score, reason





def recommend_news(news_list):


    result=[]



    for news in news_list:


        score, reason = calculate_score(
            news
        )


        result.append(

            {

                "title":
                news["title"],


                "importance":
                news.get(
                    "importance",
                    0
                ),


                "recommend_score":
                score,


                "reason":
                reason

            }

        )



    result.sort(

        key=lambda x:x["recommend_score"],

        reverse=True

    )


    return result[:5]