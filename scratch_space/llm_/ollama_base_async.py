"""Test the vanilla Ollama chatbot with async calls."""

import asyncio

from loguru import logger as lg
from ollama import AsyncClient


async def main_loop() -> None:
    """Run an async example using the vanilla Ollama AsyncClient."""
    lg.info("Starting game loop")
    ac = AsyncClient()

    model_name = "phi3"
    ac_res = await ac.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that translates english to spanish.",
            },
            {"role": "human", "content": "I love programming."},
        ],
    )

    lg.info(f"Response: {ac_res}")


# Run the main loop
asyncio.run(main_loop())
