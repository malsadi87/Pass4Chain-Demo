from typing import Iterable, Callable


def first_or_none(predicate: Callable, collection: Iterable):
    return next((x for x in collection if predicate(x)), None)
