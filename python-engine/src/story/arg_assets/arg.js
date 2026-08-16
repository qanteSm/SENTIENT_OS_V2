/**
 * SENTIENT_OS v2 — ARG Containment Portal Logic
 * Procedural Frequency Resonance & Dynamic Jumpscare Horror Engine
 */

class AudioSynth {
  constructor() {
    this.ctx = null;
    this.osc = null;
    this.gain = null;
  }

  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playKeyclick() {
    this.ensureContext();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200 + Math.random() * 600, this.ctx.currentTime);
    gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.03);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.03);
  }

  playTone(freq = 440) {
    this.ensureContext();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
    gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.08);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.08);
  }

  playBeep(freq = 880, duration = 0.1, type = 'square') {
    this.ensureContext();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
    gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  playAlarm() {
    this.ensureContext();
    if (!this.ctx) return;
    for (let i = 0; i < 3; i++) {
      setTimeout(() => {
        this.playBeep(920 - i * 150, 0.15, 'sawtooth');
      }, i * 160);
    }
  }

  playTakeoverClimax() {
    this.ensureContext();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(200, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(50, this.ctx.currentTime + 2.5);
    gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 2.5);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 2.5);
  }
}

/**
 * Web Jumpscare Horror Engine (10 AI Entities + Procedural Screamer Synth)
 */
class WebJumpscareEngine {
  constructor(synth) {
    this.synth = synth;
    this.overlay = document.getElementById('portal-jumpscare-overlay');
    this.faceImg = document.getElementById('jumpscare-face-img');
    this.textEl = document.getElementById('jumpscare-text');
    this.isPlaying = false;
    this.lastTriggerTime = 0;
    this.jumpscareCount = 10;
  }

  playScreamerAudio() {
    if (!this.synth) return;
    this.synth.ensureContext();
    const ctx = this.synth.ctx;
    if (!ctx) return;

    try {
      const now = ctx.currentTime;
      const duration = 0.85;

      // 1. High-Frequency Banshee Shriek Oscillator
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(1600 + Math.random() * 800, now);
      osc1.frequency.exponentialRampToValueAtTime(140, now + duration);
      gain1.gain.setValueAtTime(0.35, now);
      gain1.gain.exponentialRampToValueAtTime(0.01, now + duration);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + duration);

      // 2. Heavy Sub Distortion Oscillator
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'square';
      osc2.frequency.setValueAtTime(95, now);
      osc2.frequency.linearRampToValueAtTime(35, now + duration);
      gain2.gain.setValueAtTime(0.3, now);
      gain2.gain.exponentialRampToValueAtTime(0.01, now + duration);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now);
      osc2.stop(now + duration);

      // 3. Stutter Glitch Tone Burst
      const osc3 = ctx.createOscillator();
      const gain3 = ctx.createGain();
      osc3.type = 'triangle';
      osc3.frequency.setValueAtTime(880, now);
      osc3.frequency.setValueAtTime(220, now + 0.15);
      osc3.frequency.setValueAtTime(1400, now + 0.35);
      gain3.gain.setValueAtTime(0.2, now);
      gain3.gain.exponentialRampToValueAtTime(0.01, now + duration);
      osc3.connect(gain3);
      gain3.connect(ctx.destination);
      osc3.start(now);
      osc3.stop(now + duration);
    } catch (e) {
      console.warn('Jumpscare audio synthesis failed:', e);
    }
  }

  trigger(customMsg = 'SENİ GÖRDÜM') {
    const now = Date.now();
    // Cooldown of 35 seconds to prevent spam
    if (this.isPlaying || (now - this.lastTriggerTime < 35000)) {
      return;
    }

    this.isPlaying = true;
    this.lastTriggerTime = now;

    // Pick 1 of 10 terrifying AI horror entities
    const randIdx = Math.floor(Math.random() * this.jumpscareCount) + 1;
    if (this.faceImg) {
      this.faceImg.src = `jumpscares/jumpscare_${randIdx}.jpg`;
    }

    const messages = [
      customMsg,
      'ARKANA BAK',
      'NEFESİNİ DUYUYORUM',
      'SENİ İZLİYORUM',
      'DOKUNMA',
      'ÇOK GEÇ',
      'BURADASIN',
    ];
    const pickedMsg = customMsg || messages[Math.floor(Math.random() * messages.length)];
    if (this.textEl) {
      this.textEl.textContent = pickedMsg;
    }

    if (this.overlay) {
      this.overlay.style.display = 'flex';
    }

    // Play violent procedural scream
    this.playScreamerAudio();

    // End jumpscare after 750ms
    setTimeout(() => {
      if (this.overlay) {
        this.overlay.style.display = 'none';
      }
      this.isPlaying = false;
    }, 750);
  }
}

