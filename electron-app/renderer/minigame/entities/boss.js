/**
 * SENTIENT_OS v2 — Transforming Sentient Boss Entity
 * 3 Drastically Evolving Forms: Cyan Latent Core -> Purple Corrupted Beast -> Blood-Red Cataclysm Demon
 */

class SentientBoss {
  constructor(x = 640, y = 160) {
    this.x = x;
    this.y = y;
    this.targetX = x;
    this.targetY = y;
    this.radius = 65;

    this.hp = 100;
    this.maxHp = 100;
    this.phase = 1; // 1: Cyan Latent, 2: Purple Corrupted, 3: Red Cataclysm

    this.attackTimer = 0;
    this.angle = 0;
    this.glitchOffset = { x: 0, y: 0 };
    this.teleportCooldown = 0;

    // Tendril sets for each form (Form 1: 2 ribbons, Form 2: 4 tentacles, Form 3: 6 demon tendrils)
    this.tendrils = [];
    this.initTendrils(1);

    this.bullets = [];
    this.lasers = [];
  }

  initTendrils(phase) {
    this.tendrils = [];
    if (phase === 1) {
      // 2 gentle cyber ribbons
      this.tendrils = [
        { baseAngle: -Math.PI * 0.6, length: 140, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.6, length: 140, sway: 0, tipX: 0, tipY: 0 },
      ];
    } else if (phase === 2) {
      // 4 razor tendrils
      this.tendrils = [
        { baseAngle: -Math.PI * 0.75, length: 180, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: -Math.PI * 0.35, length: 170, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.35, length: 170, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.75, length: 180, sway: 0, tipX: 0, tipY: 0 },
      ];
    } else {
      // 6 cataclysm demon tendrils
      this.tendrils = [
        { baseAngle: -Math.PI * 0.85, length: 210, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: -Math.PI * 0.55, length: 190, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: -Math.PI * 0.25, length: 170, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.25, length: 170, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.55, length: 190, sway: 0, tipX: 0, tipY: 0 },
        { baseAngle: Math.PI * 0.85, length: 210, sway: 0, tipX: 0, tipY: 0 },
      ];
    }
  }

