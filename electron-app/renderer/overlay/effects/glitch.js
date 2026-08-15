/**
 * SENTIENT_OS v2 — Glitch Effect Module
 * Supports: tear, static, invert, desaturate, rgb_split, scanlines
 */

class GlitchEffect {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas ? canvas.getContext('2d') : null;
    this.active = false;
    this.animFrame = null;
    this.container = document.getElementById('overlay-container') || document.body;
  }

  trigger(params = {}) {
    const type = params.type || 'tear';
    const intensity = Math.max(0.05, Math.min(1.0, params.intensity || 0.5));
    const durationMs = params.duration_ms || 1000;

    switch (type) {
      case 'tear':
        this.runTear(intensity, durationMs);
        break;
      case 'static':
        this.runStatic(intensity, durationMs);
        break;
      case 'invert':
        this.runInvert(durationMs);
        break;
      case 'desaturate':
        this.runDesaturate(durationMs);
        break;
      case 'rgb_split':
        this.runRgbSplit(intensity, durationMs);
        break;
      case 'scanlines':
        this.runScanlines(durationMs);
        break;
      default:
        this.runTear(intensity, durationMs);
    }
  }

  runTear(intensity, durationMs) {
    const sliceCount = Math.floor(3 + intensity * 15);
    const maxOffset = intensity * 40;
    const slices = [];

    for (let i = 0; i < sliceCount; i++) {
      const slice = document.createElement('div');
      slice.className = 'glitch-tear-slice';
      const top = Math.random() * 100;
      const height = Math.random() * 8 + 2;
      const offset = (Math.random() - 0.5) * maxOffset * 2;
      slice.style.top = `${top}%`;
      slice.style.height = `${height}px`;
      slice.style.transform = `translateX(${offset}px)`;
      this.container.appendChild(slice);
      slices.push(slice);
    }

    setTimeout(() => {
      slices.forEach((s) => s.remove());
    }, durationMs);
  }

  runStatic(intensity, durationMs) {
    if (!this.ctx) return;
    this.active = true;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const pixelSize = Math.max(2, Math.floor(6 - intensity * 4));

    const drawNoise = () => {
      if (!this.active) return;
      this.ctx.clearRect(0, 0, width, height);

      const numPixels = Math.floor((width * height) / (pixelSize * pixelSize) * (intensity * 0.2));
      this.ctx.fillStyle = `rgba(255, 255, 255, ${0.4 + intensity * 0.5})`;

      for (let i = 0; i < numPixels; i++) {
        const x = Math.floor(Math.random() * (width / pixelSize)) * pixelSize;
        const y = Math.floor(Math.random() * (height / pixelSize)) * pixelSize;
        this.ctx.fillRect(x, y, pixelSize, pixelSize);
      }

      this.animFrame = requestAnimationFrame(drawNoise);
    };

    drawNoise();

    setTimeout(() => {
      this.active = false;
      if (this.animFrame) cancelAnimationFrame(this.animFrame);
      if (this.ctx) this.ctx.clearRect(0, 0, width, height);
    }, durationMs);
  }

  runInvert(durationMs) {
    this.container.classList.add('fx-invert');
    setTimeout(() => this.container.classList.remove('fx-invert'), durationMs);
  }

  runDesaturate(durationMs) {
    this.container.classList.add('fx-desaturate');
    setTimeout(() => this.container.classList.remove('fx-desaturate'), durationMs);
  }

  runRgbSplit(intensity, durationMs) {
    this.container.classList.add('fx-rgb-split');
    const offset = Math.round(intensity * 12);
    document.documentElement.style.setProperty('--rgb-offset', `${offset}px`);
    setTimeout(() => {
      this.container.classList.remove('fx-rgb-split');
    }, durationMs);
  }

  runScanlines(durationMs) {
    const scanlineLayer = document.createElement('div');
    scanlineLayer.className = 'fx-scanlines';
    this.container.appendChild(scanlineLayer);
    setTimeout(() => scanlineLayer.remove(), durationMs);
  }
}

window.GlitchEffect = GlitchEffect;
