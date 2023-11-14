from unittest.mock import patch

import pytest

import redbreast
from redbreast.testing import (
    assert_dicts_equal,
    set_difference,
)


def test_param_incorrect_usages():
    with pytest.raises(TypeError) as e:
        redbreast.param()
    assert str(e.value) == "param.__init__() missing 1 required positional argument: 'description'"

    with pytest.raises(TypeError) as e:
        redbreast.param("description", True, 420, "help")
    assert str(e.value) == "param.__init__() takes 2 positional arguments but 5 were given"


@pytest.mark.parametrize(
    "argnames_format",
    [
        "a, b",
        "a,b",
        ["a", "b"],
    ],
)
def test_parametrize_handles_different_argnames_formats(argnames_format):
    input_params = [
        redbreast.param("first", a=1, b=2),
        redbreast.param("second", a=3, b=4),
    ]
    expected_pytest_params = [
        pytest.param(1, 2, id="first"),
        pytest.param(3, 4, id="second"),
    ]
    with patch("redbreast.testing.pytest.mark.parametrize", return_value="boo") as mock:
        assert redbreast.parametrize(argnames_format, input_params) == "boo"
        mock.assert_called_with(["a", "b"], expected_pytest_params)


@pytest.mark.parametrize(
    "input_param, expected_error_msg",
    [
        (
            redbreast.param("description"),
            "Param with id='description' is missing these kwargs: ['a', 'b']",
        ),
        (
            redbreast.param("description", a=1),
            "Param with id='description' is missing these kwargs: ['b']",
        ),
        (
            redbreast.param("description", id=None, a=1),
            "Param with id='description' is missing these kwargs: ['b']",
        ),
        (
            redbreast.param("first", a=1),
            "Param with id='first' is missing these kwargs: ['b']",
        ),
        (
            redbreast.param("second"),
            "Param with id='second' is missing these kwargs: ['a', 'b']",
        ),
        (
            redbreast.param("third", a=1, b=2, c=3),
            "Param with id='third' received unexpected kwargs: ['c']",
        ),
        (
            redbreast.param("fourth", a=1, b=2, c=3, d=4),
            "Param with id='fourth' received unexpected kwargs: ['c', 'd']",
        ),
    ],
)
def test_parametrize_catches_missing_or_extra_kwargs(input_param, expected_error_msg):
    with pytest.raises(TypeError) as e:
        redbreast.parametrize("a, b", [input_param])

    assert str(e.value) == expected_error_msg


@redbreast.parametrize(
    "one, two",
    [
        redbreast.param(
            "in order, with id first",
            one=1,
            two=2,
        ),
        redbreast.param(
            "in order, with id last",
            one=1,
            two=2,
        ),
        redbreast.param(
            "wrong order",
            two=2,
            one=1,
        ),
    ],
)
def test_parametrize_kwargs_order_doesnt_matter(one, two):
    assert one == 1
    assert two == 2


@redbreast.parametrize(
    "are_planets_aligned, is_today_friday, name, request_count, cost, related_ids, handy_strings",
    [
        redbreast.param(
            "first",
            are_planets_aligned=True,
            is_today_friday=True,
            name="b",
            request_count=1,
            cost=4.20,
            related_ids={69, 420},
            handy_strings=["foo" "bar"],
        ),
        redbreast.param(
            "second",
            are_planets_aligned=False,
            is_today_friday=True,
            name="argh",
            request_count=420,
            cost=6.9,
            related_ids={999, 666},
            handy_strings=["baz"],
        ),
        redbreast.param(
            "third",
            are_planets_aligned=True,
            is_today_friday=False,
            name="arghhhhhh",
            request_count=9000,
            cost=420.69,
            related_ids={8, 9},
            handy_strings=["rrrr"],
        ),
        redbreast.param(
            "all falsy",
            are_planets_aligned=False,
            is_today_friday=False,
            name="",
            request_count=0,
            cost=0.0,
            related_ids=set(),
            handy_strings=[],
        ),
    ],
)
def test_parametrize_demo_usage(
    are_planets_aligned: bool,
    is_today_friday: bool,
    name: str,
    request_count: int,
    cost: float,
    related_ids: set[int],
    handy_strings: list[str],
):
    assert isinstance(are_planets_aligned, bool)
    assert isinstance(is_today_friday, bool)
    assert isinstance(name, str)
    assert isinstance(request_count, int)
    assert isinstance(cost, float)
    assert isinstance(related_ids, set)
    assert isinstance(handy_strings, list)


@pytest.mark.parametrize(
    "are_planets_aligned, is_today_friday, name, request_count, cost, related_ids, handy_strings",
    [
        pytest.param(
            True,
            True,
            "b",
            1,
            4.20,
            {69, 420},
            ["foo" "bar"],
            id="first",
        ),
        pytest.param(
            False,
            True,
            "argh",
            420,
            6.9,
            {999, 666},
            ["baz"],
            id="second",
        ),
        pytest.param(
            True,
            False,
            "arghhhhhh",
            9000,
            420.69,
            {8, 9},
            ["rrrr"],
            id="third",
        ),
        pytest.param(
            False,
            False,
            "",
            0,
            0.0,
            set(),
            [],
            id="all falsy",
        ),
    ],
)
def test_classic_pytest_parametrize_demo_usage(
    are_planets_aligned: bool,
    is_today_friday: bool,
    name: str,
    request_count: int,
    cost: float,
    related_ids: set[int],
    handy_strings: list[str],
):
    assert isinstance(are_planets_aligned, bool)
    assert isinstance(is_today_friday, bool)
    assert isinstance(name, str)
    assert isinstance(request_count, int)
    assert isinstance(cost, float)
    assert isinstance(related_ids, set)
    assert isinstance(handy_strings, list)


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
