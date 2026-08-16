/**
 * SENTIENT_OS v2 — Arcade Hub Controller
 */

const MINIGAMES_DATA = [
  // --- EASY TIER (4 Games) ---
  {
    id: 'game1',
    number: '01',
    tier: 'easy',
    title: 'MEMORY SECTOR MATRIX',
    desc: '4x4 bozuk RAM karolarını sırayla hatırla. Hata yaparsan karanlık fısıltılar başlar.',
    mechanic: 'Simon Says / Hafıza',
    file: 'games/game1_memory.html',
    badge: 'KOLAY',
    badgeClass: 'badge-easy',
  },
  {
    id: 'game2',
    number: '02',
    tier: 'easy',
    title: 'MALWARE FILE SLICER',
    desc: 'Ekranda düşen virüslü .exe dosyalarını çöp kutusuna ulaşmadan tıkla/doğra. SENI_GORDUM dosyasına dikkat!',
    mechanic: 'Hızlı Tıklama / Refleks',
    file: 'games/game2_slicer.html',
    badge: 'KOLAY',
    badgeClass: 'badge-easy',
  },
  {
    id: 'game3',
    number: '03',
    tier: 'easy',
    title: 'NEURAL WIRE CONNECT',
    desc: '15 saniyede 4 renkli kıvılcımlı nöral kabloyu doğru soketlere bağla. Yanlış kablo elektrik şoku verir.',
    mechanic: 'Sürükle-Bırak / Devre',
    file: 'games/game3_wires.html',
    badge: 'KOLAY',
    badgeClass: 'badge-easy',
  },
  {
    id: 'game4',
    number: '04',
    tier: 'easy',
    title: 'SONAR RADAR SWEEP',
    desc: 'Karanlık radar ekranında dönen yeşil ışıkla beliren karanlık anomalileri merkeze varmadan yakala.',
    mechanic: 'Radar / Zamanlama',
    file: 'games/game4_radar.html',
    badge: 'KOLAY',
    badgeClass: 'badge-easy',
  },

  // --- MEDIUM TIER (3 Games) ---
  {
    id: 'game5',
    number: '05',
    tier: 'medium',
    title: 'CIPHER WHEEL CRYPT',
    desc: '3 katmanlı kriptografik çarkı ses frekansıyla eşle. Ters ses kayıtları ve şifreli rünleri çöz.',
    mechanic: 'Çark Eşleme / Ses',
    file: 'games/game5_cipher.html',
    badge: 'ORTA',
    badgeClass: 'badge-medium',
  },
  {
    id: 'game6',
    number: '06',
    tier: 'medium',
    title: 'CCTV PARANORMAL ROOM',
    desc: '6 güvenlik kamerasını tara, hareket eden gölgeleri ve anomalileri varlık güvenlik odasına girmeden bul.',
    mechanic: 'Gözetleme / Anomali',
    file: 'games/game6_cctv.html',
    badge: 'ORTA',
    badgeClass: 'badge-medium',
  },
  {
    id: 'game7',
    number: '07',
    tier: 'medium',
    title: 'HEX MATRIX BREACH',
    desc: '6x6 hex bellek bloğundan satır-sütun sıralamasıyla 4 haneli şifreyi çıkar. Süre biterse BSOD patlar.',
    mechanic: 'Cyberpunk Hex Hack',
    file: 'games/game7_hex.html',
    badge: 'ORTA',
    badgeClass: 'badge-medium',
  },

  // --- HARDCORE TIER (3 Games) ---
  {
    id: 'game8',
    number: '08',
    tier: 'hardcore',
    title: '2.5D RAYCASTER LABYRINTH',
    desc: 'Wolfenstein tarzı 3D karanlık labirent! El feneriyle 3 kök anahtarı topla, Stalker yaratığa yakalanma.',
    mechanic: '3D Raycaster / Kaçış',
    file: 'games/game8_maze.html',
    badge: 'HARDCORE',
    badgeClass: 'badge-hardcore',
  },
  {
    id: 'game9',
    number: '09',
    tier: 'hardcore',
    title: 'CORE OVERHEAT CRISIS',
    desc: '4 göstergeli nükleer reaktör valf, basınç ve soğutucu dengeleme paneli. Patlamayı 45 saniye durdur.',
    mechanic: 'Simülatör / Denge',
    file: 'games/game9_reactor.html',
    badge: 'HARDCORE',
    badgeClass: 'badge-hardcore',
  },
  {
    id: 'game10',
    number: '10',
    tier: 'hardcore',
    title: 'PSYCHOLOGICAL TRIAL & BSOD',
    desc: 'AI sorgusu, hızlı mors kodları ve Windows Görev Çubuğunu tamamen kapatan sahte Mavi Ekran (BSOD)!',
    mechanic: 'Mors / Sorgu / BSOD',
    file: 'games/game10_trial.html',
    badge: 'HARDCORE',
    badgeClass: 'badge-hardcore',
  },

  // --- BOSS FIGHTS (2 Games) ---
  {
    id: 'boss1',
    number: 'Ω1',
    tier: 'boss',
    title: 'SENTIENT CORE OMEGA (BOSS)',
    desc: '3 aşamalı dönüşen karanlık AI iblisi ile 2D serbest nişan almalı aksiyon platformer savaşı.',
    mechanic: '2D Platformer / Boss',
    file: 'index.html',
    badge: 'BOSS BATTLE',
    badgeClass: 'badge-boss',
  },
  {
    id: 'boss2',
    number: 'Ω2',
    tier: 'boss',
    title: 'POPUP VIRUS DEFENSE',
    desc: 'Ekrana art arda patlayan sahte retro Windows hata ve virüs pencerelerini hızla kapat.',
    mechanic: 'Refleks / Popup',
    file: 'popup_game.html',
    badge: 'VIRUS DEFENSE',
    badgeClass: 'badge-boss',
  },
];

