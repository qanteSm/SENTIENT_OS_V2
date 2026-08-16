/**
 * SENTIENT_OS v2 — Level Geometry, Platforms & Collectibles
 * Spawns both Energy Orbs and Health Heart Repair Pickups
 */

class PlatformManager {
  constructor(canvasWidth = 1280, canvasHeight = 720) {
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;

    this.platforms = [
      // Solid Ground
      { x: 0, y: 640, w: canvasWidth, h: 80, type: 'ground' },

      // Lower Tier Platforms
      { x: 100, y: 530, w: 260, h: 18 },
      { x: 920, y: 530, w: 260, h: 18 },

      // Mid Tier Stepping Platforms
      { x: 360, y: 430, w: 260, h: 18 },
      { x: 660, y: 430, w: 260, h: 18 },

      // High Tier Sniper & Evasion Platforms
      { x: 480, y: 290, w: 320, h: 18 },
      { x: 60, y: 330, w: 220, h: 18 },
      { x: 1000, y: 330, w: 220, h: 18 },
    ];

    this.orbs = [];
    this.spawnTimer = 0;
    this.heartSpawnTimer = 0;
  }

  update(player, particles, audio) {
    this.spawnTimer++;
    this.heartSpawnTimer++;

    // 1. Spawn Energy Orbs
    if (this.spawnTimer > 120 && this.orbs.filter(o => o.type === 'energy').length < 4) {
      this.spawnTimer = 0;
      const validPlats = this.platforms.filter((p) => p.type !== 'ground');
      const plat = validPlats[Math.floor(Math.random() * validPlats.length)];
      this.orbs.push({
        type: 'energy',
        x: plat.x + plat.w / 2,
        y: plat.y - 28,
        radius: 9,
        bob: 0,
      });
    }

    // 2. Spawn Health Repair Hearts (every 8-10 seconds if needed)
    if (this.heartSpawnTimer > 400 && this.orbs.filter(o => o.type === 'heart').length < 2) {
      this.heartSpawnTimer = 0;
      const validPlats = this.platforms.filter((p) => p.type !== 'ground');
      const plat = validPlats[Math.floor(Math.random() * validPlats.length)];
      this.orbs.push({
        type: 'heart',
        x: plat.x + plat.w / 2,
        y: plat.y - 30,
        radius: 11,
        bob: Math.PI,
      });
    }

    // 3. Collect Orb Checks
    for (let i = this.orbs.length - 1; i >= 0; i--) {
      const orb = this.orbs[i];
      orb.bob += 0.06;

      if (player) {
        const dist = Math.hypot(player.x + player.w / 2 - orb.x, player.y + player.h / 2 - orb.y);
        if (dist < 32) {
          if (orb.type === 'heart') {
            player.heal(1, particles, audio);
          } else {
            player.energy = Math.min(player.maxEnergy, player.energy + 50);
            audio.playTone(880, 0.2, 'triangle', 0.1);
            particles.spawn(orb.x, orb.y, '#00ff88', 16, 4.5);
            particles.spawnShockwave(orb.x, orb.y, '#00ff88', 45);
          }
          this.orbs.splice(i, 1);
        }
      }
    }
  }

  draw(ctx) {
    // 1. Cyber Grid Background
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < this.canvasWidth; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvasHeight);
      ctx.stroke();
    }
    for (let y = 0; y < this.canvasHeight; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvasWidth, y);
      ctx.stroke();
    }
    ctx.restore();

    // 2. Platforms
    for (const plat of this.platforms) {
      ctx.save();
      ctx.fillStyle = plat.type === 'ground' ? '#090d14' : '#111824';
      ctx.fillRect(plat.x, plat.y, plat.w, plat.h);

      // Neon Border
      ctx.strokeStyle = '#00ffff';
      ctx.lineWidth = 2;
      ctx.strokeRect(plat.x, plat.y, plat.w, plat.h);

      // Top glowing energy edge
      ctx.fillStyle = '#00ffff';
      ctx.shadowColor = '#00ffff';
      ctx.shadowBlur = 8;
      ctx.fillRect(plat.x, plat.y, plat.w, 3);
      ctx.restore();
    }

    // 3. Collectibles (Energy Orbs & Hearts)
    for (const orb of this.orbs) {
      const yOffset = Math.sin(orb.bob) * 6;

      ctx.save();
      if (orb.type === 'heart') {
        // Glowing Pink/Red Heart
        ctx.fillStyle = '#ff2255';
        ctx.shadowColor = '#ff2255';
        ctx.shadowBlur = 18;
        ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('❤', orb.x, orb.y + yOffset);
      } else {
        // Glowing Green Energy Orb
        ctx.fillStyle = '#00ff88';
        ctx.shadowColor = '#00ff88';
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.arc(orb.x, orb.y + yOffset, orb.radius, 0, Math.PI * 2);
        ctx.fill();

        // Pulsing Ring
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(orb.x, orb.y + yOffset, orb.radius + Math.sin(orb.bob * 2) * 3, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }
  }
}

window.PlatformManager = PlatformManager;
