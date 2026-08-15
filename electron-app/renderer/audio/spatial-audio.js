/**
 * SENTIENT_OS v2 — Spatial Audio & SFX / Stinger Player
 * Features Stereo Panning and Procedural Horror SFX synthesis.
 */

class SpatialAudioPlayer {
  constructor(ambientEngine) {
    this.ambientEngine = ambientEngine;
  }

  get ctx() {
    this.ambientEngine.ensureContext();
    return this.ambientEngine.ctx;
  }

  playSFX(name = 'click_soft', options = {}) {
    const ctx = this.ctx;
    if (!ctx) return;

    const pan = options.pan !== undefined ? Math.max(-1.0, Math.min(1.0, options.pan)) : 0.0;
    const volume = options.volume !== undefined ? Math.max(0.0, Math.min(1.0, options.volume)) : 0.5;

    const panner = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
    if (panner) panner.pan.setValueAtTime(pan, ctx.currentTime);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(volume, ctx.currentTime);

    if (panner) {
      gain.connect(panner);
      panner.connect(ctx.destination);
    } else {
      gain.connect(ctx.destination);
    }

    const now = ctx.currentTime;

    if (name === 'click_soft' || name === 'click') {
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1200, now);
      osc.frequency.exponentialRampToValueAtTime(100, now + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.03);
      osc.connect(gain);
      osc.start(now);
      osc.stop(now + 0.035);
    } else if (name === 'static_low' || name === 'static_burst') {
      const bufferSize = ctx.sampleRate * 0.2; // 200ms noise
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = (Math.random() * 2 - 1) * 0.4;
      }
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      gain.gain.setValueAtTime(volume, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      noise.connect(gain);
      noise.start(now);
    } else if (name === 'stinger_scare' || name === 'crisis_hit') {
      // Harsh dissonant cluster hit
      const freqs = [180, 255, 360, 510, 720];
      gain.gain.setValueAtTime(volume * 1.2, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);

      freqs.forEach((f) => {
        const osc = ctx.createOscillator();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(f, now);
        osc.frequency.exponentialRampToValueAtTime(f * 0.7, now + 1.2);
        osc.connect(gain);
        osc.start(now);
        osc.stop(now + 1.25);
      });
    }
  }

  playStinger(name = 'stinger_scare', options = {}) {
    this.playSFX(name, { ...options, volume: options.volume || 0.8 });
  }
}

window.SpatialAudioPlayer = SpatialAudioPlayer;
