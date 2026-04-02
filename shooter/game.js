import { drawMenu, drawHUD, drawBossHPBar, drawLevelComplete,
         drawGameOver, drawVictory, drawHowToPlay, drawHighScores } from './ui.js';
import { Player, Drifter, Tracker, Shooter, Splitter, PowerUp, Star } from './entities.js';
import { LEVELS } from './levels.js';

export const COLORS = {
  PLAYER: '#00ccff',
  ENEMY: '#ff4488',
  BOSS: '#ff8844',
  BULLET: '#ffffff',
  ENEMY_BULLET: '#ff6699',
  POWERUP: '#ffff44',
  STARS: ['#223344', '#445566', '#aaccff'],
  BG: '#000815',
};

export const STATES = {
  MENU: 'MENU',
  PLAYING: 'PLAYING',
  BOSS_FIGHT: 'BOSS_FIGHT',
  LEVEL_COMPLETE: 'LEVEL_COMPLETE',
  GAME_OVER: 'GAME_OVER',
  VICTORY: 'VICTORY',
  HOW_TO_PLAY: 'HOW_TO_PLAY',
  HIGH_SCORES: 'HIGH_SCORES',
};

class Game {
  constructor() {
    this.canvas = document.getElementById('gameCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.state = STATES.MENU;
    this.level = 0;
    this.wave = 0;
    this.score = 0;
    this.player = null;
    this.enemies = [];
    this.playerBullets = [];
    this.enemyBullets = [];
    this.powerUps = [];
    this.boss = null;
    this.stars = [];
    this.frameCount = 0;
    this.menuSelection = 0; // 0=PLAY, 1=HOW_TO_PLAY, 2=HIGH_SCORES
    this.waveSpawnQueue = [];
    this.waveSpawnTimer = 0;
    this.screenFlash = 0;  // white flash frames (boss phase change)
    this.hitFlash = 0;     // red vignette frames (player hit)
    this.keys = {};
    this.mouse = { x: 0, y: 0, clicking: false };

    this.resize();
    this.initStars();
    this.bindInput();
    this.loop();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  initStars() {
    this.stars = [
      Array.from({ length: 60 }, () => new Star(this.canvas.width, this.canvas.height, 0.3, 0)),
      Array.from({ length: 35 }, () => new Star(this.canvas.width, this.canvas.height, 0.7, 1)),
      Array.from({ length: 15 }, () => new Star(this.canvas.width, this.canvas.height, 1.2, 2)),
    ];
  }

  bindInput() {
    window.addEventListener('keydown', e => {
      this.keys[e.code] = true;
      this.handleKeyDown(e.code);
    });
    window.addEventListener('keyup', e => { this.keys[e.code] = false; });
    this.canvas.addEventListener('mousemove', e => {
      this.mouse.x = e.clientX;
      this.mouse.y = e.clientY;
    });
    this.canvas.addEventListener('mousedown', e => {
      if (e.button === 0) { this.mouse.clicking = true; this.handleClick(); }
    });
    this.canvas.addEventListener('mouseup', e => {
      if (e.button === 0) this.mouse.clicking = false;
    });
    window.addEventListener('resize', () => this.resize());
  }

  handleKeyDown(code) {
    if (this.state === STATES.MENU) {
      if (code === 'ArrowUp') this.menuSelection = (this.menuSelection + 2) % 3;
      if (code === 'ArrowDown') this.menuSelection = (this.menuSelection + 1) % 3;
      if (code === 'Enter' || code === 'Space') this.activateMenu();
    }
    if (code === 'Escape') {
      if (this.state === STATES.HOW_TO_PLAY || this.state === STATES.HIGH_SCORES) {
        this.state = STATES.MENU;
      }
    }
  }

  handleClick() {
    const s = this.state;
    if (s === STATES.MENU) { this.activateMenu(); return; }
    if (s === STATES.LEVEL_COMPLETE) { this.nextLevel(); return; }
    if (s === STATES.GAME_OVER) { this.state = STATES.MENU; return; }
    if (s === STATES.VICTORY) { this.state = STATES.MENU; return; }
    if (s === STATES.HOW_TO_PLAY || s === STATES.HIGH_SCORES) { this.state = STATES.MENU; return; }
  }

  activateMenu() {
    if (this.menuSelection === 0) this.startGame();
    if (this.menuSelection === 1) this.state = STATES.HOW_TO_PLAY;
    if (this.menuSelection === 2) this.state = STATES.HIGH_SCORES;
  }

  startGame() {
    this.level = 0;
    this.wave = 0;
    this.score = 0;
    this.enemies = [];
    this.playerBullets = [];
    this.enemyBullets = [];
    this.powerUps = [];
    this.boss = null;
    this.player = new Player(this.canvas.width / 2, this.canvas.height / 2);
    this.state = STATES.PLAYING;
    this.startWave();
  }

  startWave() {
    const waveData = LEVELS[this.level].waves[this.wave];
    // Flatten into individual spawn entries
    this.waveSpawnQueue = waveData.enemies.flatMap(({ type, count }) =>
      Array(count).fill(type)
    );
    this.waveSpawnTimer = 0;
  }

  spawnEnemy(type, speedMult) {
    const w = this.canvas.width, h = this.canvas.height;
    const edge = Math.floor(Math.random() * 4);
    let x, y;
    if (edge === 0) { x = Math.random() * w; y = -20; }
    else if (edge === 1) { x = w + 20; y = Math.random() * h; }
    else if (edge === 2) { x = Math.random() * w; y = h + 20; }
    else { x = -20; y = Math.random() * h; }
    const map = { Drifter, Tracker, Shooter, Splitter };
    this.enemies.push(new map[type](x, y, speedMult));
  }

  nextLevel() {
    this.level++;
    this.wave = 0;
    this.enemies = [];
    this.playerBullets = [];
    this.enemyBullets = [];
    this.powerUps = [];
    this.boss = null;
    this.state = STATES.PLAYING;
    this.startWave();
  }

  startBossFight() {
    this.state = STATES.BOSS_FIGHT;
    const BossClass = LEVELS[this.level].bossClass;
    this.boss = new BossClass(this.canvas.width / 2, this.canvas.height * 0.2);
  }

  saveHighScore() {
    const scores = JSON.parse(localStorage.getItem('novaVectorScores') || '[]');
    scores.push(this.score);
    scores.sort((a, b) => b - a);
    localStorage.setItem('novaVectorScores', JSON.stringify(scores.slice(0, 5)));
  }

  loop() {
    requestAnimationFrame(() => this.loop());
    this.update();
    this.draw();
    this.frameCount++;
  }

  update() {
    // Stars always scroll
    for (const layer of this.stars) for (const s of layer) s.update(this.canvas.height);

    if (this.state !== STATES.PLAYING && this.state !== STATES.BOSS_FIGHT) return;

    this.player.update(this.keys, this.mouse.x, this.mouse.y, this.canvas);

    if (this.mouse.clicking) {
      const newBullets = this.player.shoot(this.mouse.x, this.mouse.y, this.enemies);
      this.playerBullets.push(...newBullets);
    }

    // Update + cull out-of-bounds bullets
    const inBounds = (b, pad = 30) =>
      b.x > -pad && b.x < this.canvas.width + pad &&
      b.y > -pad && b.y < this.canvas.height + pad;

    this.playerBullets = this.playerBullets.filter(b => { b.update(this.enemies); return inBounds(b); });
    this.enemyBullets  = this.enemyBullets.filter(b => { b.update([]); return inBounds(b); });

    // Enemies
    for (const enemy of this.enemies) {
      const shots = enemy.update(this.player, this.canvas);
      if (shots) this.enemyBullets.push(...shots);
    }

    // Boss
    if (this.boss) {
      const shots = this.boss.update(this.player, this.canvas, this.frameCount);
      if (shots) this.enemyBullets.push(...shots);
      if (this.boss.hp <= 0) {
        this.score += this.boss.scoreValue;
        this.boss = null;
        this.screenFlash = 20;
        if (this.level >= LEVELS.length - 1) {
          this.saveHighScore();
          this.state = STATES.VICTORY;
        } else {
          this.state = STATES.LEVEL_COMPLETE;
        }
        return;
      }
    }

    for (const pu of this.powerUps) pu.update();

    this.handleCollisions();

    if (this.state === STATES.PLAYING) this.updateWaveSpawning();

    if (this.screenFlash > 0) this.screenFlash--;
    if (this.hitFlash > 0) this.hitFlash--;
  }

  updateWaveSpawning() {
    const waveData = LEVELS[this.level].waves[this.wave];
    this.waveSpawnTimer--;
    if (this.waveSpawnTimer <= 0 && this.waveSpawnQueue.length > 0) {
      const speedMult = 1 + this.level * 0.3;
      this.spawnEnemy(this.waveSpawnQueue.shift(), speedMult);
      this.waveSpawnTimer = waveData.spawnInterval;
    }

    // Wave complete: all spawned and all dead
    if (this.waveSpawnQueue.length === 0 && this.enemies.length === 0) {
      this.wave++;
      if (this.wave >= LEVELS[this.level].waves.length) {
        this.startBossFight();
      } else {
        this.startWave();
      }
    }
  }

  handleCollisions() {
    const { playerBullets, enemyBullets, enemies, powerUps, player } = this;

    // Player bullets vs enemies
    for (let bi = playerBullets.length - 1; bi >= 0; bi--) {
      const b = playerBullets[bi];
      for (let ei = enemies.length - 1; ei >= 0; ei--) {
        const e = enemies[ei];
        if (dist(b, e) < e.radius) {
          playerBullets.splice(bi, 1);
          e.hp--;
          if (e.hp <= 0) {
            this.score += e.scoreValue;
            if (e.onDeath) {
              const spawned = e.onDeath(this.level);
              this.enemies.push(...spawned);
            }
            if (Math.random() < e.dropChance) this.powerUps.push(new PowerUp(e.x, e.y));
            enemies.splice(ei, 1);
          }
          break;
        }
      }
    }

    // Player bullets vs boss
    if (this.boss) {
      for (let bi = playerBullets.length - 1; bi >= 0; bi--) {
        const b = playerBullets[bi];
        if (dist(b, this.boss) < this.boss.radius) {
          playerBullets.splice(bi, 1);
          const phaseChanged = this.boss.takeDamage(1);
          if (phaseChanged) this.screenFlash = 20;
        }
      }
    }

    // Enemy bullets vs player
    for (let bi = enemyBullets.length - 1; bi >= 0; bi--) {
      if (dist(enemyBullets[bi], player) < player.radius) {
        enemyBullets.splice(bi, 1);
        if (player.takeDamage()) {
          this.hitFlash = 30;
          if (player.shields <= 0) {
            this.saveHighScore();
            this.state = STATES.GAME_OVER;
          }
        }
      }
    }

    // Enemies vs player (contact damage)
    for (let ei = enemies.length - 1; ei >= 0; ei--) {
      if (dist(enemies[ei], player) < enemies[ei].radius + player.radius - 5) {
        enemies.splice(ei, 1);
        if (player.takeDamage()) {
          this.hitFlash = 30;
          if (player.shields <= 0) {
            this.saveHighScore();
            this.state = STATES.GAME_OVER;
          }
        }
      }
    }

    // Power-ups vs player
    for (let pi = powerUps.length - 1; pi >= 0; pi--) {
      if (dist(powerUps[pi], player) < player.radius + 15) {
        player.applyPowerUp(powerUps[pi].type);
        powerUps.splice(pi, 1);
      }
    }
  }

  draw() {
    const { ctx, canvas } = this;
    ctx.fillStyle = COLORS.BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < this.stars.length; i++) {
      for (const s of this.stars[i]) s.draw(ctx, COLORS.STARS[i]);
    }

    const s = this.state;
    if (s === STATES.MENU) { drawMenu(ctx, canvas, this.menuSelection); return; }
    if (s === STATES.HOW_TO_PLAY) { drawHowToPlay(ctx, canvas); return; }
    if (s === STATES.HIGH_SCORES) { drawHighScores(ctx, canvas); return; }
    if (s === STATES.GAME_OVER) { drawGameOver(ctx, canvas, this.score); return; }
    if (s === STATES.VICTORY) { drawVictory(ctx, canvas, this.score); return; }
    if (s === STATES.LEVEL_COMPLETE) { drawLevelComplete(ctx, canvas, this.score, this.level); return; }

    for (const pu of this.powerUps) pu.draw(ctx);
    for (const e of this.enemies) e.draw(ctx);
    if (this.boss) this.boss.draw(ctx);
    for (const b of this.playerBullets) b.draw(ctx);
    for (const b of this.enemyBullets) b.draw(ctx);
    this.player.draw(ctx);

    if (s === STATES.BOSS_FIGHT && this.boss) drawBossHPBar(ctx, canvas, this.boss);
    drawHUD(ctx, canvas, this.player, this.score, this.level, this.wave,
            s === STATES.BOSS_FIGHT, LEVELS[this.level]?.waves?.length ?? 4);

    if (this.hitFlash > 0) {
      ctx.fillStyle = `rgba(255,0,0,${(this.hitFlash / 30) * 0.35})`;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    if (this.screenFlash > 0) {
      ctx.fillStyle = `rgba(255,255,255,${(this.screenFlash / 20) * 0.5})`;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
  }
}

function dist(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

new Game();
