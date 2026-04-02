# Nova Vector — Design Spec

**Date:** 2026-04-01
**Type:** Browser-based top-down space shooter

---

## Context

A browser-based top-down space shooter built as a practice project in the claude-playground repo. The player pilots a ship, aims with the mouse, and fights through waves of enemies across 3 levels — each ending with a multi-phase boss. Built with vanilla JS + HTML Canvas so it runs by opening a single HTML file, no build step or server required.

---

## Tech Stack

- **Runtime:** Browser only — open `shooter/index.html` directly
- **Language:** Vanilla JS (ES modules), HTML5 Canvas 2D API, CSS
- **Dependencies:** None
- **Visual style:** Vector wireframe — glowing neon outlines on black, no filled sprites. Colors: player `#00ccff`, enemies `#ff4488`, bullets `#ffffff`, power-ups `#ffff44`, boss `#ff8844`

---

## File Structure

```
shooter/
  index.html     — canvas element, HUD overlay, menu DOM
  style.css      — fullscreen canvas, dark theme, menu/screen styles
  game.js        — main game loop, state machine, input handling
  entities.js    — Player, Enemy, Bullet, Boss, PowerUp classes
  levels.js      — wave definitions, enemy spawn configs, boss scripts
  ui.js          — HUD rendering, menu/gameover/levelcomplete screens
```

---

## Game State Machine

```
MENU → PLAYING → BOSS_FIGHT → LEVEL_COMPLETE → PLAYING (next level)
                                                        ↓ (after level 3)
                                                     VICTORY
PLAYING or BOSS_FIGHT → GAME_OVER (on death)
GAME_OVER → MENU
```

---

## Controls

| Input | Action |
|---|---|
| Arrow keys | Move ship (8-directional) |
| Mouse position | Ship rotates to face cursor |
| Left click / hold | Shoot toward cursor |

---

## Player

- 3 shield points (lives displayed as hexagon icons, top-left HUD)
- Brief invincibility frames + flash animation on hit
- Constant rotation toward mouse cursor
- Ship drawn as a triangle with engine glow lines at the rear

---

## Enemies

| Type | Behavior | HP | Notes |
|---|---|---|---|
| Drifter | Flies straight across screen | Low | Most common, high drop rate |
| Tracker | Slowly homes in on player | Medium | Accelerates over time |
| Shooter | Keeps distance, fires at player | Medium | Strafe-moves to maintain range |
| Splitter | Tanks hits, splits on death | High | Spawns 2 Drifters when destroyed |

All enemies spawn from screen edges. Spawn angles and rates scale per level.

---

## Power-Ups

Dropped randomly by enemies on death (20% chance). Player walks over them to collect. Only one active weapon mod at a time; timed effects show a countdown bar in the weapon HUD slot.

| Power-up | Effect | Duration |
|---|---|---|
| Spread Shot | Fires 3 bullets in a cone | Until replaced |
| Rapid Fire | Doubles fire rate | 10s |
| Shield Recharge | Restores 1 shield point | Instant |
| Speed Boost | +50% movement speed | 8s |
| Homing Missiles | Slow missiles that track nearest enemy | Until replaced |

---

## Levels & Bosses

### Structure
Each level = 4 waves of enemies → boss fight. Enemy count and speed increase each level.

### Level 1
- **Enemies:** Drifters and Trackers only
- **Boss — The Sentinel**
  - Phase 1: Rotates slowly, fires 4 bullets in a cross pattern
  - Phase 2 (< 50% HP): Rotates faster, fires 8 bullets in a star burst

### Level 2
- **Enemies:** All types including Shooters
- **Boss — The Vortex**
  - Phase 1: Orbits screen edge, periodically launches Tracker drones
  - Phase 2: Charges straight at player repeatedly while firing spread shots

### Level 3
- **Enemies:** All types including Splitters, higher density
- **Boss — The Leviathan**
  - Phase 1: Slow, fires ring bursts and spawns Splitters
  - Phase 2: Speeds up, fires aimed beams, spawns Shooters

During boss fights, a boss HP bar appears at the top-center replacing the score display. The bottom-center wave indicator is hidden during boss fights.

---

## HUD Layout (Corners)

```
[SHIELD ❖❖○]         [SCORE: 048200]        [WEAPON: SPREAD ████░]

              (gameplay canvas)

                      [LEVEL 1 — WAVE 2/4]
```

- **Top-left:** Shield icons (3 hexagons, filled = active)
- **Top-center:** Current score
- **Top-right:** Active weapon name + timed effect countdown bar
- **Bottom-center:** Current level and wave number (replaced by boss HP bar during boss fight)

---

## Menu & Screens

**Title screen (Arcade Cabinet style):**
- Starfield background (animated scrolling dots)
- Large glowing title: `NOVA VECTOR`
- Player ship illustration centered
- Menu: `▶ PLAY`, `HOW TO PLAY`, `HIGH SCORES`
- HOW TO PLAY screen: static overlay showing controls (arrow keys, mouse aim, click to shoot) and power-up icons with descriptions; `BACK` button returns to menu
- HIGH SCORES: top 5 scores persisted in localStorage, displayed as a ranked list

**Level Complete screen:**
- `SECTOR CLEARED` header
- Score so far
- `CONTINUE →` button

**Game Over screen:**
- `SHIP DESTROYED` header
- Final score
- `TRY AGAIN` / `MAIN MENU` buttons

**Victory screen:**
- `SYSTEM LIBERATED` header
- Final score with a star rating: ★☆☆ < 50,000 pts / ★★☆ 50,000–150,000 pts / ★★★ > 150,000 pts
- `PLAY AGAIN` / `MAIN MENU` buttons

---

## Rendering

All drawing done via Canvas 2D API:
- Enemies, player, and bosses: `strokeStyle` shapes (no fills or images)
- Bullet trails: short line segments
- Power-up pickups: rotating geometric shapes
- Background: scrolling parallax starfield (3 layers at different speeds)
- Screen effects: brief white flash on boss phase change, red vignette flash on player hit

---

## Verification

1. Open `shooter/index.html` in a browser — title screen should appear
2. Click PLAY — ship appears, arrow keys move, mouse aims, click shoots
3. Kill enough enemies to trigger wave 2, then wave 3, then wave 4, then boss
4. Boss HP bar appears; boss transitions to phase 2 at 50% HP
5. Clear boss → Level Complete screen → level 2 begins
6. Take 3 hits → Game Over screen → return to menu
7. Clear all 3 levels → Victory screen with star rating
