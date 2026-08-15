/**
 * SENTIENT_OS v2 — Screen Fade & Blackout Effect Module
 */

class FadeEffect {
  constructor(fadeLayer) {
    this.layer = fadeLayer || document.getElementById('screen-fade-layer');
  }

  trigger(params = {}) {
    const targetOpacity = params.target_opacity !== undefined ? params.target_opacity : 1.0;
    const durationMs = params.duration_ms || 1000;
    const restoreAfterMs = params.restore_after_ms || (params.blackout ? (params.duration_ms || 2500) : 0);
    const color = params.color || '#000000';

    if (!this.layer) return;

    this.layer.style.backgroundColor = color;
    this.layer.style.transition = `opacity ${Math.min(300, durationMs)}ms ease`;
    this.layer.style.opacity = Math.max(0.0, Math.min(1.0, targetOpacity)).toString();

    // Auto-restore after delay if flash or blackout
    if (params.flash || restoreAfterMs > 0) {
      const waitTime = restoreAfterMs > 0 ? restoreAfterMs : durationMs;
      setTimeout(() => {
        if (this.layer) {
          this.layer.style.transition = 'opacity 800ms ease';
          this.layer.style.opacity = '0';
        }
      }, waitTime);
    }
  }

  blackout(durationMs = 2500) {
    this.trigger({ color: '#000000', target_opacity: 1.0, duration_ms: 150, restore_after_ms: durationMs });
  }

  flash(color = '#ffffff', durationMs = 500) {
    this.trigger({ color, target_opacity: 0.9, duration_ms: durationMs, flash: true });
  }
}

window.FadeEffect = FadeEffect;
