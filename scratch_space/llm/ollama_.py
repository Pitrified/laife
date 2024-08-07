"""Ollama sample.

https://python.langchain.com/v0.2/docs/integrations/chat/ollama/
"""

from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "You are a helpful assistant that translates {input_language} to {output_language}."
        ),
        HumanMessagePromptTemplate.from_template("{input}"),
    ]
)


chain = prompt | llm
res = prompt.invoke(
    {
        "input_language": "English",
        "output_language": "German",
        "input": "I love programming.",
    }
)

print(res)
