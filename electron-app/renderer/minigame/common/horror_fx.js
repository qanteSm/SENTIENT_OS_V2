/**
 * SENTIENT_OS v2 — Reusable Horror FX, Audio & BSOD Engine
 * Features 10 Unique Procedural Screamer Audios & 10 AI Jumpscare Photo Assets
 */

class HorrorFX {
  constructor(audioEngine) {
    this.audio = audioEngine || (window.MinigameAudio ? new MinigameAudio() : null);
    this.jumpscareCount = 10;
  }

  /**
   * 1. User Gesture Start Screen Gate
   */
  showStartScreen(gameTitle, gameDesc, onStart) {
    const overlay = document.createElement('div');
    overlay.id = 'start-gesture-overlay';
    overlay.className = 'gesture-start-overlay';
    overlay.innerHTML = `
      <div class="gesture-start-card">
        <div class="gesture-glitch-badge">SENTIENT SECURITY PROTOCOL</div>
        <h1 class="gesture-title">${gameTitle}</h1>
        <p class="gesture-desc">${gameDesc}</p>
        <div class="gesture-prompt">
          <span class="gesture-blink">▶ BAŞLAMAK İÇİN TIKLA VEYA BİR TUŞA BAS ◀</span>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const startHandler = () => {
      window.removeEventListener('keydown', startHandler);
      overlay.removeEventListener('click', startHandler);
      if (this.audio) this.audio.ensureContext();
      overlay.classList.add('fade-out');
      setTimeout(() => overlay.remove(), 250);
      if (onStart) onStart();
    };

    window.addEventListener('keydown', startHandler);
    overlay.addEventListener('click', startHandler);
  }

  /**
   * 2. Jumpscare Screamer (Random 1 of 10 Photos + Random 1 of 10 Audio Presets)
   */
  triggerJumpscare(customMsg = 'SENİ GÖRDÜM') {
    if (this.audio) {
      this.audio.ensureContext();
      this.playRandomScreamerAudio();
    }

    // Pick 1 of 10 jumpscare images
    const randImgIdx = Math.floor(Math.random() * this.jumpscareCount) + 1;
    const imgUrl = `../../images/jumpscare/jumpscare_${randImgIdx}.jpg`;

    const sc = document.createElement('div');
    sc.className = 'jumpscare-overlay';
    sc.innerHTML = `
      <div class="jumpscare-photo-container">
        <img src="${imgUrl}" alt="JUMPSCARE" class="jumpscare-real-img" onerror="this.src='../images/jumpscare/jumpscare_${randImgIdx}.jpg'" />
      </div>
      <div class="jumpscare-text">${customMsg}</div>
    `;

    document.body.appendChild(sc);

    // Violent screen shake
    document.body.classList.add('screen-violently-shaking');

    setTimeout(() => {
      sc.remove();
      document.body.classList.remove('screen-violently-shaking');
    }, 650);
  }

  /**
   * 10 Unique Procedural Web Audio Screamer SFX Presets
   */
  playRandomScreamerAudio() {
    if (!this.audio || !this.audio.ctx) return;
    const ctx = this.audio.ctx;
    const now = ctx.currentTime;
    const preset = Math.floor(Math.random() * 10) + 1;

    switch (preset) {
      case 1: { // High Frequency Saw Screech + Drop
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(1400, now);
        osc.frequency.exponentialRampToValueAtTime(180, now + 0.6);
        g.gain.setValueAtTime(0.4, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.6);
        this.addWhiteNoise(ctx, now, 0.4);
        break;
      }
      case 2: { // Explosive White Noise Burst with Resonant Bandpass
        this.addWhiteNoise(ctx, now, 0.6, 800, 5);
        break;
      }
      case 3: { // Distorted Guttural Cyber-Roar (Dual Detuned Saw)
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const g = ctx.createGain();
        osc1.type = 'sawtooth'; osc1.frequency.setValueAtTime(95, now);
        osc2.type = 'sawtooth'; osc2.frequency.setValueAtTime(102, now);
        g.gain.setValueAtTime(0.5, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
        osc1.connect(g); osc2.connect(g); g.connect(ctx.destination);
        osc1.start(now); osc2.start(now);
        osc1.stop(now + 0.65); osc2.stop(now + 0.65);
        break;
      }
      case 4: { // Piercing Feedback Shriek (High Resonance Sweep)
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(2200, now);
        osc.frequency.linearRampToValueAtTime(3200, now + 0.5);
        g.gain.setValueAtTime(0.35, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.5);
        break;
      }
      case 5: { // Glitched Stutter Siren (Rapid Square LFO)
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(660, now);
        for (let t = 0; t < 0.5; t += 0.05) {
          osc.frequency.setValueAtTime(t % 0.1 === 0 ? 880 : 440, now + t);
        }
        g.gain.setValueAtTime(0.35, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.55);
        break;
      }
      case 6: { // Deep Sub-Bass Demonic Impact + Shrill Peak
        const sub = ctx.createOscillator();
        const subG = ctx.createGain();
        sub.type = 'sine';
        sub.frequency.setValueAtTime(60, now);
        subG.gain.setValueAtTime(0.6, now);
        subG.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
        sub.connect(subG); subG.connect(ctx.destination);
        sub.start(now); sub.stop(now + 0.7);
        this.addWhiteNoise(ctx, now, 0.35, 2400);
        break;
      }
      case 7: { // Reverse Pitch-Bend Ghost Moan
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.exponentialRampToValueAtTime(1100, now + 0.45);
        osc.frequency.exponentialRampToValueAtTime(80, now + 0.6);
        g.gain.setValueAtTime(0.4, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.6);
        break;
      }
      case 8: { // Electric Shock Harsh Glitch Burst
        this.addWhiteNoise(ctx, now, 0.5, 3500, 8);
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(50, now);
        g.gain.setValueAtTime(0.4, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.5);
        break;
      }
      case 9: { // Dissonant Tritone Screech (440Hz + 622Hz)
        const o1 = ctx.createOscillator();
        const o2 = ctx.createOscillator();
        const g = ctx.createGain();
        o1.type = 'sawtooth'; o1.frequency.setValueAtTime(440, now);
        o2.type = 'sawtooth'; o2.frequency.setValueAtTime(622, now); // Diminished 5th (Devil's Chord)
        g.gain.setValueAtTime(0.35, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        o1.connect(g); o2.connect(g); g.connect(ctx.destination);
        o1.start(now); o2.start(now);
        o1.stop(now + 0.6); o2.stop(now + 0.6);
        break;
      }
      case 10: default: { // Triple Screamer Chaos Combo
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(140, now + 0.55);
        g.gain.setValueAtTime(0.4, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
        osc.connect(g); g.connect(ctx.destination);
        osc.start(now); osc.stop(now + 0.55);
        this.addWhiteNoise(ctx, now, 0.45, 1600, 4);
        break;
      }
    }
  }

  addWhiteNoise(ctx, now, duration = 0.4, freq = 1200, q = 3) {
    const bufferSize = ctx.sampleRate * duration;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const noiseFilter = ctx.createBiquadFilter();
    noiseFilter.type = 'bandpass';
    noiseFilter.frequency.setValueAtTime(freq, now);
    noiseFilter.Q.setValueAtTime(q, now);

    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.45, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    noise.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(ctx.destination);
    noise.start(now);
  }

  /**
   * 3. Authentic Windows 10/11 Fake BSOD
   */
  triggerFakeBSOD(onComplete) {
    const bsod = document.createElement('div');
    bsod.id = 'fake-bsod-screen';
    bsod.className = 'fake-bsod-overlay';
    bsod.innerHTML = `
      <div class="bsod-content">
        <div class="bsod-sadface">:(</div>
        <div class="bsod-title">Kişisel bilgisayarınız bir sorunla karşılaştı ve yeniden başlatılması gerekiyor.</div>
        <div class="bsod-subtitle">Şu anda bazı hata bilgileri toplanıyor, ardından otomatik olarak yeniden başlatılacak.</div>
        <div class="bsod-progress"><span id="bsod-pct">0</span>% tamamlandı</div>
        <div class="bsod-footer">
          <div class="bsod-qr-code"></div>
          <div class="bsod-details">
            <div>Bu sorun ve olası düzeltmeler hakkında daha fazla bilgi için şu adresi ziyaret edin: https://www.windows.com/stopcode</div>
            <div style="margin-top: 8px;">Bir destek görevlisini ararsanız şu bilgileri verin:</div>
            <div>Durdurma kodu: <strong>CRITICAL_PROCESS_DIED</strong></div>
            <div>Başarısız olan: <strong>SENTIENT_KERNEL_OVERRIDE.sys</strong></div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(bsod);

    let pct = 0;
    const interval = setInterval(() => {
      pct += Math.floor(Math.random() * 22) + 12;
      const el = document.getElementById('bsod-pct');
      if (el) el.textContent = Math.min(100, pct);

      if (pct >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          bsod.remove();
          if (onComplete) onComplete();
        }, 1200);
      }
    }, 450);
  }

  /**
   * 4. Total Blackout
   */
  triggerBlackout(durationMs = 2000, onComplete) {
    const blk = document.createElement('div');
    blk.className = 'total-blackout-overlay';
    document.body.appendChild(blk);

    setTimeout(() => {
      blk.remove();
      if (onComplete) onComplete();
    }, durationMs);
  }
}

window.HorrorFX = HorrorFX;
