/**
 * SENTIENT_OS v2 — Screen Fade & Flash Effect Module
 */

class FadeEffect {
  constructor(fadeLayer) {
    this.layer = fadeLayer || document.getElementById('screen-fade-layer');
  }

  trigger(params = {}) {
    const targetOpacity = params.target_opacity !== undefined ? params.target_opacity : 1.0;
    const durationMs = params.duration_ms || 1000;
    const color = params.color || '#000000';

    if (!this.layer) return;

    this.layer.style.backgroundColor = color;
    this.layer.style.transition = `opacity ${durationMs}ms ease`;
    this.layer.style.opacity = Math.max(0.0, Math.min(1.0, targetOpacity)).toString();

    // If flash (e.g. white or red pulse), automatically restore after duration
    if (params.flash) {
      setTimeout(() => {
        this.layer.style.opacity = '0';
      }, durationMs);
    }
  }

  flash(color = '#ffffff', durationMs = 500) {
    this.trigger({ color, target_opacity: 0.9, duration_ms: durationMs, flash: true });
  }
}

window.FadeEffect = FadeEffect;
