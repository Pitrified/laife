# Headless run

`make headless` runs the game with no provider.
It is for development: run the engine after a change, then read what it did.

```bash
make headless                  # 6 turns per player, seed 0
make headless TURNS=12 SEED=3
make tui                       # opens the newest log, this run's
```

It prints each player's turn count and position, and the path of the structured log it wrote under `cache/`.

`make headless SERVE=1` serves the world over HTTP while it plays and keeps serving until Ctrl-C; see [Serving the world](web.md).

## What runs

The world and the players are the live game's: [`setup_world`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_setup.py) builds them for both `make run` and `make headless`.
The seed fixes the players' starting positions.
Two runs with the same seed and script take the same actions with the same outcomes and end in the same positions.
What can differ is the interleaving of the two players' events in the log.
The turn stamped on a reply can differ too: a reply runs inside the sender's world request and carries the receiver's current turn.

Every chain gets a `ScriptedChatConfig` from [`laife.llm.scripted_chat`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/scripted_chat.py) in place of the provider.
It subclasses llm-core's `ScriptedChatConfig` (`llm_core.testing.scripted_chat_model`), whose model ignores the prompt and answers by output model from the game's `build_answers`:

- the player brain gets the next action of that player's script, cycling;
- the judges approve, and the mission generator, planner and replier return fixed values;
- an output model it has no answer for raises llm-core's `UnscriptedSchemaError`, so a new chain fails the run instead of being answered with a guess.

The default script is one action of each type, ending with `complete`, so a run of six turns per player goes through every branch of the turn loop.

`laife.entities` holds the simulation only; the page and its server are in `laife.web`, used only with `SERVE=1`.

## What it does not show

- Anything drawn on screen.
- How a real model behaves: the script exercises the engine's code paths, not the prompts.

## When it stops

Each player returns after `--turns` turns, and the world loop is then cancelled.
If the world loop dies first, its exception is raised and the run fails.
The players would otherwise wait for world responses forever.

## The gate

`tests/test_headless.py` runs one pass of the script and checks that the run ends, that every player played every turn, and that no world response was an error.
It does not check which actions were taken.
It is part of `make check`.
