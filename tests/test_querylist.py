import operator
from dataclasses import dataclass

import pytest
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from redbreast.querylist import QueryList
from redbreast.testing import parametrize, testparams


@dataclass
class Dog:
    name: str
    owner: str
    number: float


fido = Dog(number=15.72, name="Fido", owner="Sam")
muttley = Dog(number=31.44, name="Muttley", owner="Robin")
biko = Dog(number=47.17, name="Biko", owner="Sam")
buster = dict(number=71.19, name="Buster", owner="Robin")


def _default():
    return QueryList([fido, muttley, biko, buster])


def test_empty_behaviour():
    empty = QueryList([])
    assert empty.count() == len(empty) == 0
    assert empty.exists() is False
    assert empty.first() is None
    assert empty.last() is None
    assert empty.all() == []


@pytest.mark.parametrize(
    "input_key, expected_key, expected_operation",
    [
        ("name", "name", operator.eq),
        ("distance__lt", "distance", operator.lt),
        ("distance__lte", "distance", operator.le),
        ("distance__gt", "distance", operator.gt),
        ("distance__gte", "distance", operator.ge),
    ],
)
def test_map_operation(input_key, expected_key, expected_operation):
    key, operation = QueryList.map_operation(input_key)
    assert key == expected_key
    assert operation == expected_operation


def test_all():
    list_instance = [1, 2, 3]
    qs = QueryList(list_instance)
    # with .all() we "cash in" the queryset and extract the objects, so should just be a list
    assert isinstance(qs.all(), list)
    assert not isinstance(qs.all(), QueryList)
    second_list_instance = qs.all()
    # output should be a copy, not the same object
    assert second_list_instance == list_instance
    assert second_list_instance is not list_instance


def test_first():
    qs = _default()
    assert qs.first() == fido


def test_last():
    qs = _default()
    assert qs.last() == buster


def test_get():
    qs = _default()

    # happy flow -- exactly one result
    assert qs.get(name="Biko") == biko

    # no results -- error
    with pytest.raises(ObjectDoesNotExist):
        qs.get(name="foobar")

    # more than one result -- error
    with pytest.raises(MultipleObjectsReturned):
        qs.get(number__gt=0)

    # positional args are not allowed
    with pytest.raises(TypeError):
        qs.get("foo")


def test_unknown_dunder_operation_raises_exception():
    ql = _default()
    with pytest.raises(ValueError) as e:
        ql.filter(name__inside=["foo", "bar"])

    assert str(e.value) == "QueryList received unknown filter operation: name__inside"


@parametrize(
    param := testparams("filter_kwargs", "expected_match"),
    [
        param(
            description="single normal kwarg match",
            filter_kwargs=dict(name="Fido"),
            expected_match=True,
        ),
        param(
            description="single normal kwarg no match",
            filter_kwargs=dict(name="London Paddington"),
            expected_match=False,
        ),
        param(
            description="two normal kwargs",
            filter_kwargs=dict(name="Fido", number=15.72),
            expected_match=True,
        ),
        param(
            description="two normal kwargs no match",
            filter_kwargs=dict(name="Fido", number=420),
            expected_match=False,
        ),
        param(
            description="mix of normal and dunder kwargs",
            filter_kwargs=dict(name="Fido", number__gte=10),
            expected_match=True,
        ),
        param(
            description="lots of dunder kwargs",
            filter_kwargs=dict(number__gt=15, number__gte=15.72, number__lt=16, number__lte=15.72),
            expected_match=True,
        ),
    ],
)
def test__match_item(param):
    assert QueryList._match_item(fido, **param.filter_kwargs) == param.expected_match


@pytest.mark.parametrize(
    "filter_kwargs, expected_match",
    [
        (dict(number__lt=15), False),
        (dict(number__lt=15.72), False),
        (dict(number__lt=16), True),
        (dict(number__lte=15), False),
        (dict(number__lte=15.72), True),
        (dict(number__lte=16), True),
        (dict(number__gt=15), True),
        (dict(number__gt=15.72), False),
        (dict(number__gt=16), False),
        (dict(number__gte=15), True),
        (dict(number__gte=15.72), True),
        (dict(number__gte=16), False),
        (dict(name__contains="foo"), False),
        (dict(name__contains="ido"), True),
        (dict(name__in=["foo"]), False),
        (dict(name__in=["foo", "Fido"]), True),
        (dict(name__in="Fido"), True),
    ],
)
def test_dunder_operators(filter_kwargs, expected_match):
    assert QueryList._match_item(fido, **filter_kwargs) == expected_match


