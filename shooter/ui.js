// ui.js — HUD + all game screens

// ── HUD ───────────────────────────────────────────────────────────────────────

export function drawHUD(ctx, canvas, player, score, level, wave, isBoss, totalWaves) {
  const pad = 18;
  ctx.save();
  ctx.font = 'bold 11px monospace';
  ctx.shadowBlur = 6;

  // TOP LEFT: Shield icons
  ctx.strokeStyle = '#00ccff';
  ctx.shadowColor = '#00ccff';
  ctx.fillStyle = '#00ccff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('SHIELD', pad, pad);
  for (let i = 0; i < player.maxShields; i++) {
    const active = i < player.shields;
    const ix = pad + i * 22;
    const iy = pad + 16;
    ctx.strokeStyle = active ? '#00ccff' : '#334455';
    ctx.shadowColor = active ? '#00ccff' : 'transparent';
    ctx.lineWidth = active ? 2 : 1;
    drawHexagon(ctx, ix + 8, iy + 8, 8);
    if (active) {
      ctx.fillStyle = '#00ccff33';
      ctx.fill();
    }
  }

  if (!isBoss) {
    // TOP CENTER: Score
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#aaccff';
    ctx.shadowColor = '#aaccff';
    ctx.font = 'bold 10px monospace';
    ctx.fillText('SCORE', canvas.width / 2, pad);
    ctx.fillStyle = '#ffff44';
    ctx.shadowColor = '#ffff44';
    ctx.font = 'bold 18px monospace';
    ctx.fillText(String(score).padStart(6, '0'), canvas.width / 2, pad + 14);
  }

  // TOP RIGHT: Active power-up
  const prx = canvas.width - pad;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'top';
  ctx.font = 'bold 10px monospace';
  if (player.activePowerUp) {
    const labels = { spread: 'SPREAD', rapid: 'RAPID FIRE', speed: 'SPEED BOOST', homing: 'HOMING', shield: '' };
    ctx.fillStyle = '#ff8844';
    ctx.shadowColor = '#ff8844';
    ctx.fillText('WEAPON', prx, pad);
    ctx.fillText(labels[player.activePowerUp] || '', prx, pad + 12);
    if (player.powerUpMax > 0 && player.powerUpTimer > 0) {
      const barW = 60;
      const ratio = player.powerUpTimer / player.powerUpMax;
      ctx.fillStyle = '#332200';
      ctx.shadowBlur = 0;
      ctx.fillRect(prx - barW, pad + 26, barW, 4);
      ctx.fillStyle = '#ff8844';
      ctx.fillRect(prx - barW, pad + 26, barW * ratio, 4);
    }
  } else {
    ctx.fillStyle = '#334455';
    ctx.shadowBlur = 0;
    ctx.fillText('DEFAULT GUN', prx, pad + 8);
  }

  // BOTTOM CENTER: wave info (hidden during boss)
  if (!isBoss) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillStyle = '#aaccff';
    ctx.shadowColor = '#aaccff';
    ctx.shadowBlur = 4;
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`LEVEL ${level + 1}  —  WAVE ${wave + 1} / ${totalWaves}`,
      canvas.width / 2, canvas.height - pad);
  }

  ctx.restore();
}

export function drawBossHPBar(ctx, canvas, boss) {
  const barW = canvas.width * 0.5;
  const barH = 10;
  const bx = (canvas.width - barW) / 2;
  const by = 14;
  const ratio = Math.max(0, boss.hp / boss.maxHp);

  ctx.save();
  ctx.font = 'bold 10px monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  ctx.fillStyle = '#ff8844';
  ctx.shadowColor = '#ff8844';
  ctx.shadowBlur = 6;
  ctx.fillText(boss.name, canvas.width / 2, by);

  ctx.fillStyle = '#221100';
  ctx.shadowBlur = 0;
  ctx.fillRect(bx, by + 2, barW, barH);

  const barColor = boss.phase === 2 ? '#ff4400' : '#ff8844';
  ctx.fillStyle = barColor;
  ctx.shadowColor = barColor;
  ctx.shadowBlur = 4;
  ctx.fillRect(bx, by + 2, barW * ratio, barH);

  ctx.strokeStyle = '#ff8844';
  ctx.lineWidth = 1;
  ctx.shadowBlur = 0;
  ctx.strokeRect(bx, by + 2, barW, barH);
  ctx.restore();
}

function drawHexagon(ctx, x, y, r) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 - Math.PI / 6;
    i === 0
      ? ctx.moveTo(x + Math.cos(a) * r, y + Math.sin(a) * r)
      : ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r);
  }
  ctx.closePath();
  ctx.stroke();
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function glowText(ctx, text, x, y, color, size = 16, align = 'center') {
  ctx.save();
  ctx.font = `bold ${size}px monospace`;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 12;
  ctx.fillText(text, x, y);
  ctx.restore();
}

function drawShip(ctx, x, y, size = 1) {
  ctx.save();
  ctx.translate(x, y);
  ctx.strokeStyle = '#00ccff';
  ctx.shadowColor = '#00ccff';
  ctx.shadowBlur = 14;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0,           -28 * size);
  ctx.lineTo(18 * size,   20  * size);
  ctx.lineTo(0,           12  * size);
  ctx.lineTo(-18 * size,  20  * size);
  ctx.closePath();
  ctx.stroke();
  ctx.strokeStyle = '#ff8800';
  ctx.shadowColor = '#ff8800';
  ctx.beginPath();
  ctx.moveTo(-10 * size, 18 * size); ctx.lineTo(-8 * size, 28 * size); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo( 10 * size, 18 * size); ctx.lineTo( 8 * size, 28 * size); ctx.stroke();
  ctx.restore();
}

