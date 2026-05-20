# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

No build step — serve the directory with any static file server. Use port 3000 (port 8080 conflicts with WeChat on this machine):

```bash
python3 -m http.server 3000 --directory /Users/wayne/Documents/GitHub/claude-playground/shooter
```

Then open `http://localhost:3000` in the browser.

The game uses ES modules (`type="module"`), so it must be served over HTTP (not `file://`).

## Architecture

The game is a single-class state machine. `Game` in `game.js` owns all state and drives the frame loop via `requestAnimationFrame`. Everything flows through two methods each frame: `update()` → `draw()`.

**Module responsibilities:**

- `game.js` — `Game` class: state machine, game loop, collision detection, wave/level progression, input dispatch. Also exports `COLORS` and `STATES` constants used across modules.
- `entities.js` — All game objects: `Player`, `Bullet`, `HomingMissile`, `PowerUp`, `Star`, and four enemy types (`Drifter`, `Tracker`, `Shooter`, `Splitter`) plus three boss classes (`Sentinel`, `Vortex`, `Leviathan`) inheriting from `Boss`.
- `levels.js` — Data-only: the `LEVELS` array defines wave compositions and which boss class to use per level.
- `ui.js` — Pure rendering functions (no state): one exported function per screen (menu, HUD, boss HP bar, level complete, game over, victory, how-to-play, high scores).

**State machine** (`STATES`): `MENU → PLAYING → BOSS_FIGHT → LEVEL_COMPLETE → PLAYING` (next level) or `VICTORY`; `PLAYING/BOSS_FIGHT → GAME_OVER`; menu sub-screens (`HOW_TO_PLAY`, `HIGH_SCORES`) return to `MENU`.

**Entity update contract:** `enemy.update(player, canvas)` returns `null` or an array of new `Bullet`/`Enemy` instances to add to the game. Boss `update()` takes an additional `frameCount` param and can return enemy instances (e.g. `Leviathan` spawns `Splitter`/`Shooter`). The `Game.update()` loop dispatches these returned items into `this.enemyBullets` or `this.enemies`.

**Wave spawning:** `LEVELS[level].waves[wave]` defines enemy types/counts and `spawnInterval` (frames between spawns). `waveSpawnQueue` is a flat array of type strings consumed one-by-one. Wave advances when queue is empty AND `this.enemies.length === 0`.

**Collision detection:** `handleCollisions()` uses simple circle-circle (`dist()`) checks. Order matters — player bullets vs enemies first, then bullets vs boss, then enemy bullets vs player, then enemy contact vs player, then power-up pickup.

**High scores** are persisted in `localStorage` under the key `novaVectorScores` (top 5, descending).

## Adding Content

- **New enemy type:** extend `Enemy` in `entities.js`, implement `update(player, canvas)` returning bullets/null and `draw(ctx)`. Add the string key to the `map` in `Game.spawnEnemy()`.
- **New boss:** extend `Boss`, implement `update(player, canvas, frame)` and `draw(ctx)`. Import and reference it in `levels.js`.
- **New level:** add an entry to the `LEVELS` array in `levels.js` with `waves` and `bossClass`.
- **New power-up type:** add the string to `POWERUP_TYPES` in `entities.js`, handle it in `Player.shoot()` and `Player.applyPowerUp()`, add a label in both `entities.js` (`PowerUp.draw`) and `ui.js` (`drawHUD`).