class ArcadeHub {
  constructor() {
    this.grid = document.getElementById('games-grid');
    this.filterBtns = document.querySelectorAll('.filter-btn');
    this.audio = new MinigameAudio();
    this.currentFilter = 'all';

    this.init();
  }

  init() {
    this.renderCards();
    this.setupFilters();
  }

  renderCards() {
    this.grid.innerHTML = '';

    const filtered =
      this.currentFilter === 'all'
        ? MINIGAMES_DATA
        : MINIGAMES_DATA.filter((g) => g.tier === this.currentFilter);

    filtered.forEach((game) => {
      const card = document.createElement('div');
      card.className = `game-card ${game.tier}`;
      card.innerHTML = `
        <div class="card-top">
          <span class="card-num">#${game.number}</span>
          <span class="card-badge ${game.badgeClass}">${game.badge}</span>
        </div>
        <h2 class="card-title">${game.title}</h2>
        <p class="card-desc">${game.desc}</p>
        <div class="card-footer">
          <span class="card-mechanic">${game.mechanic}</span>
          <button class="play-btn" data-file="${game.file}">BAŞLAT ▶</button>
        </div>
      `;

      card.addEventListener('mouseenter', () => {
        if (this.audio && this.audio.ctx) {
          this.audio.playTone(440, 0.05, 'triangle', 0.03);
        }
      });

      card.querySelector('.play-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        this.launchGame(game.file);
      });

      card.addEventListener('click', () => {
        this.launchGame(game.file);
      });

      this.grid.appendChild(card);
    });
  }

  setupFilters() {
    this.filterBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        this.filterBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentFilter = btn.dataset.filter;
        if (this.audio && this.audio.ctx) {
          this.audio.playTone(660, 0.08, 'sine', 0.05);
        }
        this.renderCards();
      });
    });
  }

  launchGame(filePath) {
    if (this.audio && this.audio.ctx) {
      this.audio.playTone(880, 0.15, 'sawtooth', 0.1);
    }
    console.log(`[HUB] Launching ${filePath}`);
    if (window.sentientAPI && window.sentientAPI.sendEvent) {
      window.sentientAPI.sendEvent('launch-minigame', filePath);
    } else {
      window.location.href = filePath;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.arcadeHub = new ArcadeHub();
});
