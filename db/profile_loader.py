from db.queries import get_user

def load_profile(user_id):
    user=get_user(user_id)

    profile={
        "name": user[0],
        "email": user[1],
        "phone": user[2]
    }
    return profile