@parametrize(
    param := testparams("apply_filter", "expected_result"),
    [
        param(
            description="single filter",
            apply_filter=lambda qs: qs.filter(owner="Sam"),
            expected_result=[fido, biko],
        ),
        param(
            description="filter with multiple kwargs",
            apply_filter=lambda qs: qs.filter(owner="Sam", number__lt=40),
            expected_result=[fido],
        ),
        param(
            description="multiple filters in series",
            apply_filter=lambda qs: qs.filter(owner="Sam").filter(number__lt=40),
            expected_result=[fido],
        ),
        param(
            description="if no items match filter we get an empty object",
            apply_filter=lambda qs: qs.filter(owner="foo"),
            expected_result=[],
        ),
        param(
            description="single exclude",
            apply_filter=lambda qs: qs.exclude(name="Fido"),
            expected_result=[muttley, biko, buster],
        ),
        param(
            description=(
                "multiple argument exclude should only exclude members for which *all* args match"
            ),
            apply_filter=lambda qs: qs.exclude(name="Fido", owner="Sam"),
            expected_result=[muttley, biko, buster],
        ),
        param(
            description="exclude in series can be used for 'any' type behaviour",
            apply_filter=(lambda qs: qs.exclude(name="Fido").exclude(owner="Sam")),
            expected_result=[muttley, buster],
        ),
        param(
            description="fancy filtering __lt",
            apply_filter=lambda qs: qs.filter(number__lt=20),
            expected_result=[fido],
        ),
        param(
            description="fancy filtering __gt",
            apply_filter=lambda qs: qs.filter(number__gt=20),
            expected_result=[muttley, biko, buster],
        ),
        param(
            description="fancy filtering multiple __kwargs",
            apply_filter=lambda qs: qs.filter(number__gt=20, number__lte=60),
            expected_result=[muttley, biko],
        ),
    ],
)
def test_filter_and_exclude(param):
    qs = _default()

    result = param.apply_filter(qs)
    assert isinstance(result, QueryList)
    assert result == param.expected_result


def test_filter_for_nonexistent_attribute_raises_error():
    qs = _default()
    with pytest.raises(AttributeError):
        qs.filter(energy=9000)

    qs = QueryList([dict(foo="bar")])
    with pytest.raises(KeyError):
        qs.filter(energy=9000)


def test_can_subclass_querylist_and_add_dunder_methods():
    class MyQueryList(QueryList):
        """QueryList subclass that supports case-insensitive contains and length comparison
        functions"""

        operations = QueryList.operations + (
            ("icontains", lambda string, search_term: search_term.lower() in string.lower()),
            ("islongerthan", lambda item, target_len: len(item) > target_len),
        )

    ql = MyQueryList(
        [
            dict(name="foo"),
            dict(name="fooooooooooooooo"),
        ]
    )

    assert ql.filter(name__islongerthan=3).first()["name"] == "fooooooooooooooo"
    assert ql.filter(name__icontains="OoOoOo").first()["name"] == "fooooooooooooooo"


def test_querylist_subclass_filter_and_exclude_return_subclass_instance_not_querylist():
    class MyQueryList(QueryList):
        pass

    ql = MyQueryList([dict(foo="bar")])
    assert isinstance(ql.filter(foo="bar"), MyQueryList)
    assert isinstance(ql.exclude(foo="bar"), MyQueryList)


def test_querylist_register_operation():
    class _QueryList(QueryList):
        """This subclass is only necessary to prevent editing the original QueryList and
        affecting other tests."""

        operations = QueryList.operations

    _QueryList.register_operation("islongerthan", lambda item, target_len: len(item) > target_len)
    ql = _QueryList(
        [
            dict(name="foo"),
            dict(name="fooooooooooooooo"),
        ]
    )

    assert ql.filter(name__islongerthan=3).first()["name"] == "fooooooooooooooo"
    assert "islongerthan" in dict(_QueryList.operations)
    assert "islongerthan" not in dict(QueryList.operations)