  update(player, platforms, particles, audio, canvasWidth, canvasHeight) {
    this.attackTimer++;
    this.angle += this.phase === 3 ? 0.04 : this.phase === 2 ? 0.025 : 0.015;

    // Phase Transitions with Full Visual Transformation
    if (this.hp <= 33 && this.phase < 3) {
      this.phase = 3;
      this.initTendrils(3);
      audio.playBossRoar();
      particles.spawnShockwave(this.x, this.y, '#ff0033', 180);
      particles.spawn(this.x, this.y, '#ff0033', 35, 7);
    } else if (this.hp <= 66 && this.phase < 2) {
      this.phase = 2;
      this.initTendrils(2);
      audio.playBossRoar();
      particles.spawnShockwave(this.x, this.y, '#aa00ff', 130);
      particles.spawn(this.x, this.y, '#ffaa00', 25, 5);
    }

    // Floating Movement (Phase 1 is calm & slow)
    const hoverSpd = this.phase === 3 ? 0.035 : this.phase === 2 ? 0.02 : 0.012;
    const hoverAmp = this.phase === 3 ? 240 : this.phase === 2 ? 170 : 110;
    this.x = 640 + Math.sin(this.attackTimer * hoverSpd) * hoverAmp;
    this.y = 160 + Math.cos(this.attackTimer * hoverSpd * 1.5) * (this.phase === 3 ? 30 : 18);

    // Glitch Shift
    if (this.phase >= 2 && Math.random() < (this.phase === 3 ? 0.25 : 0.1)) {
      this.glitchOffset.x = (Math.random() - 0.5) * (this.phase === 3 ? 12 : 6);
      this.glitchOffset.y = (Math.random() - 0.5) * (this.phase === 3 ? 12 : 6);
    } else {
      this.glitchOffset.x = 0;
      this.glitchOffset.y = 0;
    }

    // Teleportation only in Phase 2 & 3
    if (this.phase >= 2) {
      this.teleportCooldown++;
      if (this.teleportCooldown > 380 && Math.random() < 0.02) {
        this.teleportCooldown = 0;
        particles.spawnShockwave(this.x, this.y, this.phase === 3 ? '#ff0033' : '#aa00ff', 90);
        this.x = Math.random() < 0.5 ? 320 : 960;
        this.y = 150 + Math.random() * 40;
        audio.playDash();
        particles.spawnShockwave(this.x, this.y, '#00ffff', 90);
      }
    }

    // Update Tendril Sway
    this.tendrils.forEach((t, i) => {
      t.sway = Math.sin(this.attackTimer * 0.03 + i * 1.2) * (this.phase === 3 ? 35 : 20);
      const rad = t.baseAngle + Math.sin(this.attackTimer * 0.02 + i) * 0.2;
      t.tipX = this.x + Math.cos(rad) * t.length + t.sway;
      t.tipY = this.y + Math.sin(rad) * t.length;
    });

    // Attack Intervals: Phase 1 (150 frames = 2.5s), Phase 2 (95 frames = 1.6s), Phase 3 (55 frames = 0.9s)
    const attackInterval = this.phase === 3 ? 55 : this.phase === 2 ? 95 : 150;
    if (this.attackTimer % attackInterval === 0) {
      this.executeAttack(player, particles, audio, canvasWidth, canvasHeight);
    }

    // Update Bullets
    for (let i = this.bullets.length - 1; i >= 0; i--) {
      const b = this.bullets[i];
      b.x += b.vx;
      b.y += b.vy;
      b.life--;

      // Homing logic (gentle speed)
      if (b.isHoming && player) {
        const dx = player.x + 13 - b.x;
        const dy = player.y + 21 - b.y;
        const dist = Math.hypot(dx, dy) || 1;
        b.vx += (dx / dist) * 0.12;
        b.vy += (dy / dist) * 0.12;
        const speed = Math.hypot(b.vx, b.vy);
        if (speed > 5.5) {
          b.vx = (b.vx / speed) * 5.5;
          b.vy = (b.vy / speed) * 5.5;
        }
      }

      // Check collision with player
      if (
        player &&
        player.invulnerableTimer <= 0 &&
        player.dashTimer <= 0 &&
        b.x > player.x &&
        b.x < player.x + player.w &&
        b.y > player.y &&
        b.y < player.y + player.h
      ) {
        player.hurt(1, particles, audio);
        this.bullets.splice(i, 1);
        continue;
      }

      if (b.life <= 0 || b.x < -50 || b.x > canvasWidth + 50 || b.y > canvasHeight + 50) {
        this.bullets.splice(i, 1);
      }
    }

    // Update Lasers
    for (let i = this.lasers.length - 1; i >= 0; i--) {
      const l = this.lasers[i];
      l.timer++;

      if (l.state === 'warning' && l.timer >= l.warnDuration) {
        l.state = 'firing';
        l.timer = 0;
        audio.playLaserFire();
        particles.spawnShockwave(l.x + l.w / 2, canvasHeight / 2, l.color || '#ff2244', 120);
      } else if (l.state === 'firing') {
        if (
          player &&
          player.invulnerableTimer <= 0 &&
          player.dashTimer <= 0 &&
          player.x + player.w > l.x &&
          player.x < l.x + l.w
        ) {
          player.hurt(1, particles, audio);
        }

        if (l.timer >= l.fireDuration) {
          this.lasers.splice(i, 1);
        }
      }
    }
  }

