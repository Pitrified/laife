"""Decoupled observability tooling that reads the structured JSONL log.

Kept fully separate from the game loop: nothing here imports pygame or the
simulation entities, it only ever reads ``cache/game_*.jsonl``.
"""
