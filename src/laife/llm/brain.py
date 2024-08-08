"""Brain of an agent."""

from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_ollama import ChatOllama
from loguru import logger as lg


class Brain:
    """Brain of an agent."""

    def __init__(self):
        """Initialize the brain."""
        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0,
            # base_url="http://localhost:11434",
        )
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
        lg.debug(f"Brain.achat started")
        res = await self.chain.ainvoke(
            {
                "input_language": input_language,
                "output_language": output_language,
                "input": input_text,
            }
        )
        lg.debug(f"Brain.achat finished")
        return res
