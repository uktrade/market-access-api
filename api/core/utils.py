def cleansed_username(user):
    if user is not None:
        if user.username is not None and user.username.strip() != "":
            if "@" in user.username:
                return user.username.split("@")[0]
            else:
                return user.username
        elif user.email is not None and user.email.strip() != "":
            return user.email.split("@")[0]

    return None
