"""Test the async calls."""

import asyncio
from time import time

from loguru import logger as lg


async def async_call():
    lg.info("Starting async call")
    await asyncio.sleep(1)
    lg.info("Async call finished")


async def main_loop():
    lg.info("Starting game loop")

    start_time = time()
    # await async_call()
    # create an async task
    task = asyncio.create_task(async_call())
    end_time = time()
    lg.info(f"Elapsed time: {end_time - start_time:.2f}s")

    lg.info(f"Waiting for the agent to respond")

    # wait for the task to finish
    await task


# Run the main loop
asyncio.run(main_loop())
