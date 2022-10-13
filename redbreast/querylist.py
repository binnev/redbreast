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
    def _match_item(cls, item: Any, **search_terms) -> bool:
        """
        The search_terms are the search terms given to filter/exclude/get.
        The item is one of the items in the QueryList.
        This function decides whether the item matches the search terms.
        """
        for query, value in search_terms.items():
            key, operation = cls.map_operation(query)
            attribute = cls._get_attribute(item, key)
            if not operation(attribute, value):
                return False
        return True

    @classmethod
    def _get_attribute(cls, item: Any, attribute: str) -> Any:
        """Get the value off an item with either ["dict key lookup"] or .dot_lookup"""
        return item[attribute] if isinstance(item, dict) else getattr(item, attribute)

    @classmethod
    def _recursive_get_attribute(cls, item: Any, sssssssssssssss: str) -> Any:
        attributes = sssssssssssssss.split("__")
        for attribute in attributes:
            item = cls._get_attribute(item, attribute)
        return item

    @classmethod
    def map_operation(cls, query: str) -> tuple[str, Callable]:
        """
        Fetch the key (parameter name) and operation (a function) given a query parameter.

        The default operator is equality (=)
        E.g. if query="name" -> key="name", operator=operator.eq

        If the query contains dunders (__) we attempt to fetch the relevant operation from the
        class' operations registry.
        E.g. if query="name__contains" -> key="name", operation=operator.contains
        """
        key, *dunder_operation = query.split("__", maxsplit=1)
        if dunder_operation:
            operations = dict(cls.operations)
            try:
                operation = operations[dunder_operation[0]]
            except KeyError:
                raise ValueError(f"QueryList received unknown filter operation: {query}")
        else:
            operation = operator.eq
        return key, operation

    @classmethod
    def register_operation(cls, name: str, function: Callable):
        """
        Register a new operation that can be triggered with a dunder query parameter. Name should
        be the name of the operation after the "__".

        So if you want to be able to do .filter(name__islongerthan=5), you should do:

        def is_longer_than(item, target_length):
            return len(item) > target_length

        QuerySet.register("islongerthan", is_longer_than)
        """
        cls.operations += ((name, function),)

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

    def order_by(self, *fields: str) -> "QueryList":
        class comparer:
            def __init__(self, value: Any, reverse: bool):
                self.value = value
                self.reverse = reverse

            def __eq__(self, other):
                return other.value == self.value

            def __lt__(self, other):
                if self.reverse:
                    return other.value < self.value
                else:
                    return self.value < other.value

        def comparison_func(item):
            output = []
            for field in fields:
                reverse = False
                if field.startswith("-"):
                    reverse = True
                    field = field.removeprefix("-")

                output.append(comparer(self._get_attribute(item, field), reverse))
            return tuple(output)

        return self.__class__(sorted(self, key=comparison_func))
