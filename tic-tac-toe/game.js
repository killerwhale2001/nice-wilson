import { getBestMove } from './ai.js';

const WINNING_LINES = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6],
];

let board = Array(9).fill(null);
let currentTurn = 'X';
let mode = null;
let gameOver = false;

const modeScreen = document.getElementById('mode-screen');
const gameScreen = document.getElementById('game-screen');
const statusEl = document.getElementById('status');
const cells = Array.from(document.querySelectorAll('.cell'));

export function selectMode(selectedMode) {
  mode = selectedMode;
  modeScreen.classList.add('hidden');
  gameScreen.classList.remove('hidden');
  updateStatus();
}

function checkWinner(b) {
  for (const [a, i, c] of WINNING_LINES) {
    if (b[a] && b[a] === b[i] && b[a] === b[c]) {
      return { winner: b[a], line: [a, i, c] };
    }
  }
  return null;
}

function render() {
  cells.forEach((cell, i) => {
    cell.textContent = board[i] ?? '';
    cell.dataset.value = board[i] ?? '';
    cell.classList.remove('win');
  });
}

function highlightWin(line) {
  line.forEach(i => cells[i].classList.add('win'));
}

function updateStatus(message) {
  statusEl.textContent = message ?? (
    mode === 'ai'
      ? (currentTurn === 'X' ? 'Your turn (X)' : 'Computer thinking…')
      : `Player ${currentTurn}'s turn`
  );
}

function handleClick(index) {
  if (gameOver || board[index]) return;
  if (mode === 'ai' && currentTurn === 'O') return;

  makeMove(index);

  if (!gameOver && mode === 'ai' && currentTurn === 'O') {
    updateStatus();
    setTimeout(() => {
      const move = getBestMove([...board]);
      makeMove(move);
    }, 300);
  }
}

function makeMove(index) {
  board[index] = currentTurn;
  render();

  const result = checkWinner(board);
  if (result) {
    highlightWin(result.line);
    const label = mode === 'ai' && result.winner === 'O' ? 'Computer wins!' : `Player ${result.winner} wins!`;
    updateStatus(label);
    gameOver = true;
    return;
  }

  if (board.every(Boolean)) {
    updateStatus("It's a draw!");
    gameOver = true;
    return;
  }

  currentTurn = currentTurn === 'X' ? 'O' : 'X';
  updateStatus();
}

export function restart() {
  board = Array(9).fill(null);
  currentTurn = 'X';
  gameOver = false;
  mode = null;
  render();
  gameScreen.classList.add('hidden');
  modeScreen.classList.remove('hidden');
}

cells.forEach((cell, i) => cell.addEventListener('click', () => handleClick(i)));
