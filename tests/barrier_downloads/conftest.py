from pytest import fixture

from api.core.test_utils import create_test_user


@fixture
def user():
    return create_test_user(
        first_name="Hey",
        last_name="Siri",
        email="hey@siri.com",
        username="heysiri",
    )
