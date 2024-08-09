"""Asynchronous logging."""

import asyncio
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


class Alog(metaclass=Singleton):
    def __init__(self) -> None:
        """Setup the logger."""
        # self.id = id(self)  # check the singleton
        self.last_msg = ""
        self.input_queue = asyncio.Queue()
        self.dup_count = 1
        self.log_task = None

    def log(self, msg: str) -> None:
        """Log a message."""
        if not self.log_task:
            self.start_logging()
        self.input_queue.put_nowait(msg)

    def start_logging(self) -> None:
        self.log_task = asyncio.create_task(self.log_cycle())

    async def log_cycle(self) -> None:
        """Log a message."""
        while True:
            msg = await self.input_queue.get()
            if self.is_duplicate(msg):
                self.dup_count += 1
                print(f"\r{msg} (x{self.dup_count})", end="")
                continue
            print(f"\n{msg}", end="")
            self.last_msg = msg
            self.dup_count = 1

    def is_duplicate(self, msg: str) -> bool:
        """Check if the message is a duplicate."""
        return self.last_msg == msg


alg = Alog()
