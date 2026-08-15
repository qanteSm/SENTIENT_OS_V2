/**
 * SENTIENT_OS v2 — Screen Shake & Jitter Effect Module
 */

class ShakeEffect {
  constructor(targetElement) {
    this.target = targetElement || document.getElementById('overlay-container') || document.body;
    this.fadeLayer = document.getElementById('screen-fade-layer');
    this.timer = null;
  }

  trigger(params = {}) {
    const intensity = Math.max(0.1, Math.min(1.0, params.intensity || 0.4));
    const durationMs = params.duration_ms || 1000;
    const maxOffset = Math.round(intensity * 25); // 2 to 25px

    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }

    // Flash a subtle horror vignette
    if (this.fadeLayer) {
      this.fadeLayer.style.backgroundColor = '#ff0000';
      this.fadeLayer.style.transition = 'opacity 0.1s ease';
      this.fadeLayer.style.opacity = (intensity * 0.25).toString();
      setTimeout(() => {
        if (this.fadeLayer) this.fadeLayer.style.opacity = '0';
      }, 150);
    }

    const startTime = Date.now();
    const intervalMs = 35; // ~30 fps shake

    this.timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      if (elapsed >= durationMs) {
        clearInterval(this.timer);
        this.timer = null;
        this.target.style.transform = 'none';
        return;
      }

      // Linear decay
      const decay = 1.0 - (elapsed / durationMs);
      const currentMax = maxOffset * decay;
      const offsetX = (Math.random() * 2 - 1) * currentMax;
      const offsetY = (Math.random() * 2 - 1) * currentMax;
      const rotate = (Math.random() * 2 - 1) * (intensity * 2.0 * decay);

      this.target.style.transform = `translate(${offsetX.toFixed(1)}px, ${offsetY.toFixed(1)}px) rotate(${rotate.toFixed(2)}deg)`;
    }, intervalMs);
  }
}

window.ShakeEffect = ShakeEffect;