// ── Menu ──────────────────────────────────────────────────────────────────────

export function drawMenu(ctx, canvas, menuSelection) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  ctx.save();

  // Title
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  ctx.font = 'bold 52px monospace';
  ctx.fillStyle = '#00ccff';
  ctx.shadowColor = '#00ccff';
  ctx.shadowBlur = 24;
  ctx.fillText('NOVA', cx, cy - 120);

  ctx.font = 'bold 28px monospace';
  ctx.fillStyle = '#ffffff';
  ctx.shadowColor = '#ffffff';
  ctx.shadowBlur = 8;
  ctx.fillText('VECTOR', cx, cy - 72);

  // Divider
  ctx.strokeStyle = '#00ccff44';
  ctx.lineWidth = 1;
  ctx.shadowBlur = 0;
  ctx.beginPath();
  ctx.moveTo(cx - 120, cy - 52); ctx.lineTo(cx + 120, cy - 52);
  ctx.stroke();

  ctx.restore();

  // Ship
  drawShip(ctx, cx, cy - 10);

  // Menu items
  const items = ['▶  PLAY', 'HOW TO PLAY', 'HIGH SCORES'];
  items.forEach((label, i) => {
    const selected = i === menuSelection;
    const iy = cy + 70 + i * 32;
    glowText(ctx, label, cx, iy,
      selected ? '#ffff44' : '#aaccff',
      selected ? 14 : 12);
  });
}

// ── How To Play ───────────────────────────────────────────────────────────────

export function drawHowToPlay(ctx, canvas) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  glowText(ctx, 'HOW TO PLAY', cx, cy - 160, '#00ccff', 22);

  const lines = [
    ['ARROW KEYS', 'Move your ship'],
    ['MOUSE',      'Aim your weapon'],
    ['CLICK',      'Shoot'],
    ['',           ''],
    ['S', 'Spread Shot — 3-way burst'],
    ['R', 'Rapid Fire  — 2× fire rate (10s)'],
    ['♥', 'Shield      — restore 1 shield'],
    ['V', 'Speed Boost — 1.5× speed (8s)'],
    ['H', 'Homing      — tracks enemies'],
  ];

  ctx.save();
  ctx.font = '13px monospace';
  lines.forEach(([key, desc], i) => {
    const y = cy - 110 + i * 26;
    if (key) {
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#ffff44';
      ctx.shadowColor = '#ffff44';
      ctx.shadowBlur = 4;
      ctx.fillText(key, cx - 10, y);
    }
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#aaccff';
    ctx.shadowBlur = 0;
    ctx.fillText(desc, cx + 10, y);
  });
  ctx.restore();

  glowText(ctx, 'CLICK ANYWHERE TO GO BACK', cx, cy + 160, '#334455', 11);
}

// ── High Scores ───────────────────────────────────────────────────────────────

export function drawHighScores(ctx, canvas) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  glowText(ctx, 'HIGH SCORES', cx, cy - 140, '#00ccff', 22);

  const scores = JSON.parse(localStorage.getItem('novaVectorScores') || '[]');
  if (scores.length === 0) {
    glowText(ctx, 'NO SCORES YET', cx, cy, '#334455', 14);
  } else {
    scores.slice(0, 5).forEach((s, i) => {
      const y = cy - 80 + i * 40;
      glowText(ctx, `${i + 1}.`, cx - 80, y, '#ff8844', 14, 'right');
      glowText(ctx, String(s).padStart(6, '0'), cx + 80, y, '#ffff44', 18, 'right');
    });
  }

  glowText(ctx, 'CLICK ANYWHERE TO GO BACK', cx, cy + 160, '#334455', 11);
}

// ── Level Complete ────────────────────────────────────────────────────────────

export function drawLevelComplete(ctx, canvas, score, level) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  glowText(ctx, 'SECTOR CLEARED', cx, cy - 80, '#00ccff', 28);
  glowText(ctx, `LEVEL ${level + 1} COMPLETE`, cx, cy - 40, '#aaccff', 14);
  glowText(ctx, 'SCORE', cx, cy - 16, '#aaccff', 10);
  glowText(ctx, String(score).padStart(6, '0'), cx, cy + 10, '#ffff44', 32);
  glowText(ctx, 'CLICK TO CONTINUE  →', cx, cy + 80, '#ffffff', 14);
}

// ── Game Over ─────────────────────────────────────────────────────────────────

export function drawGameOver(ctx, canvas, score) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  glowText(ctx, 'SHIP DESTROYED', cx, cy - 80, '#ff4488', 30);
  glowText(ctx, 'FINAL SCORE', cx, cy - 20, '#aaccff', 10);
  glowText(ctx, String(score).padStart(6, '0'), cx, cy + 14, '#ffff44', 32);
  glowText(ctx, 'CLICK TO RETURN TO MENU', cx, cy + 80, '#aaccff', 12);
}

// ── Victory ───────────────────────────────────────────────────────────────────

export function drawVictory(ctx, canvas, score) {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  glowText(ctx, 'SYSTEM LIBERATED', cx, cy - 100, '#ffff44', 28);

  const stars = score >= 150000 ? 3 : score >= 50000 ? 2 : 1;
  const starStr = '★'.repeat(stars) + '☆'.repeat(3 - stars);
  glowText(ctx, starStr, cx, cy - 50, '#ffff44', 28);

  glowText(ctx, 'FINAL SCORE', cx, cy - 4, '#aaccff', 10);
  glowText(ctx, String(score).padStart(6, '0'), cx, cy + 22, '#ffff44', 32);

  glowText(ctx, 'CLICK TO RETURN TO MENU', cx, cy + 90, '#aaccff', 12);
}
