/**
 * SENTIENT_OS v2 — Procedural Web Audio Ambient Engine
 * Synthesizes 6 atmospheric horror drone moods with smooth 5-second crossfades.
 */

class AmbientEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.currentMood = 'silence';
    this.activeNodes = [];
    this.heartbeatTimer = null;
  }

  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.3, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  setMood(mood = 'calm', fadeSec = 5.0) {
    this.ensureContext();
    if (this.currentMood === mood) return;

    console.log(`[AmbientEngine] Crossfading mood: ${this.currentMood} -> ${mood} (${fadeSec}s)`);
    this.currentMood = mood;

    // Fade out previous nodes
    const now = this.ctx.currentTime;
    const oldNodes = [...this.activeNodes];
    this.activeNodes = [];

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    oldNodes.forEach(({ gain, stopFunc }) => {
      gain.gain.setValueAtTime(gain.gain.value, now);
      gain.gain.linearRampToValueAtTime(0.0001, now + fadeSec);
      setTimeout(() => {
        if (stopFunc) stopFunc();
      }, fadeSec * 1000 + 100);
    });

    if (mood === 'silence') return;

    // Build new procedural drone for mood
    const newGain = this.ctx.createGain();
    newGain.gain.setValueAtTime(0.0001, now);
    newGain.gain.linearRampToValueAtTime(this.getMoodVolume(mood), now + fadeSec);
    newGain.connect(this.masterGain);

    const stopFunc = this.startMoodSynthesizer(mood, newGain);
    this.activeNodes.push({ gain: newGain, stopFunc });
  }

  getMoodVolume(mood) {
    switch (mood) {
      case 'calm': return 0.15;
      case 'tense': return 0.25;
      case 'intimate': return 0.20;
      case 'hostile': return 0.35;
      case 'dread': return 0.40;
      default: return 0.20;
    }
  }

  startMoodSynthesizer(mood, outputGain) {
    const now = this.ctx.currentTime;
    const oscillators = [];

    if (mood === 'calm') {
      // Soft 55Hz low sine drone
      const osc = this.ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(55, now);
      osc.connect(outputGain);
      osc.start();
      oscillators.push(osc);
    } else if (mood === 'tense') {
      // Dissonant dual saw with lowpass filter
      const filter = this.ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(280, now);
      filter.connect(outputGain);

      const osc1 = this.ctx.createOscillator();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(55, now);
      osc1.connect(filter);
      osc1.start();
      oscillators.push(osc1);

      const osc2 = this.ctx.createOscillator();
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(58.7, now); // Detuned minor second
      osc2.connect(filter);
      osc2.start();
      oscillators.push(osc2);
    } else if (mood === 'intimate') {
      // Slow pulsing sine wave
      const osc = this.ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(65, now);

      const lfo = this.ctx.createOscillator();
      lfo.frequency.setValueAtTime(0.2, now); // 5s breath cycle
      const lfoGain = this.ctx.createGain();
      lfoGain.gain.setValueAtTime(15, now);
      lfo.connect(lfoGain);
      lfoGain.connect(osc.frequency);
      lfo.start();
      oscillators.push(lfo);

      osc.connect(outputGain);
      osc.start();
      oscillators.push(osc);
    } else if (mood === 'hostile') {
      // Distorted square drone + rhythmic heartbeat
      const filter = this.ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(180, now);
      filter.connect(outputGain);

      const osc = this.ctx.createOscillator();
      osc.type = 'square';
      osc.frequency.setValueAtTime(45, now);
      osc.connect(filter);
      osc.start();
      oscillators.push(osc);

      // Procedural heartbeat
      this.heartbeatTimer = setInterval(() => {
        if (!this.ctx || this.currentMood !== 'hostile') return;
        this.playHeartbeatThud(outputGain);
      }, 900);
    } else if (mood === 'dread') {
      // Infrasound sub-bass (28Hz) + eerie harmonic (110Hz)
      const osc1 = this.ctx.createOscillator();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(28, now);
      osc1.connect(outputGain);
      osc1.start();
      oscillators.push(osc1);

      const osc2 = this.ctx.createOscillator();
      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(110, now);
      osc2.connect(outputGain);
      osc2.start();
      oscillators.push(osc2);
    }

    return () => {
      oscillators.forEach((o) => {
        try { o.stop(); o.disconnect(); } catch (e) {}
      });
    };
  }

  playHeartbeatThud(outputGain) {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(80, now);
    osc.frequency.exponentialRampToValueAtTime(30, now + 0.15);

    gain.gain.setValueAtTime(0.7, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    osc.connect(gain);
    gain.connect(outputGain);
    osc.start(now);
    osc.stop(now + 0.16);
  }

  setVolumeDucking(factor = 0.3, durationSec = 0.5) {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;
    this.masterGain.gain.linearRampToValueAtTime(0.3 * factor, now + durationSec);
  }

  restoreVolume(durationSec = 0.5) {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;
    this.masterGain.gain.linearRampToValueAtTime(0.3, now + durationSec);
  }
}

window.AmbientEngine = AmbientEngine;
