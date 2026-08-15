/**
 * SENTIENT_OS v2 — Realistic Fake BSOD Effect Module
 */

class FakeBSODEffect {
  constructor() {
    this.container = document.getElementById('bsod-container');
    this.timeout = null;
    this.active = false;

    window.addEventListener('keydown', (e) => {
      if (this.active && e.key === 'Escape') {
        this.hide();
      }
    });
  }

  trigger(params = {}) {
    const errorCode = params.error_code || 'CRITICAL_PROCESS_DIED';
    const durationMs = Math.min(10000, params.duration_ms || 6000);

    if (!this.container) return;

    this.active = true;
    this.container.innerHTML = `
      <div class="bsod-wrapper">
        <div class="bsod-face">:(</div>
        <div class="bsod-title">Your device ran into a problem and needs to restart. We're just collecting some error info, and then we'll restart for you.</div>
        <div class="bsod-progress"><span id="bsod-percent">0</span>% complete</div>
        <div class="bsod-details">
          <div class="bsod-qr-placeholder"></div>
          <div class="bsod-text">
            <div>For more information about this issue and possible fixes, visit https://windows.com/stopcode</div>
            <div class="bsod-code">Stop code: ${errorCode}</div>
            <div class="bsod-hint">(Press ESC to recover)</div>
          </div>
        </div>
      </div>
    `;

    this.container.style.display = 'block';

    // Simulate counter progress
    let percent = 0;
    const interval = setInterval(() => {
      if (!this.active) {
        clearInterval(interval);
        return;
      }
      percent += Math.floor(Math.random() * 20) + 10;
      if (percent > 100) percent = 100;
      const el = document.getElementById('bsod-percent');
      if (el) el.textContent = percent.toString();
      if (percent >= 100) clearInterval(interval);
    }, durationMs / 6);

    this.timeout = setTimeout(() => {
      this.hide();
    }, durationMs);
  }

  hide() {
    this.active = false;
    if (this.timeout) clearTimeout(this.timeout);
    if (this.container) {
      this.container.style.display = 'none';
      this.container.innerHTML = '';
    }
  }
}

window.FakeBSODEffect = FakeBSODEffect;