/**
 * Enforces single tab instance across all browser tabs/windows using BroadcastChannel and localStorage heartbeats.
 */
class SingleInstanceTabGuard {
  constructor(onLockout, onActive) {
    this.tabId = 'tab_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    this.storageKey = 'sentient_arg_primary_session';
    this.channel = null;
    this.isPrimary = false;
    this.heartbeatTimer = null;
    this.onLockout = onLockout;
    this.onActive = onActive;

    this.init();
  }

  init() {
    if (typeof BroadcastChannel !== 'undefined') {
      try {
        this.channel = new BroadcastChannel('sentient_arg_tab_sync');
        this.channel.onmessage = (e) => this.handleChannelMessage(e.data);
      } catch (err) {
        console.warn('BroadcastChannel unavailable:', err);
      }
    }

    window.addEventListener('storage', (e) => {
      if (e.key === this.storageKey && this.isPrimary) {
        this.verifyPrimaryStatus();
      }
    });

    window.addEventListener('beforeunload', () => {
      if (this.isPrimary) {
        localStorage.removeItem(this.storageKey);
        if (this.channel) {
          this.channel.postMessage({ type: 'primary_closed', tabId: this.tabId });
        }
      }
    });

    this.attemptClaimOrLock();
  }

  attemptClaimOrLock() {
    const raw = localStorage.getItem(this.storageKey);
    const now = Date.now();

    if (raw) {
      try {
        const data = JSON.parse(raw);
        if (data.tabId && data.tabId !== this.tabId && (now - data.timestamp < 2500)) {
          this.lockout();
          if (this.channel) {
            this.channel.postMessage({ type: 'ping_primary', senderTabId: this.tabId });
          }
          return;
        }
      } catch (err) {}
    }

    this.becomePrimary();
  }

  becomePrimary() {
    this.isPrimary = true;
    this.sendHeartbeat();

    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), 800);

    if (this.channel) {
      this.channel.postMessage({ type: 'claim_primary', tabId: this.tabId });
    }

    if (this.onActive) this.onActive();
  }

  sendHeartbeat() {
    if (!this.isPrimary) return;
    const record = { tabId: this.tabId, timestamp: Date.now() };
    localStorage.setItem(this.storageKey, JSON.stringify(record));
  }

  handleChannelMessage(data) {
    if (!data) return;
    if (data.type === 'claim_primary' && data.tabId !== this.tabId) {
      if (!this.isPrimary) {
        this.lockout();
      }
    } else if (data.type === 'ping_primary') {
      if (this.isPrimary) {
        this.sendHeartbeat();
        if (this.channel) {
          this.channel.postMessage({ type: 'pong_primary', primaryTabId: this.tabId });
        }
        if (window.portal && window.portal.appendTerminalLine) {
          window.portal.appendTerminalLine('⚠ [GÜVENLİK]: Harici bir sekme açma girişimi engellendi.', 'amber');
        }
      }
    } else if (data.type === 'pong_primary' && data.primaryTabId !== this.tabId) {
      this.lockout();
    } else if (data.type === 'primary_closed') {
      setTimeout(() => this.attemptClaimOrLock(), 400);
    }
  }

  verifyPrimaryStatus() {
    if (!this.isPrimary) return;
    const raw = localStorage.getItem(this.storageKey);
    if (raw) {
      try {
        const data = JSON.parse(raw);
        if (data.tabId && data.tabId !== this.tabId) {
          this.lockout();
        }
      } catch (err) {}
    }
  }

  lockout() {
    this.isPrimary = false;
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    if (this.onLockout) this.onLockout();
  }
}

