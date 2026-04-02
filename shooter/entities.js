// ── Star ──────────────────────────────────────────────────────────────────────

export class Star {
  constructor(canvasW, canvasH, speed, layer) {
    this.speed = speed;
    this.layer = layer;
    this.reset(canvasW, canvasH, true);
  }

  reset(canvasW, canvasH, initial = false) {
    this.x = Math.random() * canvasW;
    this.y = initial ? Math.random() * canvasH : -2;
    this.size = this.layer === 2 ? 2 : 1;
  }

  update(canvasH) {
    this.y += this.speed;
    if (this.y > canvasH + 2) this.reset(99999, canvasH);
  }

  draw(ctx, color) {
    ctx.fillStyle = color;
    ctx.fillRect(this.x, this.y, this.size, this.size);
  }
}

// ── Player ────────────────────────────────────────────────────────────────────

export class Player {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.angle = -Math.PI / 2; // pointing up initially
    this.speed = 4;
    this.radius = 15;
    this.shields = 3;
    this.maxShields = 3;
    this.activePowerUp = null;  // 'spread' | 'rapid' | 'speed' | 'homing'
    this.powerUpTimer = 0;      // frames remaining for timed power-ups
    this.powerUpMax = 0;        // max frames for current timed power-up (for bar display)
    this.invincibleTimer = 0;   // frames of post-hit invincibility
    this.shootCooldown = 0;
    this.baseShootCooldown = 12;
  }

  update(keys, mouseX, mouseY, canvas) {
    let dx = 0, dy = 0;
    if (keys['ArrowLeft']  || keys['KeyA']) dx -= 1;
    if (keys['ArrowRight'] || keys['KeyD']) dx += 1;
    if (keys['ArrowUp']    || keys['KeyW']) dy -= 1;
    if (keys['ArrowDown']  || keys['KeyS']) dy += 1;

    if (dx !== 0 && dy !== 0) { dx *= 0.707; dy *= 0.707; }

    const spd = this.activePowerUp === 'speed' ? this.speed * 1.5 : this.speed;
    this.x = Math.max(this.radius, Math.min(canvas.width  - this.radius, this.x + dx * spd));
    this.y = Math.max(this.radius, Math.min(canvas.height - this.radius, this.y + dy * spd));

    this.angle = Math.atan2(mouseY - this.y, mouseX - this.x);

    if (this.shootCooldown > 0) this.shootCooldown--;
    if (this.powerUpTimer > 0) {
      this.powerUpTimer--;
      if (this.powerUpTimer === 0 && this.activePowerUp !== 'spread' && this.activePowerUp !== 'homing') {
        this.activePowerUp = null;
      }
    }
    if (this.invincibleTimer > 0) this.invincibleTimer--;
  }

  draw(ctx) {
    if (this.invincibleTimer > 0 && Math.floor(this.invincibleTimer / 4) % 2 === 0) return;
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.angle + Math.PI / 2);

    ctx.shadowBlur = 10;
    ctx.lineWidth = 2;

    // Ship body
    ctx.strokeStyle = '#00ccff';
    ctx.shadowColor = '#00ccff';
    ctx.beginPath();
    ctx.moveTo(0, -18);
    ctx.lineTo(13, 14);
    ctx.lineTo(0, 8);
    ctx.lineTo(-13, 14);
    ctx.closePath();
    ctx.stroke();

    // Engine flames
    ctx.strokeStyle = '#ff8800';
    ctx.shadowColor = '#ff8800';
    ctx.lineWidth = 2;
    const flicker = Math.random() * 6;
    ctx.beginPath(); ctx.moveTo(-7, 12); ctx.lineTo(-5, 20 + flicker); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(7, 12);  ctx.lineTo(5,  20 + flicker); ctx.stroke();

    ctx.restore();
  }

  shoot(mouseX, mouseY, enemies) {
    if (this.shootCooldown > 0) return [];
    const cooldown = this.activePowerUp === 'rapid'
      ? Math.ceil(this.baseShootCooldown / 2)
      : this.baseShootCooldown;
    this.shootCooldown = cooldown;
    const angle = Math.atan2(mouseY - this.y, mouseX - this.x);

    if (this.activePowerUp === 'spread') {
      return [
        new Bullet(this.x, this.y, angle - 0.22, true),
        new Bullet(this.x, this.y, angle,         true),
        new Bullet(this.x, this.y, angle + 0.22,  true),
      ];
    }
    if (this.activePowerUp === 'homing') {
      return [new HomingMissile(this.x, this.y, angle, enemies)];
    }
    return [new Bullet(this.x, this.y, angle, true)];
  }

  takeDamage() {
    if (this.invincibleTimer > 0) return false;
    this.shields--;
    this.invincibleTimer = 120;
    return true;
  }

  applyPowerUp(type) {
    if (type === 'shield') {
      this.shields = Math.min(this.shields + 1, this.maxShields);
      return;
    }
    this.activePowerUp = type;
    if (type === 'rapid')  { this.powerUpTimer = 600; this.powerUpMax = 600; }
    if (type === 'speed')  { this.powerUpTimer = 480; this.powerUpMax = 480; }
    if (type === 'spread' || type === 'homing') { this.powerUpTimer = 0; this.powerUpMax = 0; }
  }
}

