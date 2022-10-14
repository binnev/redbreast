# Robin's python utilities

<img src="https://github.com/binnev/redbreast/raw/main/logo.png"/>

### Installation

```
pip install redbreast
```

## QueryList

Do you want that sweet Django QuerySet filtering, but your objects aren't in a database, and you also don't want to
write a filter / list comprehension? The QueryList is the object for you!

### Usage

Let's do some setup. We want to investigate the following group of dogs:

```python
from dataclasses import dataclass
from redbreast.querylist import QueryList


@dataclass
class Dog:
    name: str
    owner: str
    number: float


fido = Dog(number=15.72, name="Fido", owner="Sam")
muttley = Dog(number=31.44, name="Muttley", owner="Robin")
biko = Dog(number=47.17, name="Biko", owner="Sam")
buster = Dog(number=71.19, name="Buster", owner="Robin")

dogs = QueryList([fido, muttley, biko, buster])
```

#### `filter`

We can `filter` for strict equality:

```python
dogs.filter(name="Muttley").first()
# Dog(name='Muttley', owner='Robin', number=31.44)
```

Or we can do django-like filtering with double underscores in the query:

```python
dogs.filter(number__gt=30, number__lt=70)
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Biko', owner='Sam', number=47.17),
# ]
```

Some python builtins are supported too:

```python
dogs.filter(name__len=4)
# [
#     Dog(name="Fido", owner="Sam", number=15.72), 
#     Dog(name="Biko", owner="Sam", number=47.17),
# ]

dogs.filter(name__len__gt=4)
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
# ]
```

You can chain multiple `__`s to access related objects and their attributes:

```python
doggie = Dog(name="doggie", owner="owner", number=69)
friend = Dog(name="Friend", owner="Someone else", number=420)
doggie.friend = friend
friend.friend = doggie
dogs = QueryList([doggie, friend])

dogs.get(friend__owner__len__gt=5)
# Dog(name='doggie', owner='owner', number=69)
```

#### `exclude`

`exclude` works too:

```python
dogs.exclude(owner="Sam")
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
# ]
```

#### `get`

The `get` method works like in Django -- it has to match exactly one object or it will raise an exception:

```python
# one object matches this query
dogs.get(name="Muttley")
# Dog(name='Muttley', owner='Robin', number=31.44)

# multiple objects match this query
dogs.get(owner="Robin")
# Traceback (most recent call last):
#   File ".../redbreast/querylist.py", line 34, in get
#     raise MultipleObjectsReturned
# django.core.exceptions.MultipleObjectsReturned

# no objects match this query
dogs.get(name="Penelope")
# Traceback (most recent call last):
#   File "/home/binnev/code/redbreast/redbreast/querylist.py", line 32, in get
#     raise ObjectDoesNotExist
# django.core.exceptions.ObjectDoesNotExist
```

Also, it's worth noting that QueryList can handle dictionaries (with `["key_lookup"]`) as well as objects (
with `.dot_lookup`). There can even be a mix of dictionaries and objects in the QueryList:

```python
things = QueryList(
    [
        {"name": "foo", "number": 69, "owner": "Jane"},  # dict
        Dog(name="bar", number=420, owner="Johnny"),  # object
    ]
)

print(things.get(owner="Jane"))
# {'name': 'foo', 'number': 69, 'owner': 'Jane'}

print(things.get(owner="Johnny"))
# Dog(name='bar', owner='Johnny', number=420)
```

#### `order_by`

`order_by` accepts one or more field names. Prepending a `"-"` to the field name will reverse the ordering for that field,
just like in Django.

```python
result = dogs.order_by("-owner", "number")
# [
#     Dog(name='Fido', owner='Sam', number=15.72), 
#     Dog(name='Biko', owner='Sam', number=47.17), 
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
# ]
```

Attribute getters and related object lookups can be included in the field name just like with `filter` calls:

```python
result = dogs.order_by("-name__len")
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
#     Dog(name='Fido', owner='Sam', number=15.72), 
#     Dog(name='Biko', owner='Sam', number=47.17), 
# ]

```

### Adding query methods

If you want to extend the functionality of QueryList by adding more dunder query methods, you can use
the `register_operation` method:

```python
def longer_than(item, target_length: int) -> bool:
    return len(item) > target_length


QueryList.register_operation("longerthan", longer_than)
dogs = QueryList(
    [
        dict(name="foo"),
        dict(name="fooooooooooooooo"),
    ]
)
dogs.filter(name__longerthan=3).first()["name"]
# "fooooooooooooooo"
```

