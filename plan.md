# Backlog

Future work, unnumbered and in no particular order.
An item becomes a numbered folder under `plans/` when it is picked for implementation, in the `tracked-development` layout; the item is then removed from here and the folder's `00_start.md` starts from its text.
What is already built is in the `done` folders under `plans/`; `python3 scripts/plans.py list --status done` lists them.

## Engine

### Renderer checks without a screen

The headless run skips `WorldRenderer`, so nothing an agent runs exercises the drawing code.
Checks specific to the renderer: SDL's dummy video driver, or frames saved to images and compared; with a web page, Playwright screenshots.
They depend on which renderer stays (folder 41).

### Runtime warnings

`SystemExit` on quit and pygame's AVX2 notice, drafted in folder `34_runtime_warnings` and parked there until the renderer is decided (folder 41).

### Terminal output and log shape

The terminal is not the main interface: the window and `make tui` are.
Today a run prints every `alg.log` line, and the structured log has one line per move step; whether the structured log keeps its shape is reassessed, and a web view reading events from it (folder 41) is one reason to.
`Player` and `WorldRunner` call `alg.log` and `slog` for the same event in a few places; whether one call feeds both channels is decided with the log shape.

### Visual wishes

Tiled terrain and grass instead of flat colours, buildings with a garden, utensils held by the player.
They wait on the renderer choice (folder 41).

### Sprite loading

`SpriteLoader` (`src/laife/rendering/sprites.py`) is hand-rolled: sheet coordinates in a Python dict, one PNG per player state, picked by name.
The usual shape is a texture atlas with a JSON descriptor, exported by a tool such as TexturePacker or Aseprite and read directly by PixiJS (`Spritesheet`) and Phaser; Tiled covers maps the same way.
Assess whether to move to that format before more sprites are added; it goes with the web client (folder 41), which replaces the pygame loader.

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

### A build or craft completes the root mission

`Player._update_mission_from_response` calls `self.mission.record_action_success()` on a successful build or craft: the root mission becomes `COMPLETED` even while sub-missions are pending, and the next turn generates a new mission.
Seen in the headless run (folder 41): after the plan "Build a shed." then "Craft a hammer.", the build on turn 3 completed the whole mission and both steps were dropped.
To check: whether the success should go to `active_focus()`, the step being worked, and the root complete only through `advance()`, as `ActionComplete` does it.

### Building size units

`Player.build` makes a building of `(action.size, action.size)` at the player's position, and the world is in pixels: the headless script's `size=1` builds a 1 x 1 pixel shed, hidden under the player's sprite on the page (folder 41).
To check: what unit `ActionBuild.size` is in for the model, and whether a building type's own size should apply instead.

### History resets on a new mission, a plan and a completed step

`Player.history` is replaced by an empty `MissionHistory` in `_start_new_mission`, in `plan()`, and in `complete()` when a step is confirmed ("fresh slate for the new focus").
The brain then sees nothing of what it did before the reset, and the web snapshot's history is often short or empty (folder 41).
To check: whether the resets inside one mission (plan, completed step) are wanted, since the steps belong to the same mission, and whether something longer-lived should keep the actions across missions (see "Interaction memory" and "Player mind state").

### Save and resume a world

Write the whole world to disk, terrains, buildings, players with missions, history and inventory, and start a later run from it.
Needs the mission tree reload (Code health, "Mission tree: reload and ids") and a serialisable `Player`.
The web snapshot (folder 41) dumps most of it already, read-only.

### Players that can die

An alive state on the player, and what ends it.

### Dynamic map

Load the map from data instead of the hardcoded setup in `game/main.py`.

## Code health

### Vendoring shared with abyss

`laife.web.vendor` is a trimmed copy of abyss's `abyss.ui.vendor` (folder 41): an npm manifest pinned by version and integrity, a hash-checked cache, a lock checked before serving.
Two copies drift; a small shared package, used by both repos, would hold one. Its own effort across the two repos.

From folder 33 unless noted; each is checked against the code there.

### Mission tree: reload and ids

`Mission.parent_mission` is excluded from dumps (folder 41), so a mission tree written to JSON carries the parent only through the nesting of `steps`.
- Reload: `Mission.model_validate` rebuilds the tree with every `parent_mission` at `None`, and `advance()` then stops propagating upward. A validator that walks `steps` after loading and sets each step's parent to its container fixes it; wanted when something loads missions back.
- Ids: a mission is identified only by its place in the tree. An id field lets the page, the log or another mission refer to one sub-mission, and lets a sub-mission dumped on its own name its parent.

### Player mind state

`PlayerBrain` thinks for one player; the mind state (`mission`, `history`, `last_observation`, `inventory`) lives on `Player`, and `_update_mission_from_response` mixes world results into it.
One player instance has one brain instance, tightly tied, so a mind state shared between the two can exist.
To be assessed and planned on its own (folder 39 gave the brain the chains, not the state).
