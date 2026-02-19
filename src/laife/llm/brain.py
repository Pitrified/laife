"""Brain of an agent."""

import asyncio
import random

from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_ollama import ChatOllama

# from laife.config.credentials import OPENAI_API_KEY
from laife.ui.alog import alg


class Brain:
    """Brain of an agent."""

    def __init__(self):
        """Initialize the brain."""
        # ollama_model="llama3.1"
        ollama_model = "phi3"
        self.llm = ChatOllama(
            model=ollama_model,
            temperature=0,
            # base_url="http://localhost:11434",
        )
        # self.llm = ChatOpenAI(
        #     model="gpt-4o-mini",
        #     temperature=0,
        #     max_tokens=30,
        #     timeout=None,
        #     max_retries=2,
        #     api_key=OPENAI_API_KEY,
        # )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are a helpful assistant that translates {input_language} to {output_language}."
                ),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )
        self.chain = self.prompt | self.llm

    def chat(self, input_language, output_language, input_text):
        """Chat with the agent."""
        res = self.chain.invoke(
            {
                "input_language": input_language,
                "output_language": output_language,
                "input": input_text,
            }
        )
        return res

    async def achat(self, input_language, output_language, input_text):
        """Chat with the agent asynchronously."""
        alg.log("Brain.achat started")
        res = await self.chain.ainvoke(
            {
                "input_language": input_language,
                "output_language": output_language,
                "input": input_text,
            }
        )
        alg.log("Brain.achat finished")
        return res

    async def think(self, query: str) -> str:
        """Entry point for thinking."""
        # return await self.naive_think(query)
        return await self.llm_think(query)

    async def naive_think(self, query: str) -> str:
        """Randomly think about the next move."""
        await asyncio.sleep(2.5)
        if random.randint(0, 1):
            return "move"
        return "rest"

    async def llm_think(self, query: str) -> str:
        """Use the language model to think about the next move."""
        alg.log(f"BRAIN.llm_think: {query}")
        res = await self.llm.ainvoke(query)
        res_pretty = res.pretty_repr()
        alg.log(f"BRAIN.llm_think: {res}")
        return "move" if "move" in res_pretty else "rest"
