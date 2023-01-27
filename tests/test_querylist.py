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
buster = Dog(number=71.19, name="Buster", owner="Robin")


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
        ("distance__meters", "distance__meters", operator.eq),
        ("distance__meters__gte", "distance__meters", operator.ge),
    ],
)
def test__map_operation(input_key, expected_key, expected_operation):
    key, operation = QueryList._map_operation(input_key)
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
    with pytest.raises(AttributeError) as e:
        ql.filter(name__inside=["foo", "bar"])

    assert str(e.value) == "'str' object has no attribute 'inside'"


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
        (dict(name__len=4), True),
        (dict(name__len=69), False),
    ],
)
def test_dunder_operators(filter_kwargs, expected_match):
    assert QueryList._match_item(fido, **filter_kwargs) == expected_match


@pytest.mark.parametrize(
    "query, expected_value",
    [
        ("empty__len", 0),
        ("fibonacci__len", 5),
        ("empty__bool", False),
        ("zero__bool", False),
        ("positive__bool", True),
        ("naturals__bool", True),
        ("naturals__max", 4),
        ("naturals__min", 0),
        ("empty__all", True),  # python bug imo
        ("naturals__all", False),
        ("fibonacci__all", True),
        ("empty__any", False),
        ("naturals__any", True),
        ("negative__abs", 69),
        ("positive__abs", 420),
        ("zero__abs", 0),
        ("fibonacci__sum", 19),
        ("empty__sum", 0),
    ],
)
def test_attribute_getters(query, expected_value):
    item = dict(
        fibonacci=(1, 2, 3, 5, 8),
        naturals=(0, 1, 2, 3, 4),
        negative=-69,
        positive=420,
        zero=0,
        empty=[],
    )
    assert QueryList._recursive_get_attribute(item, query) == expected_value


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
        param(
            description="attribute getter in query",
            apply_filter=lambda qs: qs.filter(name__len=4),
            expected_result=[fido, biko],
        ),
        param(
            description="attribute getter and dunder operation in query",
            apply_filter=lambda qs: qs.filter(name__len__lte=6),
            expected_result=[fido, biko, buster],
        ),
        param(
            description="attribute getter and dunder operation in query; also a normal field",
            apply_filter=lambda qs: qs.filter(name__len__lte=6, owner="Robin"),
            expected_result=[buster],
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


def test_filter_works_on_dicts_too():
    dogs = QueryList(
        [
            dict(number=15.72, name="Fido", owner="Sam"),
            dict(number=31.44, name="Muttley", owner="Robin"),
            dict(number=47.17, name="Biko", owner="Sam"),
            dict(number=71.19, name="Buster", owner="Robin"),
        ]
    )
    assert dogs.filter(name="Muttley") == [dict(number=31.44, name="Muttley", owner="Robin")]


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


def test_subclass_filter_and_exclude_return_subclass_instance_not_querylist():
    class MyQueryList(QueryList):
        pass

    ql = MyQueryList([dict(foo="bar")])
    assert isinstance(ql.filter(foo="bar"), MyQueryList)
    assert isinstance(ql.exclude(foo="bar"), MyQueryList)


def test_register_operation_and_attribute_getter():
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

    _QueryList.register_attribute_getter("num_fs", lambda item: item.count("f"))
    ql = _QueryList(
        [
            dict(name="fff"),
            dict(name="ffffffffff"),
        ]
    )

    assert ql.filter(name__num_fs=3).first()["name"] == "fff"
    assert ql.filter(name__num_fs=10).first()["name"] == "ffffffffff"
    assert ql.filter(name__num_fs__gt=5).first()["name"] == "ffffffffff"
    assert "num_fs" in dict(_QueryList.attribute_getters)
    assert "num_fs" not in dict(QueryList.attribute_getters)


@parametrize(
    param := testparams("order_by", "expected_result"),
    [
        param(
            description="single numeric field",
            order_by=["number"],
            expected_result=[
                fido,
                muttley,
                biko,
                buster,
            ],
        ),
        param(
            description="single numeric field reversed",
            order_by=["-number"],
            expected_result=[
                buster,
                biko,
                muttley,
                fido,
            ],
        ),
        param(
            description="single str field",
            order_by=["name"],
            expected_result=[
                biko,
                buster,
                fido,
                muttley,
            ],
        ),
        param(
            description="single str field reversed",
            order_by=["-name"],
            expected_result=[
                muttley,
                fido,
                buster,
                biko,
            ],
        ),
        param(
            description="multiple str fields",
            order_by=["owner", "name"],
            expected_result=[
                buster,
                muttley,
                biko,
                fido,
            ],
        ),
        param(
            description="multiple str and numeric fields",
            order_by=["owner", "number"],
            expected_result=[
                muttley,
                buster,
                fido,
                biko,
            ],
        ),
        param(
            description="multiple str and numeric fields, one reversed",
            order_by=["-owner", "number"],
            expected_result=[
                fido,
                biko,
                muttley,
                buster,
            ],
        ),
        param(
            description="multiple str and numeric fields, both reversed",
            order_by=["-owner", "-number"],
            expected_result=[
                biko,
                fido,
                buster,
                muttley,
            ],
        ),
        param(
            description="multiple str fields, both reversed",
            order_by=["-owner", "-name"],
            expected_result=[
                fido,
                biko,
                muttley,
                buster,
            ],
        ),
        param(
            description="single field with attribute getter behind '__'",
            order_by=["name__len"],
            expected_result=[
                fido,
                biko,
                buster,
                muttley,
            ],
        ),
        param(
            description="single field with attribute getter behind '__', reversed",
            order_by=["-name__len"],
            expected_result=[
                muttley,
                buster,
                fido,
                biko,
            ],
        ),
        param(
            description="multiple fields, one with attribute getter behind '__', one reversed",
            order_by=["-name__len", "-number"],
            expected_result=[
                muttley,
                buster,
                biko,
                fido,
            ],
        ),
    ],
)
def test_order_by(param):
    dogs = _default()
    results = dogs.order_by(*param.order_by)
    assert results == param.expected_result
    assert isinstance(results, QueryList)


@pytest.mark.parametrize(
    "attribute_string, expected_result",
    [
        ("owner", "owner"),
        ("friend__name", "Friend"),
        ("friend__owner", "Someone else"),
        ("friend__friend__name", "FOAF"),
        ("friend__friend__name__len", 4),
        ("friend__friend__name__bool", True),
        ("friend__friend__name__max", "O"),
        ("friend__friend__name__min", "A"),
    ],
)
def test__recursive_get_attribute(attribute_string, expected_result):
    doggie = Dog(name="doggie", owner="owner", number=69)
    doggie.friend = Dog(name="Friend", owner="Someone else", number=420)
    doggie.friend.friend = Dog(name="FOAF", owner="Billy", number=666)
    assert QueryList._recursive_get_attribute(doggie, attribute_string) == expected_result

    # and with dicts -- requires some different setup
    doggie = dict(name="doggie", owner="owner", number=69)
    doggie["friend"] = dict(name="Friend", owner="Someone else", number=420)
    doggie["friend"]["friend"] = dict(name="FOAF", owner="Billy", number=666)
    assert QueryList._recursive_get_attribute(doggie, attribute_string) == expected_result


def test__recursive_get_attribute_fail():
    doggie = Dog(name="doggie", owner="owner", number=69)
    doggie.friend = Dog(name="Friend", owner="Someone else", number=420)
    with pytest.raises(AttributeError):
        QueryList._recursive_get_attribute(doggie, "friend__foo")

    doggie = dict(name="doggie", owner="owner", number=69)
    doggie["friend"] = dict(name="Friend", owner="Someone else", number=420)
    with pytest.raises(KeyError):
        QueryList._recursive_get_attribute(doggie, "friend__foo")
