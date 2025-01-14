from typing import Dict, Callable, Tuple

from rest_framework.pagination import CursorPagination

from api.barriers.models import Barrier, User

BARRIER_SCHEMA = {
    'name': 'Barrier',
    'columns': [
        {
            'name': 'id',
            'type': 'varchar',
            'nullable': False
        },
        {
            'name': 'title',
            'type': 'varchar',
            'nullable': False
        },
        {
            'name': 'created_on',
            'type': 'timestamp'
        }
    ]
}

USERS_SCHEMA = {
    'name': 'User',
    'columns': [
        {
            'name': 'id',
            'type': 'varchar',
            'nullable': False
        },
        {
            'name': 'first_name',
            'type': 'varchar',
        },
    ]
}


# Loaded into Dataflow
DATASET_SCHEMAS = {
    "tables": [
        BARRIER_SCHEMA,
        USERS_SCHEMA
    ]
}


def get_barriers():
    # return [
    #     {"id": 1, "title": "Barrier 1", "created_on": datetime.datetime.now()},
    # ]
    return Barrier.objects.all()


def get_users():
    # return [
    #     {"id": 1, "title": "Barrier 1", "created_on": datetime.datetime.now()},
    # ]
    return User.objects.all()



TABLES: Dict[str, Tuple[Callable, Dict, Tuple]] = {
    BARRIER_SCHEMA["name"]: (
        get_barriers,            # queryset
        BARRIER_SCHEMA,          # schema
        ("created_on", "pk")     # pagination ordering
    ),
    USERS_SCHEMA["name"]: (
        get_users,  # queryset
        USERS_SCHEMA,  # schema
        ("pk",)  # pagination ordering
    ),
}


def get_paginator(ordering):
    paginator = CursorPagination()
    paginator.page_size = 100
    paginator.ordering = ordering

    return paginator


def process_request(request):

    table = request.GET.get('table')
    qs_generator, table_schema, ordering = TABLES[table]
    qs = qs_generator().values(*[col["name"] for col in table_schema["columns"]])

    paginator = get_paginator(ordering)
    page = paginator.paginate_queryset(qs, request)
    next = paginator.get_next_link()

    return {
        'table': table,
        'rows': page,
        'next': next
    }
