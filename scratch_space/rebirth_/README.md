# Raise from the dead

## Python

1. Poetry to uv -- DONE
1. ruff and linting -- DONE
1. params vs config -- DONE
1. all dependencies to update -- meh locked version went as high as possible
1. python version to 3.14 -> need wheels for pygame, stay at 3.13 for now

## Renderer

cool but all not needed for now

1. Runner with no pygame - text only
1. Async logger is needed? can loguru handle that? -- no, ALog also skips repeated messages
1. ipygame if needed

## LLM

1. huge update in langchain/langgraph happened in the mean time
1. split llm and embedding in a general provider -- leverage langchain for common interface if possible and clean up the config to just use them to control which to use -- DONE
1. rename tool.py to utensil.py, tools mean something specific in langchain and LLM -- DONE
1. clean up the world and give it a decisor to decide if the action is valid or not, and to give feedback to the player
1. clean up the player and give it a planner to break down the mission into sub-missions, and a brain to think about the mission and generate an action (or just a big brain)
1. setup qdrant for the world entities and utensils and resources...
1. there is an attribute called `object`, that seems shady -- DONE
1. entities that go into the vector database should all inherit from a common base class that can convert them to a langchain document with the necessary metadata for retrieval, and also have a method to convert them back from a document to an entity
   so that we can just have a generic `add_entity_to_db` and `get_entity_from_db` methods that can work with any entity type

## world

1. split entities from communication?
1. explicit action of communication with other agent?
1. split rendering from acting? world and player classes are doing both which seems a lot
   so eg the WorldRenderer and WorldRunner, the first one is responsible for rendering the world state (pygame or text), and the second one is responsible for running the world logic and updating the world state based on the players' actions (and possibly the communications)
1. action of self reflection and memory update for each player
