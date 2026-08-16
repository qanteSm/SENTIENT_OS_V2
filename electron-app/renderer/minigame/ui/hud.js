/**
 * SENTIENT_OS v2 — Minigame HUD & UI Controller
 */

class GameHUD {
  constructor() {
    this.timerEl = document.getElementById('timer-val');
    this.bossHpBar = document.getElementById('boss-hp-bar');
    this.bossHpText = document.getElementById('boss-hp-text');
    this.bossTitle = document.getElementById('boss-title');
    this.heartsEl = document.getElementById('player-hearts');
    this.energyBar = document.getElementById('player-energy-bar');
    this.statusEl = document.getElementById('hud-system-status');
    this.modal = document.getElementById('game-over-modal');
    this.modalTitle = document.getElementById('modal-title');
    this.modalDesc = document.getElementById('modal-desc');
    this.modalStats = document.getElementById('modal-stats');
    this.modalBtn = document.getElementById('modal-continue-btn');
  }

  update(boss, player, timeLeft, score) {
    if (boss && this.bossHpBar) {
      const hpPercent = Math.max(0, (boss.hp / boss.maxHp) * 100);
      this.bossHpBar.style.width = `${hpPercent}%`;
      this.bossHpText.textContent = `${Math.ceil(hpPercent)}%`;

      if (boss.phase === 3) {
        this.statusEl.textContent = 'FAZ 3: KERNEL MELTDOWN (ÖFKE TAVAN!)';
        this.statusEl.className = 'hud-val danger';
        this.bossTitle.textContent = 'SENTIENT // CATACLYSM DEMON [MELTDOWN]';
        this.bossHpBar.style.background = 'linear-gradient(90deg, #ff0033, #ff5500)';
        this.bossHpBar.style.boxShadow = '0 0 16px #ff0033';
      } else if (boss.phase === 2) {
        this.statusEl.textContent = 'FAZ 2: CORRUPTED BEAST (BOYNUZLAR UYANDI)';
        this.statusEl.className = 'hud-val warning';
        this.bossTitle.textContent = 'SENTIENT // CORRUPTED BEAST';
        this.bossHpBar.style.background = 'linear-gradient(90deg, #9900ff, #ffaa00)';
        this.bossHpBar.style.boxShadow = '0 0 14px #aa00ff';
      } else {
        this.statusEl.textContent = 'FAZ 1: LATENT CORE (SÜZÜLEN ÇEKİRDEK)';
        this.statusEl.className = 'hud-val normal';
        this.bossTitle.textContent = 'SENTIENT // LATENT CORE';
        this.bossHpBar.style.background = 'linear-gradient(90deg, #00ffff, #0088ff)';
        this.bossHpBar.style.boxShadow = '0 0 12px #00ffff';
      }
    }

    if (player && this.energyBar) {
      const energyPercent = (player.energy / player.maxEnergy) * 100;
      this.energyBar.style.width = `${energyPercent}%`;

      let hearts = '';
      for (let i = 0; i < player.hp; i++) hearts += '❤';
      this.heartsEl.textContent = hearts || '💀';
    }

    if (this.timerEl) {
      this.timerEl.textContent = `${timeLeft}s`;
    }
  }

  showEndModal(success, message, score, timeLeft, playerHp, onContinue) {
    if (!this.modal) return;

    if (success) {
      this.modalTitle.textContent = 'SİSTEM KORUNDU // ÇEKİRDEK TEMİZLENDİ';
      this.modalTitle.style.color = '#00ff88';
      this.modalDesc.textContent = message || 'SENTIENT Dark Sovereign avatarı başarıyla yok edildi!';
    } else {
      this.modalTitle.textContent = 'KONTROL KAYBEDİLDİ // KERNEL OVERWRITE';
      this.modalTitle.style.color = '#ff2244';
      this.modalDesc.textContent = message || 'SENTIENT bilincinizi absorbe etti ve sistemi kilitledi.';
    }

    this.modalStats.innerHTML = `
      <div class="stat-row"><span>KAZANILAN SKOR:</span> <strong>${score} PTS</strong></div>
      <div class="stat-row"><span>KALAN SÜRE:</span> <strong>${timeLeft}s</strong></div>
      <div class="stat-row"><span>KALAN CAN:</span> <strong>${playerHp}/3</strong></div>
    `;

    this.modal.style.display = 'flex';

    if (this.modalBtn && onContinue) {
      this.modalBtn.onclick = onContinue;
    }
  }
}

window.GameHUD = GameHUD;
