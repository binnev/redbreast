"""Utility stuff for use in tests"""

import operator
import re
from typing import Sequence

import pytest


class param:
    """
    Shadows pytest.param, but forces you to pass values as **kwargs, *args, for better readability.
    Also, it is mandatory to pass a description. You can pass it as the only positional argument, or as a kwarg.
    (description serves the same function as pytest.param's `id` field)
    """

    def __init__(
        self,
        description: str,
        *,
        marks: tuple = (),
        **kwargs,
    ):
        self.marks = marks
        self.id = description
        self.kwargs = kwargs

    def _check_argnames_exactly_match(self, argnames: list[str]) -> None:
        """
        Check the param.kwargs exactly match the required argnames.
        This prevents you forgetting one of the values (or adding an extra, undeclared one).
        """
        expected_args = set(argnames)
        passed_kwargs = set(self.kwargs.keys())
        if missing := expected_args.difference(passed_kwargs):
            raise TypeError(f"Param with id={self.id!r} is missing these kwargs: {sorted(missing)}")
        if unexpected := passed_kwargs.difference(expected_args):
            raise TypeError(
                f"Param with id={self.id!r} received unexpected kwargs: {sorted(unexpected)}"
            )

    def to_pytest_param(self, argnames: list[str]) -> pytest.param:
        """
        Convert to a pytest.param with positional args in the correct order
        (matching the order of argnames).
        """
        self._check_argnames_exactly_match(argnames)
        values = (self.kwargs.get(n) for n in argnames)
        return pytest.param(*values, marks=self.marks, id=self.id)


def parametrize(
    argnames: str | Sequence[str],
    params: Sequence[param],
    **kwargs,
) -> pytest.mark.parametrize:
    """
    Wraps pytest.mark.parametrize.
    Unpacks the params into pytest.params with positional arguments.
    """

    # Convert argnames to a list of strings.
    # This dictates the order in which the values should appear.
    # (This is important, because they're stored in a dict and not necessarily ordered the same way)
    if isinstance(argnames, str):
        argnames = re.split(", |,", argnames)  # match comma+space and comma
    else:
        argnames = list(argnames)

    # Convert the list of params into pytest.params
    argvalues = [p.to_pytest_param(argnames) for p in params]
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
    assert not keys_diff, f"These keys are not present in both dictionaries: {sorted(keys_diff)}"
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
