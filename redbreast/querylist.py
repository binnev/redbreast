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
        ("len", lambda a, b: len(a) == b),
    )

    # functions (mostly builtins) that can get some value of an item.
    attribute_getters = (
        ("len", len),
        ("bool", bool),
        ("max", max),
        ("min", min),
        ("all", all),
        ("any", any),
        ("abs", abs),
        ("sum", sum),
    )

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

    def order_by(self, *fields: str) -> list:
        class comparer:
            """
            Thin wrapper around an item that allows us to reverse the sorting on a per-field
            basis. Credit to black panda:
            https://stackoverflow.com/questions/37693373/how-to-sort-a-list-with-two-keys-but-one-in-reverse-order
            """

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
            """Returns a tuple of attributes of the item which `sorted` will use to compare it
            against its peers"""
            return tuple(
                comparer(
                    self._recursive_get_attribute(item, field.lstrip("-")),
                    reverse=field.startswith("-"),
                )
                for field in fields
            )

        return sorted(self, key=comparison_func)

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

    @classmethod
    def register_attribute_getter(cls, name: str, function: Callable):
        cls.attribute_getters += ((name, function),)

    @classmethod
    def _match_item(cls, item: Any, **search_terms) -> bool:
        """
        The search_terms are the search terms given to filter/exclude/get.
        The item is one of the items in the QueryList.
        This function decides whether the item matches the search terms.
        """
        for query, value in search_terms.items():
            key, operation = cls._map_operation(query)
            attribute = cls._recursive_get_attribute(item, key)
            if not operation(attribute, value):
                return False
        return True

    @classmethod
    def _get_attribute(cls, item: Any, attribute: str) -> Any:
        """Get the value off an item with either ["dict key lookup"] or .dot_lookup"""
        return item[attribute] if isinstance(item, dict) else getattr(item, attribute)

    @classmethod
    def _recursive_get_attribute(cls, item: Any, query: str) -> Any:
        attributes = query.split("__")
        for attribute in attributes:
            if attribute in dict(cls.attribute_getters):
                func = dict(cls.attribute_getters)[attribute]
                item = func(item)
            else:
                item = cls._get_attribute(item, attribute)
        return item

    @classmethod
    def _map_operation(cls, query: str) -> tuple[str, Callable]:
        """
        Fetch the key (parameter name) and operation (a function) given a query parameter.

        The default operator is equality (=)
        E.g. if query="name" -> key="name", operator=operator.eq

        If the query contains dunders (__) we attempt to fetch the relevant operation from the
        class' operations registry.
        E.g. if query="name__contains" -> key="name", operation=operator.contains
        """
        # defaults
        operation = operator.eq
        key = query

        if "__" in query:
            first_parts, dunder_operation = query.rsplit("__", maxsplit=1)
            operations = dict(cls.operations)
            if dunder_operation in operations:
                operation = operations[dunder_operation]
                key = first_parts
        return key, operation