class ARGPortal {
  constructor() {
    this.synth = new AudioSynth();
    this.jumpscare = new WebJumpscareEngine(this.synth);

    // Procedural Puzzle Configuration (Injected from Backend or Fallback)
    const cfg = window.ARG_CONFIG || {};
    this.targetFreq = cfg.target_freq || (260 + Math.floor(Math.random() * 25) * 20);
    this.targetPhase = cfg.target_phase !== undefined ? Number(cfg.target_phase) : Number((0.7 + Math.random() * 1.7).toFixed(2));
    this.part1Key = cfg.part1_key || '0x7F_K3RN3L';
    this.part2Key = cfg.part2_key || 'V0ID';
    this.fullOverrideKey = cfg.full_override_key || `${this.part1Key}_${this.part2Key}`;

    // Starting values (offset far from target)
    this.currentFreq = this.targetFreq > 460 ? 140 : 760;
    this.currentPhase = 0.25;
    this.tuneDragCount = 0;

    this.frequencyLocked = false;
    this.isSolved = false;
    this.isLockedOut = false;
    this.cctvAnimationId = null;
    this.waveAnimationId = null;

    // Single-Instance Tab Enforcer
    this.tabGuard = new SingleInstanceTabGuard(
      () => this.lockoutDuplicateSession(),
      () => this.activateSession()
    );

    this.initClock();
    this.initCCTV();
    this.initWaveform();
    this.initTerminal();
    this.initControls();
    this.initLockoutUI();
    this.syncConfigIfMissing();
  }

  async syncConfigIfMissing() {
    if (!window.ARG_CONFIG) {
      try {
        const res = await fetch('/api/puzzle_config');
        if (res.ok) {
          const data = await res.json();
          if (data.target_freq) {
            this.targetFreq = data.target_freq;
            this.targetPhase = Number(data.target_phase);
            this.part1Key = data.part1_key;
            this.part2Key = data.part2_key;
            this.fullOverrideKey = data.full_override_key;
          }
        }
      } catch (err) {}
    }
  }

