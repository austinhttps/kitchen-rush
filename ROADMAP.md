# Future world and level selection

Captured from the user's request on 2026-10-27. This is a later milestone, not part of the current HUD/reconnect changes.

- Show different worlds and levels on an illustrated overworld map.
- The player drives a tiny car with WASD along roads between huts.
- Each hut represents a level and displays its level details before selection.
- Allow selection of the level and difficulty from the map.
- Carry the selected level/difficulty into room setup and synchronize it to the crew.

Implementation planning: keep map navigation separate from kitchen movement. Introduce explicit level identities and data-driven kitchen layouts when this milestone starts; preserve the room/session/rejoin entrypoints. Define hut previews (recipes, layout, hazards, score target, difficulty) before implementing selection. Host selection must be shared across the room. Final world themes, level count, and unlock/progression rules are not yet specified.

2026-10-27 update: special-guest budgets/stakes and moving-station sets currently scale by difficulty in the single bistro. Carry those profiles into individual level definitions when the map is built. A whole-floor rotation is a possible future hazard; the current high-difficulty kitchen carousel moves all stations between existing positions without rotating the floor or player controls.
