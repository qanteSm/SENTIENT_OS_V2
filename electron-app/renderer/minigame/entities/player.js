/**
 * SENTIENT_OS v2 — Player Entity Controller
 * 5 Max Hearts, Generous I-Frames, Smooth 360° Aiming & Fast Recovery
 */

class Player {
  constructor(x = 220, y = 500) {
    this.x = x;
    this.y = y;
    this.w = 26;
    this.h = 42;
    this.vx = 0;
    this.vy = 0;

    // 5 Hearts for a much more forgiving, fun experience!
    this.hp = 5;
    this.maxHp = 5;
    this.energy = 100;
    this.maxEnergy = 100;

    this.isGrounded = false;
    this.jumpsLeft = 2;
    this.dashCooldown = 0;
    this.dashTimer = 0;
    this.facingRight = true;
    this.invulnerableTimer = 0;
    this.shootCooldown = 0;

    this.coyoteTime = 0;
    this.jumpBuffer = 0;

    this.bullets = [];
    this.aimAngle = 0;
  }

  update(keys, mousePos, platforms, particles, audio, canvasWidth, canvasHeight) {
    // 1. Aiming Angle
    if (mousePos) {
      const centerX = this.x + this.w / 2;
      const centerY = this.y + this.h / 2;
      const dx = mousePos.x - centerX;
      const dy = mousePos.y - centerY;
      this.aimAngle = Math.atan2(dy, dx);
      this.facingRight = mousePos.x >= centerX;
    }

    // 2. Fast Energy Regeneration
    this.energy = Math.min(this.maxEnergy, this.energy + 0.65);
    if (this.dashCooldown > 0) this.dashCooldown--;
    if (this.invulnerableTimer > 0) this.invulnerableTimer--;
    if (this.shootCooldown > 0) this.shootCooldown--;
    if (this.jumpBuffer > 0) this.jumpBuffer--;

    // 3. Coyote time management
    if (this.isGrounded) {
      this.coyoteTime = 10;
      this.jumpsLeft = 2;
    } else if (this.coyoteTime > 0) {
      this.coyoteTime--;
    }

    // 4. Shooting
    if (keys.shoot) {
      this.tryShoot(mousePos, particles, audio);
    }

    // 5. Jump Buffer
    if (this.jumpBuffer > 0 && (this.isGrounded || this.coyoteTime > 0 || this.jumpsLeft > 0)) {
      this.executeJump(particles, audio);
      this.jumpBuffer = 0;
    }

    // 6. Horizontal Movement & Dash
    if (this.dashTimer > 0) {
      this.dashTimer--;
      if (this.dashTimer % 2 === 0) {
        particles.spawnGhost(this.x, this.y, this.w, this.h, this.facingRight, 'rgba(0, 255, 255, 0.7)');
      }
    } else {
      if (keys.left) {
        this.vx = -7.5;
      } else if (keys.right) {
        this.vx = 7.5;
      } else {
        this.vx *= 0.82;
      }

      // Smooth floaty gravity
      this.vy += 0.55;
      if (this.vy > 13.0) this.vy = 13.0;
    }

    this.x += this.vx;
    this.y += this.vy;

    // 7. Platform Collisions
    this.isGrounded = false;
    for (const plat of platforms) {
      if (
        this.x + this.w > plat.x &&
        this.x < plat.x + plat.w &&
        this.y + this.h >= plat.y &&
        this.y + this.h - this.vy <= plat.y + 14 &&
        this.vy >= 0
      ) {
        this.y = plat.y - this.h;
        this.vy = 0;
        this.isGrounded = true;
        this.jumpsLeft = 2;
      }
    }

    // 8. Screen Boundaries & Void Recovery
    if (this.x < 0) this.x = 0;
    if (this.x + this.w > canvasWidth) this.x = canvasWidth - this.w;

    if (this.y > canvasHeight + 40) {
      this.hurt(1, particles, audio);
      this.x = 640;
      this.y = 280;
      this.vy = 0;
    }

    // 9. Update Player Bullets
    for (let i = this.bullets.length - 1; i >= 0; i--) {
      const b = this.bullets[i];
      b.x += b.vx;
      b.y += b.vy;
      b.life--;

      if (b.life <= 0 || b.x < 0 || b.x > canvasWidth || b.y < 0 || b.y > canvasHeight) {
        this.bullets.splice(i, 1);
      }
    }
  }

  queueJump() {
    this.jumpBuffer = 8;
  }

  executeJump(particles, audio) {
    if (this.isGrounded || this.coyoteTime > 0) {
      this.vy = -14.8;
      this.coyoteTime = 0;
      this.jumpsLeft = 1;
      this.isGrounded = false;
      audio.playJump();
      particles.spawn(this.x + this.w / 2, this.y + this.h, '#00ffff', 8, 3);
    } else if (this.jumpsLeft > 0) {
      this.vy = -13.5;
      this.jumpsLeft = 0;
      this.isGrounded = false;
      audio.playDoubleJump();
      particles.spawn(this.x + this.w / 2, this.y + this.h, '#ff00ff', 12, 4);
    }
  }

