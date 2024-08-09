"""Singleton metaclass."""

from typing import Any


class Singleton(type):
    """Singleton metaclass.

    https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
