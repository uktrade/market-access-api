from django.core.cache import cache


def get_item(pk):
    return cache.get(pk)


def delete_item(pk):
    cache.delete(pk)


def set_item(pk, obj):
    cache.set(pk, obj, 120)
