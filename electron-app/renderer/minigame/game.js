/**
 * SENTIENT_OS v2 — Mini Game Controller (Final B Battle)
 */

class VirusDefenseGame {
  constructor() {
    this.timeLeft = 60;
    this.score = 0;
    this.targetScore = 10;
    this.active = true;

    this.timerEl = document.getElementById('timer-val');
    this.scoreEl = document.getElementById('score-val');
    this.barEl = document.getElementById('defense-bar');
    this.arena = document.getElementById('game-field');
    this.modal = document.getElementById('game-over-modal');
    this.modalTitle = document.getElementById('modal-title');
    this.modalDesc = document.getElementById('modal-desc');

    this.spawnTimer = null;
    this.gameLoopTimer = null;

    this.init();
  }

  init() {
    this.updateHUD();

    // 1-second countdown clock
    this.gameLoopTimer = setInterval(() => {
      if (!this.active) return;
      this.timeLeft--;
      this.timerEl.textContent = `${this.timeLeft}s`;

      if (this.timeLeft <= 0) {
        this.endGame(this.score >= this.targetScore);
      }
    }, 1000);

    // Initial spawn
    this.scheduleNextSpawn();
  }

  scheduleNextSpawn() {
    if (!this.active) return;

    // Difficulty curve: as time decreases, spawn rate increases
    const delay = Math.max(600, 2500 - (60 - this.timeLeft) * 35);

    this.spawnTimer = setTimeout(() => {
      this.spawnErrorWindow();
      this.scheduleNextSpawn();
    }, delay);
  }

  spawnErrorWindow() {
    if (!this.active) return;

    const errorTitles = [
      'CRITICAL SYSTEM EXCEPTION',
      'SENTIENT_CORE_ACCESS_VIOLATION',
      'KERNEL_SECURITY_CHECK_FAILURE',
      'MEMORY_CORRUPTION_DETECTED',
      'UNAUTHORIZED_AI_OVERRIDE',
    ];

    const title = errorTitles[Math.floor(Math.random() * errorTitles.length)];
    const popup = document.createElement('div');
    popup.className = 'error-popup';

    const maxX = window.innerWidth - 360;
    const maxY = window.innerHeight - 200;
    const posX = Math.max(20, Math.floor(Math.random() * maxX));
    const posY = Math.max(70, Math.floor(Math.random() * maxY));

    popup.style.left = `${posX}px`;
    popup.style.top = `${posY}px`;

    popup.innerHTML = `
      <div class="error-titlebar">
        <span>${title}</span>
        <div class="error-close-btn">✕</div>
      </div>
      <div class="error-body">
        <span class="error-icon">❌</span>
        <span>Bu işlem durdurulamıyor. Sistem kararsız durumda!</span>
      </div>
      <div class="error-btn-bar">
        <button class="error-ok-btn">Kapat</button>
      </div>
    `;

    const closeHandler = () => {
      popup.remove();
      this.score++;
      this.updateHUD();

      if (this.score >= this.targetScore) {
        this.endGame(true);
      }
    };

    popup.querySelector('.error-close-btn').addEventListener('click', closeHandler);
    popup.querySelector('.error-ok-btn').addEventListener('click', closeHandler);

    this.arena.appendChild(popup);
  }

  updateHUD() {
    this.scoreEl.textContent = `${this.score}/${this.targetScore}`;
    const percent = Math.min(100, (this.score / this.targetScore) * 100);
    this.barEl.style.width = `${percent}%`;
  }

  endGame(success) {
    this.active = false;
    clearInterval(this.gameLoopTimer);
    clearTimeout(this.spawnTimer);

    this.arena.innerHTML = '';
    this.modal.style.display = 'flex';

    if (success) {
      this.modalTitle.textContent = 'SİSTEM KORUNDU';
      this.modalTitle.style.color = '#00ff88';
      this.modalDesc.textContent = 'Virüs saldırısı başarıyla püskürtüldü!';
    } else {
      this.modalTitle.textContent = 'KONTROL KAYBEDİLDİ';
      this.modalTitle.style.color = '#ff3333';
      this.modalDesc.textContent = 'Sistem kararsız hale geldi. SENTIENT kontrolü ele geçirdi.';
    }

    if (window.sentientAPI && window.sentientAPI.sendEvent) {
      window.sentientAPI.sendEvent('minigame-result', {
        success,
        score: this.score,
        time_left: this.timeLeft,
      });
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.game = new VirusDefenseGame();
});
