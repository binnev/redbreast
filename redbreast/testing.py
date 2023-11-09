"""Utility stuff for use in tests"""

import operator
import re
from typing import Optional, Protocol, Sequence

import pytest


class TestParams(Protocol):
    """This is to help static type checkers detect the always-present "description" kwarg."""

    description: Optional[str]

    def __init__(self, *, description: str, **kwargs) -> None:
        ...


class param:
    """
    Shadows pytest.param, but the values go in the **kwargs, not the *args.
    """

    def __init__(
        self,
        *,  # force kwargs
        marks: tuple = (),
        id: Optional[str] = None,
        **kwargs,
    ):
        self.marks = marks
        self.id = id
        self.kwargs = kwargs


def parametrize(argnames: str | Sequence[str], params: Sequence[param], **kwargs):
    """
    Wraps pytest.mark.parametrize.
    Unpacks the redbreast.params into pytest.params with positional arguments.
    """

    # convert argnames to a list of strings.
    # This dictates the order in which the values should appear.
    if isinstance(argnames, str):
        argnames = re.split(", |,", argnames)  # match comma+space and comma
    else:
        argnames = list(argnames)

    # convert the list of redbreast.params into pytest.params
    argvalues = []
    for p in params:
        # check the param.kwargs exactly match the required argnames
        expected_args = set(argnames)
        passed_kwargs = set(p.kwargs.keys())
        if missing := expected_args.difference(passed_kwargs):
            raise TypeError(
                f"Param with id={p.id!r} is missing these kwargs: {sorted(missing)}"
            )
        if unexpected := passed_kwargs.difference(expected_args):
            raise TypeError(
                f"Param with id={p.id!r} received unexpected kwargs: {sorted(unexpected)}"
            )

        # Get the positional args in the correct order (matching the order of argnames)
        values = [p.kwargs.get(n) for n in argnames]
        arg_value = pytest.param(*values, marks=p.marks, id=p.id)
        argvalues.append(arg_value)
    return pytest.mark.parametrize(argnames, argvalues, **kwargs)


def set_difference(a, b):
    """Symmetrical difference between two sets. Useful for spotting the difference between a
    set of values and the expected set of values.
    E.g.

    diff = set_difference(serializer.data.keys(), expected_keys)
    assert not diff  # if they are different, the error message will tell you exactly how
    """
    a = set(a)
    b = set(b)
    difference = {*(a - b), *(b - a)}
    return difference


def assert_dicts_equal(a: dict, b: dict):
    """
    Compares two dictionaries for equality and gives a more useful error message than
    `assert dict1 == dict2`

    Suggested usage:
    `assert_dicts_equal(serializer.data, expected_data)`
    """
    # If they're equal we don't need to waste time with anything fancy
    if a == b:
        return

    keys_diff = set_difference(a.keys(), b.keys())
    assert (
        not keys_diff
    ), f"These keys are not present in both dictionaries: {sorted(keys_diff)}"
    for key, a_value in a.items():
        b_value = b[key]
        if isinstance(a_value, dict) and isinstance(b_value, dict):
            assert_dicts_equal(a_value, b_value)
        else:
            # if either of the values is a boolean, use `a is b` instead of `a == b`.
            # (because `1 == True` and `0 == False` in python!)
            func = (
                operator.is_
                if (isinstance(a_value, bool) or isinstance(b_value, bool))
                else operator.eq
            )
            assert func(
                a_value, b_value
            ), f"Values don't match for key '{key}': {b_value} != {a_value}"
