"""Asynchronous logging."""

import asyncio

from laife.meta.singleton import Singleton


class Alog(metaclass=Singleton):
    """Asynchronous logger that handles duplicate messages by counting occurrences."""

    def __init__(self) -> None:
        """Set up the logger."""
        self.last_msg = ""
        self.input_queue = asyncio.Queue()
        self.dup_count = 1
        self.log_task = None

    def log_nowait(self, msg: str) -> None:
        """Log a message immediately, bypassing the queue."""
        print(f"\n{msg}")  # noqa: T201
        self.last_msg = msg
        self.dup_count = 1

    def log(self, msg: str) -> None:
        """Log a message."""
        if not self.log_task:
            self.start_logging()
            self.input_queue.put_nowait("ALOG: Starting alog")
        self.input_queue.put_nowait(msg)

    def start_logging(self) -> None:
        """Start the logging task."""
        self.log_task = asyncio.create_task(self.log_cycle())

    async def log_cycle(self) -> None:
        """Log messages from the queue."""
        while True:
            msg = await self.input_queue.get()
            if self.is_duplicate(msg):
                self.dup_count += 1
                print(f"\r{msg} (x{self.dup_count})", end="")  # noqa: T201
                self.input_queue.task_done()
                continue
            print(f"\n{msg}", end="")  # noqa: T201
            self.last_msg = msg
            self.dup_count = 1
            self.input_queue.task_done()

    def is_duplicate(self, msg: str) -> bool:
        """Check if the message is a duplicate."""
        return self.last_msg == msg


alg = Alog()