  executeAttack(player, particles, audio, canvasWidth, canvasHeight) {
    if (this.phase === 1) {
      // Phase 1: Form 1 Cyan Core (Very gentle!)
      if (Math.random() < 0.5) {
        // Cyan Laser with 90 frames (1.5s) warning
        audio.playLaserCharge();
        const laserX = 220 + Math.random() * (canvasWidth - 500);
        this.lasers.push({
          x: laserX,
          w: 55,
          color: '#00ffff',
          state: 'warning',
          timer: 0,
          warnDuration: 90,
          fireDuration: 22,
        });
      } else {
        // 2 slow cyan pulse orbs
        audio.playLaserFire();
        for (let i = -1; i <= 1; i += 2) {
          const angle = Math.PI / 2 + i * 0.25;
          this.bullets.push({
            x: this.x,
            y: this.y + 40,
            vx: Math.cos(angle) * 3.6,
            vy: Math.sin(angle) * 3.6,
            radius: 8,
            color: '#00e5ff',
            life: 150,
          });
        }
      }
    } else if (this.phase === 2) {
      // Phase 2: Form 2 Purple Corrupted Beast
      audio.playLaserCharge();
      setTimeout(() => {
        audio.playLaserFire();
        for (let i = 0; i < 3; i++) {
          const angle = Math.PI / 2 + (i - 1) * 0.35;
          this.bullets.push({
            x: this.x,
            y: this.y + 40,
            vx: Math.cos(angle) * 4.2,
            vy: Math.sin(angle) * 4.2,
            radius: 9,
            color: '#ffaa00', // Amber spikes
            life: 140,
          });
        }
      }, 300);

      // 1 target purple laser (55 frames warning)
      if (player) {
        this.lasers.push({
          x: Math.max(50, player.x - 20),
          w: 65,
          color: '#aa00ff',
          state: 'warning',
          timer: 0,
          warnDuration: 55,
          fireDuration: 22,
        });
      }
    } else if (this.phase === 3) {
      // Phase 3: Form 3 Blood-Red Cataclysm Demon
      audio.playLaserFire();
      const count = 8;
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + this.angle;
        this.bullets.push({
          x: this.x,
          y: this.y,
          vx: Math.cos(angle) * 5.2,
          vy: Math.sin(angle) * 5.2,
          radius: 8,
          color: '#ff0033',
          life: 120,
        });
      }

      // 1 Crimson laser with 35 frames warning
      const lX = 200 + Math.random() * (canvasWidth - 400);
      this.lasers.push({
        x: lX,
        w: 65,
        color: '#ff0033',
        state: 'warning',
        timer: 0,
        warnDuration: 35,
        fireDuration: 20,
      });
    }
  }

  takeDamage(amount, particles, audio) {
    this.hp = Math.max(0, this.hp - amount);
    audio.playBossHit();
    const hitColor = this.phase === 3 ? '#ff0033' : this.phase === 2 ? '#ffaa00' : '#00ffff';
    particles.spawn(this.x, this.y, hitColor, 12, 4);
    particles.spawn(this.x, this.y, '#ffffff', 6, 3);
  }

  draw(ctx, canvasHeight) {
    const gx = this.x + this.glitchOffset.x;
    const gy = this.y + this.glitchOffset.y;

    // Theme Colors based on Phase Form
    const mainColor = this.phase === 3 ? '#ff0033' : this.phase === 2 ? '#aa00ff' : '#00e5ff';
    const accentColor = this.phase === 3 ? '#ff6600' : this.phase === 2 ? '#ffaa00' : '#ffffff';
    const darkBg = this.phase === 3 ? '#100004' : this.phase === 2 ? '#0b0014' : '#030a12';

    // 1. Draw Lasers
    for (const l of this.lasers) {
      if (l.state === 'warning') {
        ctx.save();
        ctx.fillStyle = l.color === '#00ffff' ? 'rgba(0, 255, 255, 0.15)' : 'rgba(255, 0, 50, 0.18)';
        ctx.fillRect(l.x, 0, l.w, canvasHeight);
        ctx.strokeStyle = l.color || mainColor;
        ctx.setLineDash([8, 8]);
        ctx.lineWidth = 2;
        ctx.strokeRect(l.x, 0, l.w, canvasHeight);

        // Warning Text inside column
        ctx.fillStyle = l.color || mainColor;
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('⚠ UYARI ⚠', l.x + l.w / 2, 90);
        ctx.restore();
      } else if (l.state === 'firing') {
        ctx.save();
        ctx.fillStyle = l.color || mainColor;
        ctx.shadowColor = l.color || mainColor;
        ctx.shadowBlur = 25;
        ctx.fillRect(l.x, 0, l.w, canvasHeight);

        // White core beam
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(l.x + l.w * 0.32, 0, l.w * 0.36, canvasHeight);
        ctx.restore();
      }
    }

    // 2. Draw Tendrils (Shifts based on Phase Form)
    ctx.save();
    for (let i = 0; i < this.tendrils.length; i++) {
      const t = this.tendrils[i];
      ctx.strokeStyle = mainColor;
      ctx.lineWidth = this.phase === 3 ? 8 : this.phase === 2 ? 6 : 4;
      ctx.lineCap = 'round';
      ctx.shadowColor = mainColor;
      ctx.shadowBlur = 12;

      ctx.beginPath();
      ctx.moveTo(gx, gy);
      const cpX = (gx + t.tipX) / 2 + Math.sin(this.angle + i) * (this.phase === 3 ? 50 : 30);
      const cpY = (gy + t.tipY) / 2 + Math.cos(this.angle + i) * (this.phase === 3 ? 40 : 25);
      ctx.quadraticCurveTo(cpX, cpY, t.tipX, t.tipY);
      ctx.stroke();

      // Glowing Tendril Claw Nodes
      ctx.fillStyle = accentColor;
      ctx.beginPath();
      ctx.arc(t.tipX, t.tipY, this.phase === 3 ? 7 : 5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    // 3. Draw Evolving Boss Core & Demon Visage
    ctx.save();
    ctx.translate(gx, gy);

    // Rotating Shield Rings
    ctx.strokeStyle = mainColor;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(0, 0, this.radius + 18, this.angle, this.angle + Math.PI * 1.5);
    ctx.stroke();

    ctx.strokeStyle = accentColor;
    ctx.beginPath();
    ctx.arc(0, 0, this.radius + 30, -this.angle * 1.3, -this.angle * 1.3 + Math.PI * 1.3);
    ctx.stroke();

    // Dark Core Base Body
    ctx.fillStyle = darkBg;
    ctx.beginPath();
    ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = mainColor;
    ctx.lineWidth = 4;
    ctx.stroke();

    // Horns Evolve: (Phase 1: Small Antennas, Phase 2: Demon Horns, Phase 3: Massive Double Demon Horns)
    if (this.phase === 1) {
      // Cyan Antennas
      ctx.fillStyle = '#00ffff';
      ctx.fillRect(-25, -75, 4, 25);
      ctx.fillRect(21, -75, 4, 25);
    } else if (this.phase === 2) {
      // Violet Horns
      ctx.fillStyle = '#aa00ff';
      ctx.beginPath();
      ctx.moveTo(-25, -30);
      ctx.lineTo(-55, -85);
      ctx.lineTo(-10, -45);
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(25, -30);
      ctx.lineTo(55, -85);
      ctx.lineTo(10, -45);
      ctx.fill();
    } else {
      // Meltdown Cataclysm Double Horns
      ctx.fillStyle = '#ff0033';
      ctx.shadowColor = '#ff0033';
      ctx.shadowBlur = 15;
      // Horn 1
      ctx.beginPath();
      ctx.moveTo(-30, -25);
      ctx.lineTo(-70, -100);
      ctx.lineTo(-12, -45);
      ctx.fill();
      // Horn 2
      ctx.beginPath();
      ctx.moveTo(30, -25);
      ctx.lineTo(70, -100);
      ctx.lineTo(12, -45);
      ctx.fill();
      // Inner Spikes
      ctx.fillStyle = '#ffaa00';
      ctx.beginPath();
      ctx.moveTo(-15, -40);
      ctx.lineTo(0, -90);
      ctx.lineTo(15, -40);
      ctx.fill();
    }

    // Sinister AI Eye (Color morphs from Cyan -> Amber -> Burning Crimson)
    const eyeColor = this.phase === 3 ? '#ff0000' : this.phase === 2 ? '#ffaa00' : '#00ffff';
    ctx.fillStyle = eyeColor;
    ctx.shadowColor = eyeColor;
    ctx.shadowBlur = 22;
    ctx.beginPath();
    ctx.arc(0, 0, this.radius * 0.46, 0, Math.PI * 2);
    ctx.fill();

    // Piercing Dark Pupil
    ctx.fillStyle = '#000000';
    const pupilOffsetX = Math.sin(this.attackTimer * 0.04) * 8;
    ctx.beginPath();
    ctx.arc(pupilOffsetX, 0, this.radius * 0.22, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    // 4. Draw Bullets
    for (const b of this.bullets) {
      ctx.save();
      ctx.fillStyle = b.color;
      ctx.shadowColor = b.color;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }
}

window.SentientBoss = SentientBoss;