// ── Bullet ────────────────────────────────────────────────────────────────────

export class Bullet {
  constructor(x, y, angle, fromPlayer) {
    this.x = x;
    this.y = y;
    this.fromPlayer = fromPlayer;
    const speed = fromPlayer ? 10 : 5;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.radius = 3;
    this.trail = [];
  }

  update(_enemies) {
    this.trail.push({ x: this.x, y: this.y });
    if (this.trail.length > 4) this.trail.shift();
    this.x += this.vx;
    this.y += this.vy;
  }

  draw(ctx) {
    const color = this.fromPlayer ? '#ffffff' : '#ff6699';
    ctx.save();
    ctx.strokeStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 6;
    ctx.lineWidth = 2;
    if (this.trail.length > 1) {
      ctx.globalAlpha = 0.4;
      ctx.beginPath();
      ctx.moveTo(this.trail[0].x, this.trail[0].y);
      for (const p of this.trail) ctx.lineTo(p.x, p.y);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.beginPath();
    ctx.arc(this.x, this.y, 2, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }
}

// ── HomingMissile ─────────────────────────────────────────────────────────────

export class HomingMissile {
  constructor(x, y, angle, enemies) {
    this.x = x;
    this.y = y;
    this.vx = Math.cos(angle) * 4;
    this.vy = Math.sin(angle) * 4;
    this.speed = 4;
    this.turnRate = 0.06;
    this.radius = 3;
    this.fromPlayer = true;
    this.trail = [];
  }

  update(enemies) {
    this.trail.push({ x: this.x, y: this.y });
    if (this.trail.length > 6) this.trail.shift();

    // Steer toward nearest enemy
    let nearest = null, nearestDist = Infinity;
    for (const e of enemies) {
      const d = Math.hypot(e.x - this.x, e.y - this.y);
      if (d < nearestDist) { nearestDist = d; nearest = e; }
    }

    if (nearest) {
      const targetAngle = Math.atan2(nearest.y - this.y, nearest.x - this.x);
      const currentAngle = Math.atan2(this.vy, this.vx);
      let delta = targetAngle - currentAngle;
      while (delta > Math.PI)  delta -= Math.PI * 2;
      while (delta < -Math.PI) delta += Math.PI * 2;
      const newAngle = currentAngle + Math.sign(delta) * Math.min(Math.abs(delta), this.turnRate);
      this.vx = Math.cos(newAngle) * this.speed;
      this.vy = Math.sin(newAngle) * this.speed;
    }

    this.x += this.vx;
    this.y += this.vy;
  }

  draw(ctx) {
    ctx.save();
    ctx.strokeStyle = '#ffff44';
    ctx.shadowColor = '#ffff44';
    ctx.shadowBlur = 8;
    ctx.lineWidth = 2;
    if (this.trail.length > 1) {
      ctx.globalAlpha = 0.3;
      ctx.beginPath();
      ctx.moveTo(this.trail[0].x, this.trail[0].y);
      for (const p of this.trail) ctx.lineTo(p.x, p.y);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.beginPath();
    ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }
}

// ── Enemy (base) ──────────────────────────────────────────────────────────────

export class Enemy {
  constructor(x, y, hp, radius, scoreValue, dropChance) {
    this.x = x;
    this.y = y;
    this.hp = hp;
    this.radius = radius;
    this.scoreValue = scoreValue;
    this.dropChance = dropChance;
    this.onDeath = null;
  }

  draw(_ctx) {}

  update(_player, _canvas) {
    return null;
  }
}

// ── Drifter ───────────────────────────────────────────────────────────────────

export class Drifter extends Enemy {
  constructor(x, y, speedMult = 1) {
    super(x, y, 1, 10, 100, 0.3);
    const cx = window.innerWidth  / 2 + (Math.random() - 0.5) * 300;
    const cy = window.innerHeight / 2 + (Math.random() - 0.5) * 300;
    const angle = Math.atan2(cy - y, cx - x);
    const speed = (2 + Math.random() * 1.5) * speedMult;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
  }

  update(_player, _canvas) {
    this.x += this.vx;
    this.y += this.vy;
    return null;
  }

  draw(ctx) {
    ctx.save();
    ctx.strokeStyle = '#ff4488';
    ctx.shadowColor = '#ff4488';
    ctx.shadowBlur = 8;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(this.x,               this.y - this.radius);
    ctx.lineTo(this.x + this.radius, this.y);
    ctx.lineTo(this.x,               this.y + this.radius);
    ctx.lineTo(this.x - this.radius, this.y);
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }
}

// ── Tracker ───────────────────────────────────────────────────────────────────

export class Tracker extends Enemy {
  constructor(x, y, speedMult = 1) {
    super(x, y, 2, 12, 200, 0.2);
    this.speed = 1.2 * speedMult;
    this.maxSpeed = 3.5 * speedMult;
  }

  update(player, _canvas) {
    const angle = Math.atan2(player.y - this.y, player.x - this.x);
    this.speed = Math.min(this.speed + 0.015, this.maxSpeed);
    this.x += Math.cos(angle) * this.speed;
    this.y += Math.sin(angle) * this.speed;
    return null;
  }

  draw(ctx) {
    ctx.save();
    ctx.strokeStyle = '#ff4488';
    ctx.shadowColor = '#ff4488';
    ctx.shadowBlur = 8;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(this.x - 5, this.y); ctx.lineTo(this.x + 5, this.y);
    ctx.moveTo(this.x, this.y - 5); ctx.lineTo(this.x, this.y + 5);
    ctx.stroke();
    ctx.restore();
  }
}

// ── Shooter ───────────────────────────────────────────────────────────────────

export class Shooter extends Enemy {
  constructor(x, y, speedMult = 1) {
    super(x, y, 2, 12, 250, 0.2);
    this.speed = 1.5 * speedMult;
    this.preferredDist = 220;
    this.shootTimer = 80;
    this.strafeDir = Math.random() < 0.5 ? 1 : -1;
    this.strafeSwitchTimer = 90;
  }

  update(player, canvas) {
    const dx = player.x - this.x, dy = player.y - this.y;
    const d = Math.hypot(dx, dy);
    const toPlayer = { x: dx / d, y: dy / d };

    const radialSpeed = (d - this.preferredDist) * 0.02;
    this.strafeSwitchTimer--;
    if (this.strafeSwitchTimer <= 0) { this.strafeDir *= -1; this.strafeSwitchTimer = 90; }
    const strafeX = -toPlayer.y * this.strafeDir * this.speed;
    const strafeY =  toPlayer.x * this.strafeDir * this.speed;

    this.x = Math.max(0, Math.min(canvas.width,  this.x + toPlayer.x * radialSpeed + strafeX * 0.5));
    this.y = Math.max(0, Math.min(canvas.height, this.y + toPlayer.y * radialSpeed + strafeY * 0.5));

    this.shootTimer--;
    if (this.shootTimer <= 0) {
      this.shootTimer = 80;
      const angle = Math.atan2(player.y - this.y, player.x - this.x);
      return [new Bullet(this.x, this.y, angle, false)];
    }
    return null;
  }

  draw(ctx) {
    ctx.save();
    ctx.strokeStyle = '#ff4488';
    ctx.shadowColor = '#ff4488';
    ctx.shadowBlur = 8;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2 - Math.PI / 6;
      i === 0
        ? ctx.moveTo(this.x + Math.cos(a) * this.radius, this.y + Math.sin(a) * this.radius)
        : ctx.lineTo(this.x + Math.cos(a) * this.radius, this.y + Math.sin(a) * this.radius);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }
}

// ── Splitter ──────────────────────────────────────────────────────────────────

export class Splitter extends Enemy {
  constructor(x, y, speedMult = 1) {
    super(x, y, 4, 16, 400, 0.15);
    this.speedMult = speedMult;
    const angle = Math.random() * Math.PI * 2;
    const speed = (1.5 + Math.random()) * speedMult;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.onDeath = (level) => {
      const sm = 1 + level * 0.3;
      return [new Drifter(this.x - 10, this.y, sm), new Drifter(this.x + 10, this.y, sm)];
    };
  }

  update(_player, _canvas) {
    this.x += this.vx;
    this.y += this.vy;
    return null;
  }

  draw(ctx) {
    ctx.save();
    ctx.strokeStyle = '#ff4488';
    ctx.shadowColor = '#ff4488';
    ctx.shadowBlur = 10;
    ctx.lineWidth = 2;
    for (const rot of [0, Math.PI / 4]) {
      ctx.beginPath();
      for (let i = 0; i < 4; i++) {
        const a = rot + (i / 4) * Math.PI * 2;
        const px = this.x + Math.cos(a) * this.radius;
        const py = this.y + Math.sin(a) * this.radius;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.stroke();
    }
    ctx.restore();
  }
}

// ── PowerUp ───────────────────────────────────────────────────────────────────

const POWERUP_TYPES = ['spread', 'rapid', 'shield', 'speed', 'homing'];

export class PowerUp {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.type = POWERUP_TYPES[Math.floor(Math.random() * POWERUP_TYPES.length)];
    this.angle = 0;
    this.radius = 10;
  }

  update() {
    this.angle += 0.04;
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.angle);
    ctx.strokeStyle = '#ffff44';
    ctx.shadowColor = '#ffff44';
    ctx.shadowBlur = 12;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      i === 0
        ? ctx.moveTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius)
        : ctx.lineTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ffff44';
    ctx.font = 'bold 9px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const labels = { spread: 'S', rapid: 'R', shield: '♥', speed: 'V', homing: 'H' };
    ctx.rotate(-this.angle);
    ctx.fillText(labels[this.type], 0, 0);
    ctx.restore();
  }
}

// ── Boss (base) ───────────────────────────────────────────────────────────────

export class Boss {
  constructor(x, y, hp, radius, scoreValue) {
    this.x = x;
    this.y = y;
    this.hp = hp;
    this.maxHp = hp;
    this.radius = radius;
    this.scoreValue = scoreValue;
    this.phase = 1;
    this.name = 'BOSS';
  }

