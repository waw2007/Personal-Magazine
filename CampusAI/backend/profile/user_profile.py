import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


PROFILE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "user_profile.json"
)



def load_profile():

    if not os.path.exists(PROFILE_PATH):

        return {

            "grade":"",
            "major":"",
            "interests":[]

        }


    with open(
        PROFILE_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)




def save_profile(profile):


    with open(
        PROFILE_PATH,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(

            profile,

            f,

            ensure_ascii=False,

            indent=4

        )


    return profile