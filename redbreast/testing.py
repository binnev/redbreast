"""Utility stuff for use in tests"""
import operator
from dataclasses import make_dataclass
from typing import Any, Optional, Protocol

import pytest


class TestParams(Protocol):
    """This is to help static type checkers detect the always-present "description" kwarg."""

    description: Optional[str]

    def __init__(self, *, description: str, **kwargs) -> None:
        ...


def parametrize(param_class: TestParams, values_list, *args, **kwargs):
    """Thin wrapper around pytest.mark.parametrize, which helps enforce keyword
    arguments in the parameters"""
    # the `id` field is what pycharm displays as the description for each individual test case.
    # Pytest usually auto-generates these (badly)
    values_list = [pytest.param(value, id=value.description) for value in values_list]
    return pytest.mark.parametrize("param", values_list, *args, **kwargs)


def testparams(*field_names) -> type[TestParams]:
    """Generates a dataclass to hold the given test parameters. The `description` field is always
    included, so we don't have to define it every time we write a test. Keyword arguments are
    enforced for readability. Typing is set to Optional[Any] for all fields, to keep the syntax
    as simple as possible (and anyway, PyCharm doesn't pick up any type hints from this generated
    class)."""
    field_names = field_names + ("description",)
    fields = [(name, Optional[Any], None) for name in field_names]
    return make_dataclass(cls_name="testparams", fields=fields)


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
