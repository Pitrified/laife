# Backlog

Future work, unnumbered and in no particular order.
An item becomes a numbered folder under `plans/` when it is picked for implementation, in the `tracked-development` layout; the item is then removed from here and the folder's `00_start.md` starts from its text.
What is already built is in the `done` folders under `plans/`; `python3 scripts/plans.py list --status done` lists them.

## Engine

### Renderer: pygame or a web app

Whether pygame stays as the renderer.
Options: pygame as now; a text-only runner beside a renderer (`scratch_space/rebirth_/` had it); a web page reading the world state, served from g7 over the tailnet and opened from g4 or the phone, as the sibling repo abyss does.
Also decides the Python pin: pygame 2.6 has no 3.14 wheel, and the `==3.14.*` pin uses nothing newer than 3.12 (folder 33).
The visual wishes wait on this choice: tiled terrain and grass instead of flat colours, buildings with a garden, utensils held by the player, a window that shows more state and answers the mouse.
The same pass trims the engine's terminal output and the logs.
The terminal is not the main interface: the window and `make tui` are.
Today a run prints every `alg.log` line, and the structured log has one line per move step; whether the structured log keeps its shape is reassessed with it.
`Player` and `WorldRunner` call `alg.log` and `slog` for the same event in a few places; whether one call feeds both channels is decided with the log shape.

### Renderer checks without a screen

The headless run skips `WorldRenderer`, so nothing an agent runs exercises the drawing code.
Checks specific to the renderer: SDL's dummy video driver, or frames saved to images and compared.
They depend on which renderer stays (item above).

### Runtime warnings

`SystemExit` on quit and pygame's AVX2 notice, drafted in folder `34_runtime_warnings` and parked there until the renderer is decided.

### Seed for the live game

`setup_world()` takes a `random.Random`; the headless run seeds it, `game/main.py` passes an unseeded one.
A `--seed` argument or an env var would make a live run start from a known world (folder 38).

### Recorded replay for the headless run

The headless run answers from a fixed script.
Replaying a live run's recorded answers would use the same seam, `ScriptedChatConfig` per player; it diverges as soon as the world differs from the recording, so it waits for a case that needs it (folder 38).

### Tuning the chat params

laife's model, temperature and `reasoning_effort` (`ChatParams.load_params`) were picked to make a live run work, never tuned.
gpt-6-luna takes only temperature 1 unless `reasoning_effort` is `"none"`; fala-language-tutor's prompt lab compared models and efforts for its own prompts (its folder 14).
A change is checked by a live run capped by turns and approved first, since it spends the prepaid OpenAI credit (folder 40).

### A failed reply stops the world

An exception in the target's `receive_message()` escapes `WorldRunner.route_interaction` and ends `WorldRunner.simulate()`: the live game stops with a traceback, the headless run re-raises it.
The other choice is a `WResError` to the sender, as other world errors are handled since folder 35. Whether a failed reply should end the game is a gameplay decision (folder 38).

## Gameplay

### Starting utensils and the vector store in play

Define the starter utensils (bucket, axe, hammer, hoe) and seed them into the Chroma store with the building and terrain types.
Give the brain a retrieval step, so it looks up relevant utensils and buildings before choosing an action.
`ChromaConfig` is built and nothing in play queries it (folder 33).
Folder `31_utensil_crafting` holds the analysis of crafting a utensil that does not exist yet, including generating an image of it.

### Interaction memory

When a player receives a message, keep the content and sender, so the brain recalls past interactions when it replies.
`Player.receive_message()` replies and keeps nothing (folder 33).
A longer-term memory beyond the mission history is the same item grown.

### Interaction v2

The async-inbox strategy proposed in `24_player_interaction/00.1_strategy2_upgrade.md`: interactions that scale past a few players and allow broadcast.

### Shared missions

A player shares its mission with the world and can ask others for help.

### The complete judge sees no history

A live run on gpt-6-luna (2026-11-13, folder 34): a player moved 10 steps east, claimed its mission "move 10 steps east" complete, and the complete judge rejected it.
Its feedback: the current position is known, but no starting position or other evidence confirms the move.
The player then moved east again to make the move "recorded".
`WorldRunner.judge_complete()` gets the objective, the player's own claimed outcome, the observation and `Player.render_state()` (name, position, state); not the mission history. So a mission about moving cannot be confirmed.

A second live run, on g4 after folder 40 (log `game_20261113T222654.jsonl`), repeated it: p1 took the mission "Move 20 tiles east to search for a resource to gather", moved 20 steps east, claimed it complete on turn 2 and was rejected.
On turn 3 its reason was that "the displacement could not be verified from the observation", and it moved 20 east again "to establish a fresh, verifiable move".

### Distance in the observation is not a step count

The observation gives each nearby entity a cardinal direction and its Euclidean distance (`WorldMapObservation`); an `ActionMove` counts steps, and a diagonal step is `(+1, -1)`, about 1.41 of distance.
In the same g4 run p0 read "Alex's House is 12 tiles to the northeast", asked for 12 steps northeast, and the 8th step was blocked by the house: it aimed at the house's own position, inside its footprint.
The world handled it correctly; on turn 2 p0 read the house as 2.2 away and moved 1 north.
Open: whether the observation should give `(dx, dy)` in steps, or the building's edge rather than its position.

### Players that can die

An alive state on the player, and what ends it.

### Dynamic map

Load the map from data instead of the hardcoded setup in `game/main.py`.

## Code health

From folder 33 unless noted; each is checked against the code there.

### Player mind state

`PlayerBrain` thinks for one player; the mind state (`mission`, `history`, `last_observation`, `inventory`) lives on `Player`, and `_update_mission_from_response` mixes world results into it.
One player instance has one brain instance, tightly tied, so a mind state shared between the two can exist.
To be assessed and planned on its own (folder 39 gave the brain the chains, not the state).