  takeDamage(amount) {
    this.hp -= amount;
    if (this.hp <= this.maxHp * 0.5 && this.phase === 1) {
      this.phase = 2;
      this.onPhaseChange();
      return true;
    }
    return false;
  }

  onPhaseChange() {}

  update(_player, _canvas, _frame) { return null; }

  draw(_ctx) {}
}

// ── Sentinel ──────────────────────────────────────────────────────────────────

export class Sentinel extends Boss {
  constructor(x, y) {
    super(x, y, 60, 38, 2000);
    this.name = 'THE SENTINEL';
    this.angle = 0;
    this.shootTimer = 0;
    this.rotSpeed = 0.012;
    this.fireInterval = 90;
  }

  onPhaseChange() {
    this.rotSpeed = 0.026;
    this.fireInterval = 50;
  }

  update(_player, _canvas, _frame) {
    this.angle += this.rotSpeed;
    this.shootTimer++;
    if (this.shootTimer >= this.fireInterval) {
      this.shootTimer = 0;
      const count = this.phase === 1 ? 4 : 8;
      return Array.from({ length: count }, (_, i) => {
        const a = this.angle + (i / count) * Math.PI * 2;
        return new Bullet(this.x, this.y, a, false);
      });
    }
    return null;
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.angle);
    ctx.strokeStyle = '#ff8844';
    ctx.shadowColor = '#ff8844';
    ctx.shadowBlur = 16;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      i === 0
        ? ctx.moveTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius)
        : ctx.lineTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < 4; i++) {
      const a = (i / 4) * Math.PI * 2 + Math.PI / 4;
      i === 0
        ? ctx.moveTo(Math.cos(a) * 18, Math.sin(a) * 18)
        : ctx.lineTo(Math.cos(a) * 18, Math.sin(a) * 18);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }
}

