from unittest.mock import patch

import pytest

import redbreast
from redbreast.testing import (
    assert_dicts_equal,
    set_difference,
)


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
        redbreast.param(id="first", a=1, b=2),
        redbreast.param(id="second", a=3, b=4),
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
            redbreast.param(),
            "Param with id=None is missing these kwargs: ['a', 'b']",
        ),
        (
            redbreast.param(a=1),
            "Param with id=None is missing these kwargs: ['b']",
        ),
        (
            redbreast.param(id=None, a=1),
            "Param with id=None is missing these kwargs: ['b']",
        ),
        (
            redbreast.param(id="first", a=1),
            "Param with id='first' is missing these kwargs: ['b']",
        ),
        (
            redbreast.param(id="second"),
            "Param with id='second' is missing these kwargs: ['a', 'b']",
        ),
        (
            redbreast.param(id="third", a=1, b=2, c=3),
            "Param with id='third' received unexpected kwargs: ['c']",
        ),
        (
            redbreast.param(id="fourth", a=1, b=2, c=3, d=4),
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
            id="in order, with id first",
            one=1,
            two=2,
        ),
        redbreast.param(
            one=1,
            two=2,
            id="in order, with id last",
        ),
        redbreast.param(
            two=2,
            one=1,
            id="wrong order",
        ),
        redbreast.param(
            two=2,
            one=1,
        ),  # no label
    ],
)
def test_parametrize_kwargs_order_doesnt_matter(one, two):
    assert one == 1
    assert two == 2


@redbreast.parametrize(
    "a, b, c, d, e, f",
    [
        redbreast.param(
            id="first",
            a=True,
            b="b",
            c=1,
            d=4.20,
            e={69, 420},
            f=["foo" "bar"],
        ),
        redbreast.param(
            id="second",
            a=False,
            b="argh",
            c=420,
            d=6.9,
            e={999, 666},
            f=["baz"],
        ),
        redbreast.param(
            id="third",
            a=True,
            b="arghhhhhh",
            c=9000,
            d=420.69,
            e={8, 9},
            f=["rrrr"],
        ),
        redbreast.param(
            id="all falsy",
            a=False,
            b="",
            c=0,
            d=0.0,
            e=set(),
            f=[],
        ),
    ],
)
def test_parametrize_demo_usage(
    a: bool,
    b: str,
    c: int,
    d: float,
    e: set[int],
    f: list[str],
):
    assert isinstance(a, bool)
    assert isinstance(b, str)
    assert isinstance(c, int)
    assert isinstance(d, float)
    assert isinstance(e, set)
    assert isinstance(f, list)


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
