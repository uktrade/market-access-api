def is_not_blank(s):
    return bool(s and s.strip())


def pretty_name(name):
    if is_not_blank(name):
        return ' '.join(map(str, [x.capitalize() for x in name.split(".")]))
    return name


def cleansed_username(user):
    if user is not None:
        if is_not_blank(user.first_name) and is_not_blank(user.last_name):
            return pretty_name(f"{user.first_name}.{user.last_name}")

        if is_not_blank(user.username):
            if "@" in user.username:
                return pretty_name(user.username.split("@")[0])
            else:
                return pretty_name(user.username)

        if is_not_blank(user.email):
            return pretty_name(user.email.split("@")[0])

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
