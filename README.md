# Robin's python utilities

## QueryList

Do you want that sweet Django QuerySet filtering, but your objects aren't in a database, and you also don't want to
write a filter / list comprehension? The QueryList is the object for you!

### Installation

Install this library with

```
pip install redbreast
```

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

`exclude` works too:

```python
dogs.exclude(owner="Sam")
# [
#     Dog(name='Muttley', owner='Robin', number=31.44), 
#     Dog(name='Buster', owner='Robin', number=71.19),
# ]
```

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