import time

from django.db import connection
from django.urls import resolve


class SqlMonitor:
    def __init__(self):
        self.query_count = 0
        self.query_time = 0.0

    def __call__(self, execute, sql, params, many, context):
        start_time = time.time()
        try:
            return execute(sql, params, many, context)
        finally:
            self.query_count += 1
            self.query_time += time.time() - start_time


class SqlMonitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        sql_monitor = SqlMonitor()
        with connection.execute_wrapper(sql_monitor):
            response = self.get_response(request)

        print(f"sql.endpoint: {request.path}")
        print(f"sql.query_count: {sql_monitor.query_count}")
        print(f"sql.query_time: {sql_monitor.query_time}")

        return response