// ── Vortex ────────────────────────────────────────────────────────────────────

export class Vortex extends Boss {
  constructor(x, y) {
    super(x, y, 90, 36, 3000);
    this.name = 'THE VORTEX';
    this.orbitAngle = 0;
    this.orbitSpeed = 0.008;
    this.spreadTimer = 0;
    this.spreadInterval = 120;
    this.chargeTimer = 0;
    this.chargeInterval = 90;
    this.charging = false;
    this.chargeVx = 0;
    this.chargeVy = 0;
  }

  onPhaseChange() {
    this.orbitSpeed = 0;
    this.chargeTimer = 0;
  }

  update(player, canvas, _frame) {
    const shots = [];
    if (this.phase === 1) {
      this.orbitAngle += this.orbitSpeed;
      const cx = canvas.width / 2, cy = canvas.height / 2;
      const r = Math.min(cx, cy) * 0.75;
      this.x = cx + Math.cos(this.orbitAngle) * r;
      this.y = cy + Math.sin(this.orbitAngle) * r;

      // Fire 3 aimed bullets in a spread toward the player every 120 frames
      this.spreadTimer++;
      if (this.spreadTimer >= this.spreadInterval) {
        this.spreadTimer = 0;
        const aim = Math.atan2(player.y - this.y, player.x - this.x);
        for (let i = -1; i <= 1; i++) {
          shots.push(new Bullet(this.x, this.y, aim + i * 0.2, false));
        }
      }
    } else {
      if (!this.charging) {
        this.chargeTimer++;
        if (this.chargeTimer >= this.chargeInterval) {
          this.chargeTimer = 0;
          this.charging = true;
          const angle = Math.atan2(player.y - this.y, player.x - this.x);
          this.chargeVx = Math.cos(angle) * 8;
          this.chargeVy = Math.sin(angle) * 8;
          for (let i = -2; i <= 2; i++) {
            const a = Math.atan2(player.y - this.y, player.x - this.x) + i * 0.2;
            shots.push(new Bullet(this.x, this.y, a, false));
          }
        }
      } else {
        this.x += this.chargeVx;
        this.y += this.chargeVy;
        if (this.x < 40 || this.x > canvas.width - 40 ||
            this.y < 40 || this.y > canvas.height - 40) {
          this.charging = false;
          this.x = Math.max(100, Math.min(canvas.width - 100, this.x));
          this.y = Math.max(100, Math.min(canvas.height - 100, this.y));
        }
      }
    }
    return shots.length ? shots : null;
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.strokeStyle = '#ff8844';
    ctx.shadowColor = '#ff8844';
    ctx.shadowBlur = 16;
    ctx.lineWidth = 2.5;
    for (let t = 0; t < 2; t++) {
      const rot = (t === 0 ? 1 : -1) * (Date.now() / 1000) * 0.8;
      ctx.beginPath();
      for (let i = 0; i < 3; i++) {
        const a = rot + (i / 3) * Math.PI * 2;
        i === 0
          ? ctx.moveTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius)
          : ctx.lineTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius);
      }
      ctx.closePath();
      ctx.stroke();
    }
    ctx.restore();
  }
}

