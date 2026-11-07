# Null's Brawl data adapter scaffold

This directory documents the boundary between the offline simulator and the community mod format.

- The simulator reads local JSON fixtures under \`../brawler_data/\`.
- The fixtures are synthetic examples, not official balance values or a ready-to-install mod.
- The linked Modification Portal documents \`content.json\` table patches and CSV data.
- Before making an actual package, use the exact schema, supported tables, column types and game-version metadata from the portal and the intended Null's Brawl release.
- This project does not execute Python inside Null's Brawl or connect to its live process.

Reference: https://github.com/ilynl7/nulls-brawl-modification-portal
