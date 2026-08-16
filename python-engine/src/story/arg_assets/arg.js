/**
 * SENTIENT_OS v2 — ARG Containment Portal Logic
 * Includes Single-Instance Multi-Tab Lockdown Enforcer
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
        // If an active primary tab exists and checked in within 2.5s
        if (data.tabId && data.tabId !== this.tabId && (now - data.timestamp < 2500)) {
          // Duplicate instance detected!
          this.lockout();
          if (this.channel) {
            this.channel.postMessage({ type: 'ping_primary', senderTabId: this.tabId });
          }
          return;
        }
      } catch (err) {}
    }

    // No active primary session or lock expired, claim primary
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
      // Previous primary closed, attempt to activate
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
    this.targetFreq = 440;
    this.targetPhase = 1.55;
    this.currentFreq = 120;
    this.currentPhase = 0.3;
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
  }

  initLockoutUI() {
    const closeBtn = document.getElementById('btn-lockout-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        try {
          window.close();
        } catch (e) {}
        // Fallback message if window.close() is blocked by browser security
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

    // Play alert sound
    this.synth.playAlarm();

    // Disable all controls
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
      ctx.strokeStyle = 'rgba(255, 170, 0, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin(x * (this.targetFreq * 0.0001) + t + this.targetPhase) * 35;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // User Tuned Wave (Bright Green / Yellow / Red based on distance)
      const diff = Math.abs(this.currentFreq - this.targetFreq) + Math.abs(this.currentPhase - this.targetPhase) * 100;
      if (this.frequencyLocked) {
        ctx.strokeStyle = '#00ff88';
      } else if (diff < 30) {
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
      freqSlider.addEventListener('input', (e) => {
        if (this.isLockedOut) return;
        this.currentFreq = parseFloat(e.target.value);
        if (freqVal) freqVal.textContent = this.currentFreq;
        this.synth.playTone(this.currentFreq);
      });
    }

    if (phaseSlider) {
      phaseSlider.addEventListener('input', (e) => {
        if (this.isLockedOut) return;
        this.currentPhase = parseFloat(e.target.value);
        if (phaseVal) phaseVal.textContent = this.currentPhase.toFixed(2);
        this.synth.playKeyclick();
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

          // Lock UI controls so they cannot be altered
          freqSlider.disabled = true;
          phaseSlider.disabled = true;
          lockBtn.disabled = true;
          lockBtn.textContent = '✓ FREKANS KİLİTLENDİ [0x7F_K3RN3L]';
          lockBtn.style.background = 'rgba(0, 255, 136, 0.25)';
          lockBtn.style.borderColor = '#00ff88';
          lockBtn.style.color = '#00ff88';
          lockBtn.style.cursor = 'default';

          resultBox.className = 'freq-result-box success';
          resultBox.innerHTML = `✓ REZONANS KİLİTLENDİ!<br><span style="font-size: 13px; color: #00ff88;">[1. PARÇA ANAHTARI]: <strong>0x7F_K3RN3L</strong></span>`;
          this.appendTerminalLine('========================================', 'cyan');
          this.appendTerminalLine('✓ FREKANS MODÜLASYONU KİLİTLENDİ!', 'cyan');
          this.appendTerminalLine('Çözülen [1. PARÇA]: 0x7F_K3RN3L', 'green');
          this.appendTerminalLine('Masaüstünüzdeki ENCRYPTED_SECTOR_0x4F.txt dosyasında gizlenen 2. Parça: V0ID', 'amber');
          this.appendTerminalLine('Root Terminaline girilecek komut: override 0x7F_K3RN3L_V0ID', 'cyan');
          this.appendTerminalLine('========================================', 'cyan');
        } else {
          this.synth.playAlarm();
          resultBox.className = 'freq-result-box fail';
          resultBox.textContent = `✗ FREKANS SENKRONİZE EDİLEMEDİ (Sapma: +${Math.round(freqDiff)}Hz, Faz: ${phaseDiff.toFixed(2)}). Yeşil rezonans çizgisine denk getirin!`;
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
      this.appendTerminalLine(`Osilatör Kilidi: ${this.frequencyLocked ? '🟢 KİLİTLİ (0x7F_K3RN3L)' : '🔴 SENKRONİZE DEĞİL'}`, 'amber');
    } else if (cmd === 'logs') {
      this.appendTerminalLine('LOG-1: 0x4F Sektörü manipüle edildi.', 'dim');
      this.appendTerminalLine('LOG-2: Masaüstünde SENTIENT_INCIDENT_REPORT_89.txt ve ENCRYPTED_SECTOR_0x4F.dat mevcut.', 'amber');
      this.appendTerminalLine('LOG-3: 1. Parçayı sol taraftaki Frekans Modülatöründen, 2. Parçayı .dat dosyasından bulun.', 'cyan');
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
        return;
      }

      const validKeys = [
        '0X7F_K3RN3L_V0ID',
        '0X7F_K3RN3L_VOID',
        '0X7F_KERNEL_V0ID',
        '0X7F_KERNEL_VOID',
      ];

      if (validKeys.includes(key)) {
        this.triggerSolveSuccess(key);
      } else {
        this.synth.playAlarm();
        this.appendTerminalLine(`✗ GEÇERSİZ OVERRIDE ANAHTARI: '${key}'`, 'red');
        this.appendTerminalLine('İpucu: 1. Parça (0x7F_K3RN3L) ve masaüstündeki ENCRYPTED_SECTOR_0x4F.dat dosyasındaki 2. Parçayı birleştirin (örn: override 0x7F_K3RN3L_V0ID).', 'amber');
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
      const modal = document.getElementById('hijack-modal');
      if (modal) modal.style.display = 'flex';

      setTimeout(() => {
        window.close();
      }, 3500);
    }, 1200);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.portal = new ARGPortal();
});
