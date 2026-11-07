# Null's Brawl data adapter (project scaffold)

This folder is a **reference/scaffold** for keeping local simulation data separate from the dodge planner.

## Current status

- The simulator reads `../brawler_data/profiles.json` for local profile overrides.
- The JSON values currently supplied are demo archetypes, **not official game balance values**.
- This folder does not contain an installable Null's Brawl mod yet.
- No live game connection, client modification, process inspection, or match-input automation is included.

## Mod-format notes

The [Null's Brawl Modification Portal](https://github.com/ilynl7/nulls-brawl-modification-portal) documents mods as `content.json` packages that apply supported table patches. The portal describes CSV tables such as `characters`, `skills`, `maps`, and projectile/status-effect tables.

Before creating a real package, use the portal's current schema and the exact table/column names from the matching game-data version. Do not guess identifiers or copy demo simulator values into a game patch.

## Planned safe workflow

1. Export or manually curate a version-labelled, offline data snapshot.
2. Normalize the fields needed by the simulator into `brawler_data/profiles.json`.
3. Add map and projectile test fixtures as separate JSON files.
4. Validate JSON and run offline simulation/replay tests.
5. Treat any Null's mod package as a separate, optional resource/data patch—not as a way to execute the Python dodge planner.