// ── Leviathan ─────────────────────────────────────────────────────────────────

export class Leviathan extends Boss {
  constructor(x, y) {
    super(x, y, 130, 50, 5000);
    this.name = 'THE LEVIATHAN';
    this.ringTimer = 0;
    this.ringInterval = 100;
    this.spawnTimer = 0;
    this.spawnInterval = 150;
    this.vx = 0.8;
    this.vy = 0.4;
  }

  onPhaseChange() {
    this.vx = 2.5;
    this.vy = 1.5;
    this.ringInterval = 60;
    this.spawnInterval = 100;
  }

  update(player, canvas, _frame) {
    this.x += this.vx;
    this.y += this.vy;
    if (this.x < this.radius || this.x > canvas.width  - this.radius) this.vx *= -1;
    if (this.y < this.radius || this.y > canvas.height * 0.6 - this.radius) this.vy *= -1;

    const shots = [];

    this.ringTimer++;
    if (this.ringTimer >= this.ringInterval) {
      this.ringTimer = 0;
      const count = this.phase === 1 ? 12 : 16;
      for (let i = 0; i < count; i++) {
        const a = (i / count) * Math.PI * 2;
        shots.push(new Bullet(this.x, this.y, a, false));
      }
      if (this.phase === 2) {
        const aim = Math.atan2(player.y - this.y, player.x - this.x);
        for (let n = 0; n < 3; n++) {
          const b = new Bullet(this.x, this.y, aim, false);
          b.vx *= 1.6; b.vy *= 1.6;
          shots.push(b);
        }
      }
    }

    this.spawnTimer++;
    if (this.spawnTimer >= this.spawnInterval) {
      this.spawnTimer = 0;
      const sm = this.phase === 1 ? 1 : 1.3;
      const offset = (Math.random() - 0.5) * 100;
      shots.push(this.phase === 1
        ? new Splitter(this.x + offset, this.y + 60, sm)
        : new Shooter(this.x + offset, this.y + 60, sm));
    }

    return shots.length ? shots : null;
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.strokeStyle = '#ff8844';
    ctx.shadowColor = '#ff8844';
    ctx.shadowBlur = 20;
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      i === 0
        ? ctx.moveTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius)
        : ctx.lineTo(Math.cos(a) * this.radius, Math.sin(a) * this.radius);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const a1 = (i / 5) * Math.PI * 2 - Math.PI / 2;
      const a2 = ((i + 2) / 5) * Math.PI * 2 - Math.PI / 2;
      ctx.moveTo(Math.cos(a1) * this.radius, Math.sin(a1) * this.radius);
      ctx.lineTo(Math.cos(a2) * this.radius, Math.sin(a2) * this.radius);
    }
    ctx.stroke();
    ctx.restore();
  }
}
