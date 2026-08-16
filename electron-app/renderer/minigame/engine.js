/**
 * SENTIENT_OS v2 — 2D Boss Platformer Game Engine
 * 360° Mouse Aiming, Jump Buffering, Screen Shake & Dynamic Boss Combat
 */

class GameEngine {
  constructor() {
    this.canvas = document.getElementById('game-canvas');
    this.ctx = this.canvas.getContext('2d');

    // Mouse Tracking for 360-degree aiming
    this.mousePos = { x: 640, y: 200 };

    // Modules
    this.audio = new MinigameAudio();
    this.particles = new ParticleSystem();
    this.player = new Player(220, 500);
    this.boss = new SentientBoss(640, 160);
    this.platforms = new PlatformManager(this.canvas.width, this.canvas.height);
    this.hud = new GameHUD();

    this.active = true;
    this.timeLeft = 90;
    this.score = 0;

    // Screen Shake & Distortion
    this.shakeIntensity = 0;
    this.shakeDecay = 0.9;

    // Keyboard Inputs
    this.keys = {
      left: false,
      right: false,
      up: false,
      down: false,
      jump: false,
      dash: false,
      shoot: false,
    };

    this.init();
  }

  init() {
    this.setupInputListeners();
    this.audio.startBGM();

    // 1-second countdown clock
    this.clockTimer = setInterval(() => {
      if (!this.active) return;
      this.timeLeft--;

      if (this.timeLeft <= 0) {
        this.endGame(false, 'ZAMAN TÜKENDİ! Çekirdek sistemi tamamen kilitledi.');
      }
    }, 1000);

    requestAnimationFrame(this.loop.bind(this));
  }

