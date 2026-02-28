# Plan - Next Features

Ordered roughly by dependency and impact: earlier items unblock later ones.

## 1. Terrain entity

Create a `Terrain` class (forest, lake, fertile land) with position, size, and terrain type. Implement `Vectorable`, `to_prompt(pov_pos)`, and `to_document()`/`from_document()`. Add terrain instances to `WorldRunner` and include them in `WorldMapObservation` so the player can perceive terrain when observing. This is the most fundamental missing piece of the world model and unblocks dynamic map composition, prompt richness, and terrain rendering.

## ~~2. Typed world responses (`WRes` subclasses)~~ (done)

Replace the generic `response_data: dict` in `WRes` with typed pydantic subclasses (`WResBuild`, `WResCraft`, `WResObserve`, `WResMove`). This eliminates stringly-typed payloads, adds validation at the boundary, and makes the player-side response handling safer and self-documenting.

## 3. ~~Player inventory~~ (done)

Add an `inventory: list[Utensil]` to `Player`. Track utensils obtained via crafting (when `WResCraft` succeeds, place the utensil in inventory). Let the brain see the inventory in its observation prompt so it can reason about what tools are available before deciding to craft or use one.

## 4. Dynamic mission assignment

Replace the hardcoded `"Build a house"` mission with LLM-driven mission generation based on the current world observation. On first think cycle (or when a mission completes), the player asks a "mission generator" chain to propose a goal given what it sees. This makes gameplay emergent instead of scripted.

## 5. Mission lifecycle (completion and failure)

Wire up mission status transitions: after the world judge confirms a build/craft succeeded, mark the active mission `COMPLETED`. After N consecutive failures or an explicit LLM signal, mark it `FAILED` and trigger re-planning or a new mission. Without this, the player loops forever on a single mission.

## 6. Starting utensils and vector DB population

Define the four starter utensils (bucket, axe, hammer, hoe) and seed them into the Chroma vector store alongside the building types. Give the brain a retrieval step so it can look up relevant utensils/buildings before choosing an action, making its decisions grounded in actual world data.

## 7. Terrain rendering

Render terrain regions as tiled/colored backgrounds in `WorldRenderer`, replacing the flat black fill. Map each `TerrainType` to a tile color or sprite. This gives immediate visual feedback that the world has varied geography, and is a prerequisite for prettier map visuals.

## 8. Player-to-player interaction

Add `ActionInteract` to the action union. When a player picks it, the world delivers the target player's `to_prompt()` and routes a natural-language message between the two. This opens the door to cooperative mission-solving and emergent social behavior.

## 9. Structured game logger

Replace `Alog` with a structured logger (JSON lines or similar) recording every action, world response, mission transition, and LLM call with timing. Add log levels and file output. This is necessary for debugging multi-agent runs and later building an analytics dashboard.

## 10. Refactor repetitive player request pattern

Extract the "build request, send to world, await response, handle status, record history" boilerplate in `Player` into a generic helper (e.g., `async _world_request(req: WReq) -> WRes`). Cuts duplication across the move/build/craft handlers and makes adding new action types cheaper.
