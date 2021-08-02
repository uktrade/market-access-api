import os
import pytest

from pytest_django.fixtures import _disable_native_migrations
import django
from django.conf import settings

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = False
    django.setup()


@pytest.fixture(scope="session")
def django_db_setup(
    request,
    django_test_environment: None,
    django_db_blocker,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
    django_db_createdb: bool,
    django_db_modify_db_settings: None,
) -> None:
    """Top level fixture to ensure test databases are available"""
    from django.test.utils import setup_databases, teardown_databases

    setup_databases_args = {
        "aliases": ["default"],
    }

    if not django_db_use_migrations:
        _disable_native_migrations()

    if django_db_keepdb and not django_db_createdb:
        setup_databases_args["keepdb"] = True

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            **setup_databases_args
        )

    def teardown_database() -> None:
        with django_db_blocker.unblock():
            try:
                teardown_databases(db_cfg, verbosity=request.config.option.verbose)
            except Exception as exc:
                request.node.warn(
                    pytest.PytestWarning(
                        "Error when trying to teardown test databases: %r" % exc
                    )
                )

    if not django_db_keepdb:
        request.addfinalizer(teardown_database)
