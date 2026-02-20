"""Test the Ollama chatbot with async calls."""

import asyncio
from time import time

from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain_ollama import ChatOllama
from loguru import logger as lg


async def main_loop() -> None:
    """Demonstrate async chatting with an Ollama-based chat model."""
    lg.info("Starting game loop")

    # Initialize the Ollama chatbot
    ollama = ChatOllama(
        model="llama3.1",
        temperature=0,
        base_url="http://localhost:11434",
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                "You are a helpful assistant that translates {input_language} to {output_language}."
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )
    chain = prompt | ollama

    # Chat with the agent asynchronously
    lg.info("Chatting with the agent asynchronously")
    start_time = time()

    # call chain.ainvoke without blocking
    task = asyncio.create_task(
        chain.ainvoke(
            {
                "input_language": "en",
                "output_language": "es",
                "input": "Hello, how are you?",
            }
        )
    )

    dispatch_time = time()
    lg.info(f"Dispatch time: {dispatch_time - start_time:.2f}s")

    lg.info("Waiting for the agent to respond")

    # wait for the task to complete
    res = await task
    lg.info(f"Response: {res}")
    end_time = time()
    lg.info(f"Response time: {end_time - start_time:.2f}s")


# Run the main loop
asyncio.run(main_loop())
