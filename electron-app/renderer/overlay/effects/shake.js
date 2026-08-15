/**
 * SENTIENT_OS v2 — Screen Shake Effect Module
 */

class ShakeEffect {
  constructor(targetElement) {
    this.target = targetElement || document.getElementById('overlay-container') || document.body;
    this.timer = null;
  }

  trigger(params = {}) {
    const intensity = Math.max(0.05, Math.min(1.0, params.intensity || 0.3));
    const durationMs = params.duration_ms || 800;
    const maxOffset = Math.round(intensity * 18); // 1 to 18px

    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }

    const startTime = Date.now();
    const intervalMs = 40; // 25 fps shake

    this.timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      if (elapsed >= durationMs) {
        clearInterval(this.timer);
        this.timer = null;
        this.target.style.transform = 'none';
        return;
      }

      // Linear decay over duration
      const decay = 1.0 - (elapsed / durationMs);
      const currentMax = maxOffset * decay;
      const offsetX = (Math.random() * 2 - 1) * currentMax;
      const offsetY = (Math.random() * 2 - 1) * currentMax;
      const rotate = (Math.random() * 2 - 1) * (intensity * 1.5 * decay);

      this.target.style.transform = `translate(${offsetX.toFixed(1)}px, ${offsetY.toFixed(1)}px) rotate(${rotate.toFixed(2)}deg)`;
    }, intervalMs);
  }
}

window.ShakeEffect = ShakeEffect;
