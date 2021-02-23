#!/usr/bin/env python
import os
import sys
from django.conf import settings


# def initialise_debugger():
#     import debugpy

#     if not os.getenv("RUN_MAIN"):
#         debugpy.listen(("0.0.0.0", 3000))
#         sys.stdout.write("Start the VS Code debugger now, waiting...\n")
#         debugpy.wait_for_client()
#         sys.stdout.write("Debugger attached, starting server...\n")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # if settings.DEBUG:
    #     initialise_debugger()

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