  tryDash(particles, audio) {
    if (this.dashCooldown <= 0 && this.energy >= 15) {
      this.energy -= 15;
      this.dashTimer = 14;
      this.dashCooldown = 22;
      audio.playDash();
      const dir = this.facingRight ? 1 : -1;
      this.vx = dir * 20.0;
      this.vy = 0;
      particles.spawn(this.x + this.w / 2, this.y + this.h / 2, '#00ffff', 16, 5);
      particles.spawnShockwave(this.x + this.w / 2, this.y + this.h / 2, '#00ffff', 45);
    }
  }

  tryShoot(mousePos, particles, audio) {
    if (this.shootCooldown <= 0 && this.energy >= 5) {
      this.energy -= 5;
      this.shootCooldown = 8; // Fast, responsive firing
      audio.playShoot();

      const startX = this.x + this.w / 2;
      const startY = this.y + 16;

      let vx, vy;
      if (mousePos) {
        const dx = mousePos.x - startX;
        const dy = mousePos.y - startY;
        const dist = Math.hypot(dx, dy) || 1;
        const speed = 20;
        vx = (dx / dist) * speed;
        vy = (dy / dist) * speed;
      } else {
        const dir = this.facingRight ? 1 : -1;
        vx = dir * 20;
        vy = 0;
      }

      this.bullets.push({
        x: startX,
        y: startY,
        vx,
        vy,
        radius: 7,
        damage: 4.5, // High impact player damage
        life: 60,
      });

      particles.spawn(startX + vx * 0.7, startY + vy * 0.7, '#00ffff', 5, 2.5);
    }
  }

  heal(amount, particles, audio) {
    if (this.hp < this.maxHp) {
      this.hp = Math.min(this.maxHp, this.hp + amount);
      audio.playTone(1040, 0.3, 'triangle', 0.15);
      particles.spawn(this.x + this.w / 2, this.y + this.h / 2, '#ff3366', 20, 4);
      particles.spawnShockwave(this.x + this.w / 2, this.y + this.h / 2, '#ff3366', 50);
    }
  }

  hurt(dmg, particles, audio) {
    if (this.invulnerableTimer > 0 || this.dashTimer > 0) return;
    this.hp -= dmg;
    this.invulnerableTimer = 110; // ~1.8 seconds of generous safety!
    audio.playPlayerHurt();
    particles.spawn(this.x + this.w / 2, this.y + this.h / 2, '#ff2244', 20, 6);
    particles.spawnShockwave(this.x + this.w / 2, this.y + this.h / 2, '#ff2244', 60);
  }

  draw(ctx, mousePos) {
    if (this.invulnerableTimer > 0 && Math.floor(this.invulnerableTimer / 4) % 2 === 0) {
      return;
    }

    ctx.save();
    ctx.translate(this.x, this.y);

    if (this.dashTimer > 0) {
      ctx.shadowColor = '#00ffff';
      ctx.shadowBlur = 20;
    }

    // Main Armor Body
    ctx.fillStyle = this.dashTimer > 0 ? '#ffffff' : '#0a1626';
    ctx.fillRect(0, 0, this.w, this.h);

    // Neon Frame
    ctx.strokeStyle = '#00ffff';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, this.w, this.h);

    // Visor Headpiece
    ctx.fillStyle = '#ff0055';
    const visorX = this.facingRight ? 14 : 2;
    ctx.fillRect(visorX, 6, 10, 8);

    // Energy Core in chest
    ctx.fillStyle = this.energy > 20 ? '#00ffff' : '#ffaa00';
    ctx.beginPath();
    ctx.arc(this.w / 2, 22, 4, 0, Math.PI * 2);
    ctx.fill();

    // Aiming Gun Arm / Barrel pointing at mouse cursor
    ctx.save();
    ctx.translate(this.w / 2, 16);
    ctx.rotate(this.aimAngle);
    ctx.fillStyle = '#00ffff';
    ctx.shadowColor = '#00ffff';
    ctx.shadowBlur = 8;
    ctx.fillRect(0, -3, 18, 6);
    ctx.restore();

    // Thruster Boots
    ctx.fillStyle = '#00ffff';
    ctx.fillRect(2, this.h - 4, 8, 4);
    ctx.fillRect(this.w - 10, this.h - 4, 8, 4);

    ctx.restore();

    // Draw Aiming Laser Guide Line
    if (mousePos) {
      ctx.save();
      ctx.strokeStyle = 'rgba(0, 255, 255, 0.25)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(this.x + this.w / 2, this.y + 16);
      ctx.lineTo(mousePos.x, mousePos.y);
      ctx.stroke();
      ctx.restore();
    }

    // Draw Bullets
    for (const b of this.bullets) {
      ctx.save();
      ctx.fillStyle = '#00ffff';
      ctx.shadowColor = '#00ffff';
      ctx.shadowBlur = 14;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }
}

window.Player = Player;
