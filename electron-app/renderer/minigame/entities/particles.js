/**
 * SENTIENT_OS v2 — Particle & Visual FX System
 */

class ParticleSystem {
  constructor() {
    this.particles = [];
    this.ghosts = [];
  }

  spawn(x, y, color, count = 8, speed = 4, life = 30, size = 4) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const spd = (Math.random() * 0.7 + 0.3) * speed;
      this.particles.push({
        x,
        y,
        vx: Math.cos(angle) * spd,
        vy: Math.sin(angle) * spd,
        color,
        size: Math.random() * size + 2,
        life,
        maxLife: life,
        shape: Math.random() < 0.3 ? 'square' : 'circle',
      });
    }
  }

  spawnGhost(x, y, w, h, facingRight, color = 'rgba(0, 255, 255, 0.4)') {
    this.ghosts.push({
      x,
      y,
      w,
      h,
      facingRight,
      color,
      alpha: 0.6,
      decay: 0.05,
    });
  }

  spawnShockwave(x, y, color = '#ff0055', maxRadius = 80) {
    this.particles.push({
      x,
      y,
      radius: 5,
      maxRadius,
      color,
      life: 25,
      maxLife: 25,
      isWave: true,
    });
  }

  updateAndDraw(ctx) {
    // 1. Draw Player Dash Ghosts
    for (let i = this.ghosts.length - 1; i >= 0; i--) {
      const g = this.ghosts[i];
      g.alpha -= g.decay;
      if (g.alpha <= 0) {
        this.ghosts.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.globalAlpha = g.alpha;
      ctx.fillStyle = g.color;
      ctx.fillRect(g.x, g.y, g.w, g.h);
      ctx.restore();
    }

    // 2. Draw Particles & Shockwaves
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.life--;

      if (p.isWave) {
        p.radius += (p.maxRadius - p.radius) * 0.15;
        const alpha = p.life / p.maxLife;
        ctx.save();
        ctx.strokeStyle = p.color;
        ctx.lineWidth = 3 * alpha;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      } else {
        p.x += p.vx;
        p.y += p.vy;
        const alpha = p.life / p.maxLife;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = alpha;

        if (p.shape === 'circle') {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillRect(p.x, p.y, p.size, p.size);
        }
        ctx.globalAlpha = 1.0;
      }

      if (p.life <= 0) {
        this.particles.splice(i, 1);
      }
    }
  }

  clear() {
    this.particles = [];
    this.ghosts = [];
  }
}

window.ParticleSystem = ParticleSystem;
