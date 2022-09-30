import pytest


pytestmark = pytest.mark.django_db
from redbreast.testing import parametrize, testparams, assert_dicts_equal, set_difference


@parametrize(
    param := testparams("a", "b", "c"),  # here we define the parameter names by creating a class
    [
        # here we create instances to hold the actual values.
        # keyword arguments are mandatory
        param(description="passing only description"),
        param(description="passing only a", a=1),
        param(description="passing only b", b=2),
        param(description="passing b and c", b=2, c=3),
        param(description="all kwargs passed", a=1, b=2, c=3),
        param(a=1, b=2, c=3, description="kwargs in different order"),
        param(a=1, b=2, c=3),  # pycharm won't give this a label because it has no description
    ],
)
def test_custom_parametrize(param):
    # parameters can be accessed by dot notation because param is a DataClass :)
    assert param.a in [1, None]
    assert param.b in [2, None]
    assert param.c in [3, None]
    assert type(param.description) in [str, type(None)]


@pytest.mark.parametrize(
    "values, expected_values, expected_diff",
    [
        (set(), set(), set()),
        (list(), list(), set()),
        (list(), set(), set()),
        (set(), list(), set()),
        ({1}, set(), {1}),
        ([1], set(), {1}),
        (list(), {1}, {1}),
        ([1], {2}, {1, 2}),
        ([1, 2, 3], {1, 2, 3}, set()),
        ([3, 2, 1], {1, 2, 3}, set()),
        ([3, 2, 1], {1, 2, 4}, {3, 4}),
        (["3", "2", "1"], {"1", "2", "4"}, {"3", "4"}),
        (["3", "2", "1"], {"1", "2", 3}, {"3", 3}),
        ({"1": 1, "2": 2}.keys(), {"1", "2"}, set()),
    ],
)
def test_set_difference(values, expected_values, expected_diff):
    assert set_difference(values, expected_values) == expected_diff


@pytest.mark.parametrize(
    "a, b",
    [
        (dict(), dict()),
        ({"foo": "foo"}, {"foo": "foo"}),
        ({"foo": "foo", "bar": "bar"}, {"bar": "bar", "foo": "foo"}),
        ({"foo": 3}, {"foo": 3.0}),  # based on equality, not on type
    ],
)
def test_assert_dicts_equal_match(a, b):
    assert_dicts_equal(a, b)


@pytest.mark.parametrize(
    "a, b, error_message",
    [
        (
            {"foo": "foo"},
            {"bar": "bar"},
            f"These keys are not present in both dictionaries: {['bar', 'foo']}",
        ),
        (
            {"foo": "foo", "bar": "bar"},
            {"foo": "foo", "bar": "bbbbbbbbbbbbbbbb"},
            "Values don't match for key 'bar': bbbbbbbbbbbbbbbb != bar",
        ),
        (
            {"foo": "foo", "bar": {"nested": "dict"}},
            {"foo": "foo", "bar": {"nested": "bbbbbbbbbbbbbbbb"}},
            "Values don't match for key 'nested': bbbbbbbbbbbbbbbb != dict",
        ),
        (
            {"foo": "foo", "bar": {"nested": "dict"}},
            {"foo": "foo", "bar": {"nested": "dict", "extra": "stuff"}},
            f"These keys are not present in both dictionaries: {['extra']}",
        ),
        (
            {"foo": "foo", "bar": {"nested": "dict"}},
            {"foo": "foo", "bar": "just a string"},
            "Values don't match for key 'bar': just a string != {'nested': 'dict'}",
        ),
    ],
)
def test_assert_dicts_equal_mismatch(a, b, error_message):
    with pytest.raises(AssertionError) as e:
        assert_dicts_equal(a, b)
    assert e.value.args[0] == error_message
