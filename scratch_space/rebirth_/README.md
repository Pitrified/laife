# Raise from the dead

## Python

1. Poetry to uv
1. ruff and linting
1. params vs config
1. all dependencies to update (and python version to 3.14)

## Renderer

1. Runner with no pygame - text only
1. Async logger is needed? can loguru handle that?
1. ipygame if needed

## LLM

1. huge update in langchain/langgraph happened in the mean time
1. split llm and embedding in a general provider -- leverage langchain for common interface if possible and clean up the config to just use them to control which to use
1. rename tool.py to utensil.py, tools mean something specific in langchain and LLM
1. clean up the world and give it a decisor to decide if the action is valid or not, and to give feedback to the player
1. clean up the player and give it a planner to break down the mission into sub-missions, and a brain to think about the mission and generate an action (or just a big brain)
1. setup qdrant for the world entities and tools and resources...

## world

1. split entities from communication?
1. explicit action of communication with other agent?