### Caveats

Django's QuerySet is "lazy" -- meaning that `filter`/`exclude` calls do not actually hit the database. Instead they
simply add to an SQL query that the QuerySet remembers. This query is only sent to the database when you call `all`
/`first`/`last`/`exists` on the QuerySet.

By contrast, the QueryList is _not_ lazy. It will execute every `filter`/`exclude` call on the spot (thus reducing the
number of items it contains):

```python
dogs = dogs.filter(owner="Robin")
print(dogs)
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
# ]
```

## Parametrize

This is a thin wrapper around `pytest.mark.parametrize` that provides better oversight of tests with lots of parameters.

Consider the following (totally useless) test:

```python
@pytest.mark.parametrize(
    "a, b, c, d, e, f, g, h, i",
    [
        (True, 2, "foo", [], (), 69, 7, 8, ...),
        (False, 2, "bar", [], (), 420, 7, 8, ...),
        (None, 2, "baz", [], (), 666, 7, 8, ...),
        (True, 2, "baz", [], (), 9000, 7, 8, ...),
    ],
)
def test_parametrize(a, b, c, d, e, f, g, h, i):
    assert a in [True, False, None]
    assert b == 2
    assert isinstance(c, str)
    assert isinstance(d, list) and len(d) == 0
    assert isinstance(e, tuple) and len(e) == 0
    assert isinstance(f, int)
    assert g == 7
    assert h == 8
    assert i == Ellipsis
```

It was difficult to write because I couldn't quickly see which parameter name mapped to which value. Let's rewrite the
test using my parametrize wrapper:

```python
from redbreast.testing import parametrize, testparams


@parametrize(
    param := testparams("a", "b", "c", "d", "e", "f", "g", "h", "i"),
    [
        param(a=True, b=2, c="foo", d=[], e=(), f=69, g=7, h=8, i=...),
        param(a=False, b=2, c="bar", d=[], e=(), f=420, g=7, h=8, i=...),
        param(a=None, b=2, c="baz", d=[], e=(), f=666, g=7, h=8, i=...),
        param(a=True, b=2, c="baz", d=[], e=(), f=9000, g=7, h=8, i=...),
    ],
)
def test_parametrize(param):
    assert param.a in [True, False, None]
    assert param.b == 2
    assert isinstance(param.c, str)
    assert isinstance(param.d, list) and len(param.d) == 0
    assert isinstance(param.e, tuple) and len(param.e) == 0
    assert isinstance(param.f, int)
    assert param.g == 7
    assert param.h == 8
    assert param.i == Ellipsis
```

Much better. I can see at a glance that `g=7`, for example.

By invoking `param := testparams("a", "b", "c", ...)` we are creating a dataclass on the fly, which accepts
arguments `"a", "b", "c", ...`, and acts as our container for each test case. All arguments are optional, and default
to `None` if no value is supplied. Only keyword arguments are allowed, because the whole point is to make the test more
descriptive. Using positional args -- `param(1, 2, 3, ...)` -- is not allowed.

The dataclass has the default argument `description` to encourage you to describe each test case. The description is
also passed to pytest so that it shows up nicely in output. By default, pytest tries to generate a description based on
the items in the list:

```python
# test_testing.py::test_parametrize[param0] PASSED                         [ 25%]
# test_testing.py::test_parametrize[param1] PASSED                         [ 50%]
# test_testing.py::test_parametrize[param2] PASSED                         [ 75%]
# test_testing.py::test_parametrize[param3] PASSED                         [100%]
```

If we pass the following descriptions, they will show up in the output instead:

```python
@parametrize(
    param := testparams("a", "b", "c", "d", "e", "f", "g", "h", "i"),
    [
        param(description="1st test case", ...),
        param(description="2nd test case", ...),
        param(description="3rd test case", ...),
        param(description="4th test case", ...),
    ],
)
def test_parametrize(param):
    ...

# ============================= test session starts ==============================
# collecting ... collected 4 items
# 
# test_testing.py::test_parametrize[1st test case] PASSED                  [ 25%]
# test_testing.py::test_parametrize[2nd test case] PASSED                  [ 50%]
# test_testing.py::test_parametrize[3rd test case] PASSED                  [ 75%]
# test_testing.py::test_parametrize[4th test case] PASSED                  [100%]
# 
# ============================== 4 passed in 0.04s ===============================
```

Admittedly, our descriptions in this example aren't much more useful than pytest's ones, but you can go into as much
detail as you want. I sometimes write a small paragraph describing the motivation / context around a test case. 