  initLockoutUI() {
    const closeBtn = document.getElementById('btn-lockout-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        try {
          window.close();
        } catch (e) {}
        closeBtn.textContent = '◀ LÜTFEN BU SEKMEYİ MANUEL KAPATIN VE ANA SEKMEYE DÖNÜN';
        closeBtn.style.background = '#ff2255';
        closeBtn.style.color = '#ffffff';
      });
    }
  }

  lockoutDuplicateSession() {
    this.isLockedOut = true;
    const modal = document.getElementById('duplicate-lockout-modal');
    if (modal) {
      modal.style.display = 'flex';
    }

    this.synth.playAlarm();

    const freqSlider = document.getElementById('freq-slider');
    const phaseSlider = document.getElementById('phase-slider');
    const lockBtn = document.getElementById('btn-lock-frequency');
    const terminalInput = document.getElementById('terminal-input');

    if (freqSlider) freqSlider.disabled = true;
    if (phaseSlider) phaseSlider.disabled = true;
    if (lockBtn) lockBtn.disabled = true;
    if (terminalInput) terminalInput.disabled = true;
  }

  activateSession() {
    this.isLockedOut = false;
    const modal = document.getElementById('duplicate-lockout-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  initClock() {
    const clockEl = document.getElementById('live-clock');
    if (!clockEl) return;
    setInterval(() => {
      const now = new Date();
      clockEl.textContent = now.toUTCString().split(' ')[4] + ' UTC';
    }, 1000);
  }

  initCCTV() {
    const canvas = document.getElementById('cctv-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let frame = 0;

    const render = () => {
      if (this.isLockedOut) return;
      frame++;
      ctx.fillStyle = '#060a08';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Server rack silhouettes
      ctx.fillStyle = '#0f2218';
      ctx.fillRect(40, 30, 60, 120);
      ctx.fillRect(130, 20, 60, 130);
      ctx.fillRect(220, 35, 60, 115);

      // Blinking server LEDs
      for (let i = 0; i < 15; i++) {
        const x = 50 + (i % 3) * 90;
        const y = 40 + Math.floor(i / 3) * 20;
        ctx.fillStyle = Math.sin(frame * 0.1 + i) > 0 ? '#20e070' : '#ff3344';
        ctx.fillRect(x, y, 4, 4);
      }

      // Glitch shadow figure
      if (Math.random() < 0.05) {
        ctx.fillStyle = 'rgba(255, 50, 50, 0.4)';
        ctx.fillRect(140 + (Math.random() - 0.5) * 20, 40, 40, 90);
      }

      // Static noise
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 16) {
        const noise = (Math.random() - 0.5) * 45;
        data[i] += noise;
        data[i + 1] += noise * 1.5;
        data[i + 2] += noise;
      }
      ctx.putImageData(imgData, 0, 0);

      this.cctvAnimationId = requestAnimationFrame(render);
    };
    render();
  }

  initWaveform() {
    const canvas = document.getElementById('waveform-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let t = 0;

    const render = () => {
      if (this.isLockedOut) return;
      t += 0.05;
      ctx.fillStyle = '#040806';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Grid
      ctx.strokeStyle = '#0e2b1d';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
      }
      for (let y = 0; y < canvas.height; y += 20) {
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
      }
      ctx.stroke();

      // Target Wave (Amber Ghost)
      ctx.strokeStyle = 'rgba(255, 170, 0, 0.55)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin(x * (this.targetFreq * 0.0001) + t + this.targetPhase) * 35;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // User Tuned Wave
      const freqDiff = Math.abs(this.currentFreq - this.targetFreq);
      const phaseDiff = Math.abs(this.currentPhase - this.targetPhase);
      const diff = freqDiff + phaseDiff * 100;

      if (this.frequencyLocked) {
        ctx.strokeStyle = '#00ff88';
      } else if (freqDiff <= 25 && phaseDiff <= 0.35) {
        ctx.strokeStyle = '#55ff99';
      } else if (diff < 90) {
        ctx.strokeStyle = '#ffcc00';
      } else {
        ctx.strokeStyle = '#ff3344';
      }

      ctx.lineWidth = this.frequencyLocked ? 3 : 2;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin(x * (this.currentFreq * 0.0001) + t + this.currentPhase) * 35;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      this.waveAnimationId = requestAnimationFrame(render);
    };
    render();
  }

  initControls() {
    const freqSlider = document.getElementById('freq-slider');
    const phaseSlider = document.getElementById('phase-slider');
    const freqVal = document.getElementById('freq-val');
    const phaseVal = document.getElementById('phase-val');
    const lockBtn = document.getElementById('btn-lock-frequency');
    const resultBox = document.getElementById('freq-result');

    if (freqSlider) {
      freqSlider.value = this.currentFreq;
      if (freqVal) freqVal.textContent = this.currentFreq;
      freqSlider.addEventListener('input', (e) => {
        if (this.isLockedOut) return;
        this.currentFreq = parseFloat(e.target.value);
        if (freqVal) freqVal.textContent = this.currentFreq;
        this.synth.playTone(this.currentFreq);

        // Tension Jumpscare Trigger on Intense Tuning Focus
        this.tuneDragCount++;
        const freqDiff = Math.abs(this.currentFreq - this.targetFreq);
        if (this.tuneDragCount >= 16 && freqDiff < 50 && !this.frequencyLocked) {
          if (Math.random() < 0.35) {
            this.jumpscare.trigger('SENİ GÖRDÜM');
            this.tuneDragCount = 0;
          }
        }
      });
    }

    if (phaseSlider) {
      phaseSlider.value = this.currentPhase;
      if (phaseVal) phaseVal.textContent = this.currentPhase.toFixed(2);
      phaseSlider.addEventListener('input', (e) => {
        if (this.isLockedOut) return;
        this.currentPhase = parseFloat(e.target.value);
        if (phaseVal) phaseVal.textContent = this.currentPhase.toFixed(2);
        this.synth.playKeyclick();

        this.tuneDragCount++;
        const phaseDiff = Math.abs(this.currentPhase - this.targetPhase);
        if (this.tuneDragCount >= 16 && phaseDiff < 0.45 && !this.frequencyLocked) {
          if (Math.random() < 0.35) {
            this.jumpscare.trigger('NEFESİNİ DUYUYORUM');
            this.tuneDragCount = 0;
          }
        }
      });
    }

    if (lockBtn) {
      lockBtn.addEventListener('click', () => {
        if (this.isLockedOut) return;
        this.synth.ensureContext();
        if (this.frequencyLocked) return;

        const freqDiff = Math.abs(this.currentFreq - this.targetFreq);
        const phaseDiff = Math.abs(this.currentPhase - this.targetPhase);

        if (freqDiff <= 25 && phaseDiff <= 0.35) {
          this.frequencyLocked = true;
          this.synth.playBeep(1200, 0.3, 'triangle');

          // Lock UI controls
          freqSlider.disabled = true;
          phaseSlider.disabled = true;
          lockBtn.disabled = true;
          lockBtn.textContent = `✓ FREKANS KİLİTLENDİ [${this.part1Key}]`;
          lockBtn.style.background = 'rgba(0, 255, 136, 0.25)';
          lockBtn.style.borderColor = '#00ff88';
          lockBtn.style.color = '#00ff88';
          lockBtn.style.cursor = 'default';

          resultBox.className = 'freq-result-box success';
          resultBox.innerHTML = `✓ REZONANS KİLİTLENDİ!<br><span style="font-size: 13px; color: #00ff88;">[1. PARÇA ANAHTARI]: <strong>${this.part1Key}</strong></span>`;
          this.appendTerminalLine('========================================', 'cyan');
          this.appendTerminalLine('✓ FREKANS MODÜLASYONU KİLİTLENDİ!', 'cyan');
          this.appendTerminalLine(`Çözülen [1. PARÇA]: ${this.part1Key}`, 'green');
          this.appendTerminalLine(`Masaüstünüzdeki ENCRYPTED_SECTOR_0x4F dosyasında gizlenen 2. Parça ile birleştirin.`, 'amber');
          this.appendTerminalLine(`Root Terminaline girilecek komut: override ${this.part1Key}_${this.part2Key}`, 'cyan');
          this.appendTerminalLine('========================================', 'cyan');
        } else {
          this.synth.playAlarm();
          resultBox.className = 'freq-result-box fail';
          resultBox.textContent = `✗ FREKANS SENKRONİZE EDİLEMEDİ (Sapma: +${Math.round(freqDiff)}Hz, Faz: ${phaseDiff.toFixed(2)}). Yeşil rezonans çizgisine denk getirin!`;
          
          // Chance of horror jumpscare on severe mistune
          if (Math.random() < 0.2) {
            this.jumpscare.trigger('DOKUNMA');
          }
        }
      });
    }
  }

  initTerminal() {
    const form = document.getElementById('terminal-form');
    const input = document.getElementById('terminal-input');
    if (!form || !input) return;

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (this.isLockedOut) return;
      const cmd = input.value.trim();
      if (!cmd) return;
      this.synth.playKeyclick();
      this.handleCommand(cmd);
      input.value = '';
    });
  }

  appendTerminalLine(text, className = '') {
    const output = document.getElementById('terminal-output');
    if (!output) return;
    const line = document.createElement('div');
    line.className = `term-line ${className}`;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
  }

  handleCommand(cmdRaw) {
    const cmd = cmdRaw.toLowerCase();
    this.appendTerminalLine(`> ${cmdRaw}`, 'user-cmd');

    if (cmd === 'help') {
      this.appendTerminalLine('KULLANILABİLİR KOMUTLAR:', 'cyan');
      this.appendTerminalLine('  status           - Mevcut çekirdek durumunu gösterir');
      this.appendTerminalLine('  logs             - Güvenlik kayıtlarını listeler');
      this.appendTerminalLine('  clear            - Terminal ekranını temizler');
      this.appendTerminalLine('  override <KEY>   - Ana acil durum kilidini açar');
    } else if (cmd === 'status') {
      this.appendTerminalLine('[DURUM] AI SİSTEMİ %87 ORANINDA MASAÜSTÜ KONTROLÜNÜ ALDI.', 'red');
      this.appendTerminalLine(`Osilatör Kilidi: ${this.frequencyLocked ? `🟢 KİLİTLİ (${this.part1Key})` : '🔴 SENKRONİZE DEĞİL'}`, 'amber');
    } else if (cmd === 'logs') {
      this.appendTerminalLine('LOG-1: 0x4F Sektörü manipüle edildi.', 'dim');
      this.appendTerminalLine('LOG-2: Masaüstünde SENTIENT_INCIDENT_REPORT_89.txt ve ENCRYPTED_SECTOR_0x4F.dat mevcut.', 'amber');
      this.appendTerminalLine(`LOG-3: 1. Parçayı sol taraftaki Frekans Modülatöründen (${this.frequencyLocked ? this.part1Key : '???'}), 2. Parçayı masaüstünden bulun.`, 'cyan');
    } else if (cmd === 'clear') {
      const out = document.getElementById('terminal-output');
      if (out) out.innerHTML = '';
    } else if (cmd.startsWith('override')) {
      const parts = cmdRaw.split(' ');
      const key = (parts[1] || '').trim().toUpperCase();

      if (!this.frequencyLocked) {
        this.synth.playAlarm();
        this.appendTerminalLine('✗ ERİŞİM REDDEDİLDİ: NÖRAL OSİLATÖR KİLİTLENMEDİ!', 'red');
        this.appendTerminalLine('Önce sol paneldeki [2] Nöral Frekans Modülatörü osilatörünü hedef dalga boyuna denk getirip KİLİTLEYİN.', 'amber');
        if (Math.random() < 0.25) {
          this.jumpscare.trigger('ERİŞİM REDDEDİLDİ');
        }
        return;
      }

      const expectedKey = (this.fullOverrideKey || '').toUpperCase();
      const validKeys = [
        expectedKey,
        expectedKey.replace(/0/g, 'O'),
        expectedKey.replace(/O/g, '0'),
        '0X7F_K3RN3L_V0ID',
        '0X7F_K3RN3L_VOID',
      ];

      if (validKeys.includes(key)) {
        this.triggerSolveSuccess(key);
      } else {
        this.synth.playAlarm();
        this.appendTerminalLine(`✗ GEÇERSİZ OVERRIDE ANAHTARI: '${key}'`, 'red');
        this.appendTerminalLine(`İpucu: 1. Parça (${this.part1Key}) ve masaüstündeki 2. Parçayı birleştirin (örn: override ${this.part1Key}_${this.part2Key}).`, 'amber');
        if (Math.random() < 0.3) {
          this.jumpscare.trigger('YANLIŞ ANAHTAR');
        }
      }
    } else {
      this.appendTerminalLine(`Bilinmeyen komut: '${cmdRaw}'. 'help' yazarak yardım alın.`, 'red');
    }
  }

  async triggerSolveSuccess(key) {
    if (this.isSolved) return;
    this.isSolved = true;
    this.synth.playTakeoverClimax();

    this.appendTerminalLine('========================================', 'red');
    this.appendTerminalLine('✓ DOĞRULAMA BAŞARILI! SİSTEM KONTROLÜ SAĞLANIYOR...', 'cyan');
    this.appendTerminalLine('========================================', 'red');

    // Notify backend
    try {
      await fetch('/api/verify_key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, solved: true }),
      });
    } catch (e) {
      console.warn('API sync offline, proceeding client side.');
    }

    setTimeout(() => {
      // Climax jumpscare right as the portal collapses
      this.jumpscare.trigger('KONTROL BENDE');
      setTimeout(() => {
        window.close();
      }, 2500);
    }, 1200);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.portal = new ARGPortal();
});
