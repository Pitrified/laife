# LLM service layer

## Overview

We can have several provider for the same LLM based functionality.

1. Chat
   1. OpenAI
   2. AzureOpenAI
   3. HuggingFace based local model
   4. Ollama based local model
2. Embedding
   1. OpenAI
   2. AzureOpenAI
   3. HuggingFace based local model
   4. Ollama based local model
3. Vector store
   1. Qdrant
   2. Chroma
   3. Azure Search
   4. In memory
   5. Pinecone ???
   6. Weaviate ???
4. Vector store retriever ???
5. Cache
6. Rate limiter

We need a way to:

1. Configure which provider to use for each functionality (chat, embedding, vector database)
2. Configure the provider with the necessary parameters (e.g. API key, model name, etc.)
3. Provide a common interface for each functionality that can be used by the rest of the codebase without worrying about the underlying provider

If possible we want to leverage langchain for the common interface:

- https://docs.langchain.com/oss/python/langchain/models
- https://reference.langchain.com/python/langchain/embeddings/

## Chat

Refs:
1. general model usage https://docs.langchain.com/oss/python/langchain/models
2. `init_chat_model` specs https://reference.langchain.com/python/langchain/models/

We define a general `ChatConfig` base class,
this class defines an interface with a method `create_chat_model` that will create the chat model based on the config, using the general `init_chat_model` from langchain.
We can consider leveraging the `BaseModelKwargs` from 
https://github.com/Pitrified/python-project-template/blob/feat/webapp_scaffold/src/project_name/data_models/basemodel_kwargs.py
which lets us dump the `BaseModel` to a dict at first level only and we can send that to the `init_chat_model` with `**config.to_kw()`.
src/laife/llm_services/chat/config/base.py

Then define specific config for each provider, e.g. `OpenAIChatConfig`, `AzureOpenAIChatConfig`, etc.
src/laife/llm_services/chat/config/chat_openai.py
If the standard `create_chat_model` is not enough for a specific provider, we can override it in the specific config class.
Eg the HuggingFace based local model might have additional configs for a full offline mode, we can intercept them in the create method and set the env vars before calling the general `init_chat_model`.

Config classes can have sensible defaults.
In the big params file, we can customize the config for each provider, and have multiple models for each provider if needed.
src/laife/params/llm_services/chat.py

Config classes will be placed in `src/laife/llm_services/chat/config` folder, one module per provider, and a general `base.py` for the base config class.
