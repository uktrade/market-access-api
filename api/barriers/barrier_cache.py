from django.core.cache import cache


BARRIERS_PREFIX = 'barriers/'


def get(pk):
    return cache.get(f"{BARRIERS_PREFIX}/{pk}")


def delete(pk):
    cache.delete(f"{BARRIERS_PREFIX}/{pk}")


def set(pk, obj):
    cache.set(f"{BARRIERS_PREFIX}/{pk}", obj, 120)
