import operator
from copy import deepcopy
from typing import Callable, Any

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class QueryList(list):
    """A list that you can filter like a Django QuerySet"""

    # registry of double-underscore method names and the functions they map to
    operations = (
        ("lt", operator.lt),
        ("lte", operator.le),
        ("gt", operator.gt),
        ("gte", operator.ge),
        ("contains", operator.contains),
        ("in", lambda a, b: a in b),
    )

    def filter(self, **kwargs) -> "QueryList":
        func = lambda item: self._match_item(item, **kwargs)
        return self.__class__(filter(func, self))

    def exclude(self, **kwargs) -> "QueryList":
        func = lambda item: not self._match_item(item, **kwargs)
        return self.__class__(filter(func, self))

    def get(self, **kwargs) -> Any:
        qs = self.filter(**kwargs)
        if len(qs) == 0:
            raise ObjectDoesNotExist
        if len(qs) > 1:
            raise MultipleObjectsReturned
        return self.filter(**kwargs)[0]

    @classmethod
    def _match_item(cls, item: Any, **kwargs):
        for key, value in kwargs.items():
            key, operation = cls.map_operation(key)
            attribute = item[key] if isinstance(item, dict) else getattr(item, key)
            if not operation(attribute, value):
                return False
        return True

    @classmethod
    def map_operation(cls, key: str) -> tuple[str, Callable]:
        key, *dunder_operation = key.split("__")
        operation = operator.eq
        if dunder_operation:
            operations = dict(cls.operations)
            try:
                operation = operations[dunder_operation[0]]
            except KeyError:
                raise ValueError(
                    f"QueryList received unknown filter operation: {key}__{dunder_operation[0]}"
                )
        return key, operation

    def all(self) -> list:
        return list(deepcopy(self))

    def exists(self) -> bool:
        return bool(self)

    def first(self) -> Any:
        return self[0] if self.exists() else None

    def last(self) -> Any:
        return self[-1] if self.exists() else None

    def count(self) -> int:
        return len(self)
