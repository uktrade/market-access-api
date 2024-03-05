import pytest

from api.core.test_utils import create_test_user
from api.feature_flags.models import Flag, FlagStatus, UserFlag

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def user():
    return create_test_user(
        first_name="Hey",
        last_name="Siri",
        email="hey@siri.com",
        username="heysiri",
    )


@pytest.fixture
def flag():
    return Flag.objects.create(name="Test", status=FlagStatus.ACTIVE)


def test_get_user_feature_flags(user, flag):
    user_flag = UserFlag.objects.create(user=user, flag=flag)

    assert user.flags.count() == 1
    assert user.flags.first() == user_flag
