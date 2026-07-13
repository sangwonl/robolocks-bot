# sample-skirmisher

This is a minimal Robolocks bot repo you can push to GitHub and import from the Arena tab.

## Files

- `robolocks.bot.json`: bot manifest loaded by Robolocks.
- `bot.py`: Python bot entrypoint.
- `unit.json`: unit selection. This sample uses the built-in `standard_tank` preset.

## GitHub Import

Push this directory as a GitHub repository, then import it in Robolocks with one of:

```txt
owner/repo
owner/repo@branch-or-tag
github:owner/repo@commit-sha
https://github.com/owner/repo/tree/branch-or-tag
```

Robolocks fetches:

```txt
https://raw.githubusercontent.com/owner/repo/ref/robolocks.bot.json
https://raw.githubusercontent.com/owner/repo/ref/bot.py
https://raw.githubusercontent.com/owner/repo/ref/unit.json
```

## Behavior

The bot:

- scans with a wide turret-mounted arc,
- aims the turret at the closest live enemy,
- fires when the firing solution is at least `0.35`,
- keeps a medium range band,
- orbits while in range,
- pushes its movement target away from nearby sensed obstacles.

It intentionally avoids `FaceArmorToward` while moving because `MoveTo` already steers the hull.

## Unit Config

Current format:

```json
{
  "unitPresetId": "standard_tank"
}
```

Available presets in the current web build include:

- `standard_tank`
- `heavy_gunner`
- `ballistic_test`
- `scout_optics`

Custom module JSON can be added later under a `modules` object once the Arena import UI exposes that workflow.
