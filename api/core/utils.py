def cleansed_username(user):
    if user is not None:
        if user.first_name.strip() and user.last_name.strip():
            return f"{user.first_name} {user.last_name}"
        
        if user.username.strip():
            if "@" in user.username:
                return user.username.split("@")[0]
            else:
                return user.username
        
        if user.email.strip():
            return user.email.split("@")[0]

    return None


class EchoUTF8:
    """
    Writer that echoes written data and encodes to utf-8 if necessary.
    Used for streaming large CSV files, defined as per
    https://docs.djangoproject.com/en/2.0/howto/outputting-csv/.
    """

    def write(self, value):
        """Returns value that is being "written"."""
        if isinstance(value, str):
            return value.encode('utf-8')
        return value