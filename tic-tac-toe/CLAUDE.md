# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development

This is a static vanilla JS project using ES modules — no build step, no package manager.

Because ES modules require HTTP (not `file://`), serve locally with any static server:

```bash
npx serve .           # from the tic-tac-toe/ directory
# or
python3 -m http.server 8080
```

There are no tests, no linter, and no CI configuration for this project.

## Architecture

The game uses three ES modules:

- **`game.js`** — owns all state (`board`, `currentTurn`, `mode`, `gameOver`) and drives the UI. Exports `selectMode()` and `restart()` for the HTML onclick handlers.
- **`ai.js`** — stateless minimax implementation. Exports `getBestMove(board)` which returns the optimal cell index for player `O`. No side effects.
- **`index.html`** — renders two screens (`#mode-screen`, `#game-screen`) toggled via `.hidden` CSS class. Wires AI/restart buttons via dynamic `import()`.

Key design detail: `index.html` uses dynamic `import('./game.js')` for button handlers because static `<script>` tags can't call named exports from modules directly. This means the module is re-imported on each click (cached by the browser after the first load).