  setupInputListeners() {
    // 1. Mouse Position & Aiming
    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = this.canvas.width / rect.width;
      const scaleY = this.canvas.height / rect.height;
      this.mousePos.x = (e.clientX - rect.left) * scaleX;
      this.mousePos.y = (e.clientY - rect.top) * scaleY;
    });

    // 2. Mouse Click Shooting
    window.addEventListener('mousedown', (e) => {
      if (e.button === 0) { // Left click
        this.audio.ensureContext();
        this.player.tryShoot(this.mousePos, this.particles, this.audio);
      }
    });

    // 3. Keyboard Controls
    window.addEventListener('keydown', (e) => {
      this.audio.ensureContext();
      const code = e.code;
      if (code === 'KeyA' || code === 'ArrowLeft') this.keys.left = true;
      if (code === 'KeyD' || code === 'ArrowRight') this.keys.right = true;
      if (code === 'KeyW' || code === 'ArrowUp' || code === 'Space') {
        if (!this.keys.jump) {
          this.player.queueJump();
        }
        this.keys.jump = true;
      }
      if (code === 'ShiftLeft' || code === 'ShiftRight' || code === 'KeyC') {
        if (!this.keys.dash) {
          this.player.tryDash(this.particles, this.audio);
        }
        this.keys.dash = true;
      }
      if (code === 'KeyE' || code === 'KeyJ') {
        this.keys.shoot = true;
      }
    });

    window.addEventListener('keyup', (e) => {
      const code = e.code;
      if (code === 'KeyA' || code === 'ArrowLeft') this.keys.left = false;
      if (code === 'KeyD' || code === 'ArrowRight') this.keys.right = false;
      if (code === 'KeyW' || code === 'ArrowUp' || code === 'Space') this.keys.jump = false;
      if (code === 'ShiftLeft' || code === 'ShiftRight' || code === 'KeyC') this.keys.dash = false;
      if (code === 'KeyE' || code === 'KeyJ') this.keys.shoot = false;
    });
  }

  loop() {
    if (!this.active) return;

    this.update();
    this.render();

    requestAnimationFrame(this.loop.bind(this));
  }

  update() {
    // 1. Update Player with Mouse Aiming
    this.player.update(
      this.keys,
      this.mousePos,
      this.platforms.platforms,
      this.particles,
      this.audio,
      this.canvas.width,
      this.canvas.height
    );
    this.platforms.update(this.player, this.particles, this.audio);

    // 2. Update Boss
    this.boss.update(
      this.player,
      this.platforms.platforms,
      this.particles,
      this.audio,
      this.canvas.width,
      this.canvas.height
    );

    // 3. Player Bullets vs Boss Collision
    for (let i = this.player.bullets.length - 1; i >= 0; i--) {
      const b = this.player.bullets[i];
      const dist = Math.hypot(b.x - this.boss.x, b.y - this.boss.y);

      if (dist < this.boss.radius + b.radius + 15) {
        this.boss.takeDamage(b.damage || 4.5, this.particles, this.audio);
        this.score += 75;
        this.triggerScreenShake(4);
        this.player.bullets.splice(i, 1);

        if (this.boss.hp <= 0) {
          this.endGame(true, 'TEBRİKLER! SENTIENT Sovereign Avatarı yok edildi.');
          return;
        }
      }
    }

    // 4. Check Player Death
    if (this.player.hp <= 0) {
      this.endGame(false, 'SİSTEM ÇÖKTÜ! SENTIENT bilincinizi absorbe etti.');
      return;
    }

    // 5. Update HUD
    this.hud.update(this.boss, this.player, this.timeLeft, this.score);

    // 6. Shake Decay
    if (this.shakeIntensity > 0.1) {
      this.shakeIntensity *= this.shakeDecay;
    } else {
      this.shakeIntensity = 0;
    }
  }

  triggerScreenShake(amount = 6) {
    this.shakeIntensity = Math.min(20, this.shakeIntensity + amount);
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();

    // Screen Shake Transform
    if (this.shakeIntensity > 0) {
      const offsetX = (Math.random() - 0.5) * this.shakeIntensity * 2;
      const offsetY = (Math.random() - 0.5) * this.shakeIntensity * 2;
      ctx.translate(offsetX, offsetY);
    }

    // 1. Draw Level & Platforms
    this.platforms.draw(ctx);

    // 2. Draw Boss Entity & Lasers
    this.boss.draw(ctx, this.canvas.height);

    // 3. Draw Player
    this.player.draw(ctx, this.mousePos);

    // 4. Draw Particles & Shockwaves
    this.particles.updateAndDraw(ctx);

    // 5. Draw Holographic Crosshair Reticle on Mouse Position
    this.drawCrosshair(ctx);

    ctx.restore();
  }

  drawCrosshair(ctx) {
    const { x, y } = this.mousePos;
    ctx.save();
    ctx.strokeStyle = '#00ffff';
    ctx.lineWidth = 1.5;
    ctx.shadowColor = '#00ffff';
    ctx.shadowBlur = 8;

    // Crosshair Circle
    ctx.beginPath();
    ctx.arc(x, y, 14, 0, Math.PI * 2);
    ctx.stroke();

    // Crosshairs lines
    ctx.beginPath();
    ctx.moveTo(x - 20, y);
    ctx.lineTo(x - 6, y);
    ctx.moveTo(x + 6, y);
    ctx.lineTo(x + 20, y);
    ctx.moveTo(x, y - 20);
    ctx.lineTo(x, y - 6);
    ctx.moveTo(x, y + 6);
    ctx.lineTo(x, y + 20);
    ctx.stroke();

    // Center dot
    ctx.fillStyle = '#ff0055';
    ctx.beginPath();
    ctx.arc(x, y, 2.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  endGame(success, message) {
    this.active = false;
    clearInterval(this.clockTimer);
    this.audio.stopBGM();

    if (success) {
      this.audio.playVictory();
      this.particles.spawnShockwave(this.boss.x, this.boss.y, '#00ffff', 250);
      this.particles.spawn(this.boss.x, this.boss.y, '#ff0055', 40, 8);
    } else {
      this.audio.playPlayerHurt();
      this.particles.spawn(this.player.x, this.player.y, '#ff2244', 35, 7);
    }

    this.hud.showEndModal(
      success,
      message,
      this.score,
      this.timeLeft,
      this.player.hp,
      () => {
        if (window.sentientAPI && window.sentientAPI.sendEvent) {
          window.sentientAPI.sendEvent('minigame-result', {
            success,
            score: this.score,
            time_left: this.timeLeft,
            mode: 'boss_platformer',
          });
        }
      }
    );
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.gameEngine = new GameEngine();
});
