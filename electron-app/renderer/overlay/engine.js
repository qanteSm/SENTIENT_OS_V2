/**
 * SENTIENT_OS v2 — Overlay Effect Engine Skeleton (Phase 1)
 */

class OverlayEffectEngine {
  constructor() {
    this.canvas = document.getElementById('glitch-canvas');
    this.textLayer = document.getElementById('text-overlay-layer');
    this.fadeLayer = document.getElementById('screen-fade-layer');
    this.vignetteLayer = document.getElementById('vignette-layer');

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    console.log('[OverlayEngine] Visual effect engine initialized in background');
  }

  resizeCanvas() {
    if (this.canvas) {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    }
  }

  displayText(text, durationMs = 3000) {
    if (!this.textLayer) return;
    this.textLayer.textContent = text;
    setTimeout(() => {
      if (this.textLayer.textContent === text) {
        this.textLayer.textContent = '';
      }
    }, durationMs);
  }

  setFade(opacity, durationMs = 1000) {
    if (!this.fadeLayer) return;
    this.fadeLayer.style.transition = `opacity ${durationMs}ms ease`;
    this.fadeLayer.style.opacity = opacity.toString();
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.overlayEngine = new OverlayEffectEngine();
});
