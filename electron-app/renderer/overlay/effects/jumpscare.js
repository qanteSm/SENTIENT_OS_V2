/**
 * SENTIENT_OS v2 — High-Impact Jumpscare Effect Module
 * Visual: Fullscreen flash + screaming analog horror face with RGB glitch shake
 * Audio: Multi-layer procedural bloodcurdling screech synthesizer
 */

class JumpscareEffect {
  constructor() {
    this.container = document.getElementById('jumpscare-container');
    this.audioCtx = null;
  }

  getAudioContext() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  playHorrorScreech(durationS = 1.0) {
    try {
      const ctx = this.getAudioContext();
      const now = ctx.currentTime;

      // 1. Screeching high-frequency oscillator with aggressive pitch modulation
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain1 = ctx.createGain();

      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(800, now);
      osc1.frequency.exponentialRampToValueAtTime(3200, now + 0.15);
      osc1.frequency.linearRampToValueAtTime(1400, now + durationS);

      osc2.type = 'square';
      osc2.frequency.setValueAtTime(850, now);
      osc2.frequency.exponentialRampToValueAtTime(3400, now + 0.12);
      osc2.frequency.linearRampToValueAtTime(900, now + durationS);

      // 2. White noise burst (for throat screech grit)
      const bufferSize = ctx.sampleRate * durationS;
      const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = noiseBuffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
      }
      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = noiseBuffer;

      const noiseFilter = ctx.createBiquadFilter();
      noiseFilter.type = 'bandpass';
      noiseFilter.frequency.setValueAtTime(2200, now);
      noiseFilter.Q.setValueAtTime(3.0, now);

      // Distortion wave shaper
      const distortion = ctx.createWaveShaper();
      const curve = new Float32Array(256);
      for (let i = 0; i < 256; i++) {
        const x = (i * 2) / 256 - 1;
        curve[i] = ((3 + 20) * x * 20 * (Math.PI / 180)) / (Math.PI + 20 * Math.abs(x));
      }
      distortion.curve = curve;

      // 3. Sub-bass shockwave hit
      const subOsc = ctx.createOscillator();
      const subGain = ctx.createGain();
      subOsc.type = 'sine';
      subOsc.frequency.setValueAtTime(150, now);
      subOsc.frequency.exponentialRampToValueAtTime(25, now + 0.5);
      subGain.gain.setValueAtTime(1.0, now);
      subGain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);

      subOsc.connect(subGain);
      subGain.connect(ctx.destination);

      // Master screech gain envelope
      gain1.gain.setValueAtTime(0.01, now);
      gain1.gain.linearRampToValueAtTime(0.95, now + 0.04);
      gain1.gain.exponentialRampToValueAtTime(0.01, now + durationS);

      osc1.connect(distortion);
      osc2.connect(distortion);
      distortion.connect(gain1);

      whiteNoise.connect(noiseFilter);
      noiseFilter.connect(gain1);

      gain1.connect(ctx.destination);

      osc1.start(now);
      osc2.start(now);
      whiteNoise.start(now);
      subOsc.start(now);

      osc1.stop(now + durationS);
      osc2.stop(now + durationS);
      whiteNoise.stop(now + durationS);
      subOsc.stop(now + durationS);
    } catch (e) {
      console.warn('[Jumpscare] Audio synthesis failed:', e);
    }
  }

  trigger(params = {}) {
    const durationMs = params.duration_ms || 1000;
    this.playHorrorScreech(durationMs / 1000.0);

    if (!this.container) {
      this.container = document.getElementById('jumpscare-container');
    }
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="jumpscare-overlay">
        <div class="jumpscare-glitch-layer"></div>
        <img class="jumpscare-face-img" src="../../assets/images/jumpscare.jpg" alt="" />
        <div class="jumpscare-flash"></div>
      </div>
    `;
    this.container.style.display = 'block';

    // Violent shake and strobe
    setTimeout(() => {
      if (this.container) {
        this.container.style.display = 'none';
        this.container.innerHTML = '';
      }
    }, durationMs);
  }
}

window.JumpscareEffect = JumpscareEffect;
