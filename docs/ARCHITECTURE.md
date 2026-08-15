# SENTIENT_OS v2 — Mimari Tasarım Dokümanı

> **Versiyon:** 1.0  
> **Tarih:** 15 Ağustos 2026  
> **Durum:** Kesinleşmiş — Geliştirme öncesi referans

---

## 1. Genel Bakış

SENTIENT_OS v2, AI-tabanlı bir psikolojik korku deneyimidir. Mimari olarak iki bağımsız süreçten oluşur:

- **Electron App** (Presentation) — Overlay, chat penceresi, ses motoru, onboarding UI
- **Python Engine** (Backend) — AI, hikaye, dosya tarama, Win32 API, veritabanı

İki süreç yerel bir **WebSocket** bağlantısı üzerinden asenkron haberleşir.

---

## 2. Sistem Topolojisi

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KULLANICI                                   │
│                     (Windows 10/11)                                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
   ┌────────▼─────────┐        ┌─────────▼──────────┐
   │  ELECTRON APP     │        │  PYTHON ENGINE      │
   │  (Renderer)       │◄──────►│  (Headless Backend) │
   │                   │  WS    │                     │
   │  • Overlay Window │ IPC    │  • AI Brain         │
   │  • Chat Window    │        │  • Story Engine     │
   │  • Onboarding UI  │        │  • File Scanner     │
   │  • Web Audio API  │        │  • Win32 Bridge     │
   │  • CSS/WebGL FX   │        │  • Edge-TTS Worker  │
   │  • System Tray    │        │  • SQLite Store     │
   └──────────────────┘        └─────────────────────┘
            │                             │
            │    ┌───────────────────┐    │
            └────► KILL SWITCH       ◄────┘
                 │ (İzole Thread)    │
                 │ RegisterHotKey    │
                 │ Ctrl+Shift+Q     │
                 └───────────────────┘
```

### Neden Bu Topoloji?

| Sorun (V1) | Çözüm (V2) |
|------------|------------|
| PyQt6 + GDI render çakışması | Electron tek render pipeline (Chromium) |
| GUI thread + background thread karmaşası | İki ayrı süreç, temiz sorumluluk ayrımı |
| Monolitik Python uygulaması | Presentation ↔ Logic ayrımı |
| Test edilemeyen UI bağımlılıkları | Python backend UI'sız test edilebilir |

---

## 3. Katmanlı Mimari (Python Backend)

Python backend 3 katmandan oluşur. **Bağımlılık kuralı:** Üst katman alt katmanı bilir, alt katman üst katmanı BİLMEZ.

```
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER (Yönetim)                              │
│                                                             │
│  Director ─── Sahne yönetmeni: kim ne zaman ne yapacak      │
│  EventBus ─── Async pub/sub: modüller arası iletişim        │
│  Session ──── Oturum yaşam döngüsü: başlat/durdur/kurtar    │
│  Safety ───── Kill switch, resource guard, panic detection   │
├─────────────────────────────────────────────────────────────┤
│  DOMAIN LAYER (İş Mantığı)                                  │
│                                                             │
│  AIEngine ──── Gemini entegrasyon, prompt builder, cache     │
│  Personality ─ AI kişilik durumu ve evrimi                   │
│  Memory ────── 3 katmanlı hafıza (working/episodic/semantic) │
│  Narrative ─── Hikaye state machine, faz geçişleri           │
│  Timeline ──── Olay zamanlayıcı, pacing motoru               │
│  EffectDecider AI kararından efekt listesine dönüşüm         │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER (Altyapı)                             │
│                                                             │
│  Persistence ── SQLite wrapper, event store, checkpoint      │
│  Win32Bridge ── Masaüstü tarama, wallpaper, brightness       │
│  PrivacyFilter  Hassas dosya/yol filtreleme                  │
│  EdgeTTS ────── Async TTS üretim worker                      │
│  WSServer ───── WebSocket sunucusu                           │
│  Config ─────── Pydantic settings, YAML loader               │
│  Logger ─────── Structured JSON logging                      │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Inversion Örneği

```python
# KÖTÜ (V1 tarzı — doğrudan bağımlılık)
class Brain:
    def __init__(self):
        self.memory = Memory()  # Singleton, global state

# İYİ (V2 tarzı — constructor injection)
class Brain:
    def __init__(self, memory: MemoryInterface, config: Settings):
        self._memory = memory
        self._config = config
```

---

## 4. Electron Yapısı

```
electron-app/
├── main/                          # Main Process
│   ├── main.ts                    # Entry point
│   ├── ipc-bridge.ts              # WebSocket client → Python
│   ├── window-manager.ts          # Pencere oluşturma/yönetimi
│   ├── tray.ts                    # System tray icon + menü
│   └── kill-switch.ts             # Kill switch listener (yedek)
│
├── renderer/                      # Renderer Process(es)
│   ├── overlay/                   # Tam ekran şeffaf overlay
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── engine.js              # Efekt render motoru
│   │   └── effects/               # Bireysel efekt modülleri
│   │       ├── glitch.js
│   │       ├── text-overlay.js
│   │       ├── fade.js
│   │       ├── shake.js
│   │       └── particles.js
│   │
│   ├── chat/                      # AI chat penceresi
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── chat.js
│   │   └── typing-animation.js
│   │
│   ├── onboarding/                # Onboarding akışı
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── flow.js
│   │
│   └── audio/                     # Ses motoru
│       ├── ambient-engine.js      # Web Audio API ambient
│       ├── spatial-audio.js       # 3D konumlandırma
│       └── tts-player.js          # TTS playback
│
└── assets/                        # Statik kaynaklar
    ├── audio/
    ├── fonts/
    └── images/
```

### Pencere Tipleri

| Pencere | Tip | Özellikler |
|---------|-----|-----------|
| **Overlay** | `BrowserWindow` | `transparent: true`, `frame: false`, `alwaysOnTop: true`, `clickThrough: true`, tam ekran |
| **Chat** | `BrowserWindow` | `frame: false`, boyutlandırılabilir, sürüklenebilir, kapatılamaz (X → AI tepki) |
| **Onboarding** | `BrowserWindow` | `frame: false`, sabit boyut, ortada |
| **System Tray** | `Tray` | İkon + sağ tık menü (Ses aç/kapa, Çıkış) |

### Click-Through Overlay

```typescript
// Overlay penceresi fare tıklamalarını geçirir
// Sadece efekt anında geçici olarak interaktif olabilir
const overlay = new BrowserWindow({
  transparent: true,
  frame: false,
  alwaysOnTop: true,
  skipTaskbar: true,
  fullscreen: true,
  webPreferences: { /* ... */ }
});

// Normal durumda tıklama geçir
overlay.setIgnoreMouseEvents(true, { forward: true });

// Efekt anında interaktif yap (gerekirse)
overlay.setIgnoreMouseEvents(false);
```

---

## 5. Veri Akışı

### Kullanıcı Mesaj Akışı

```
Kullanıcı mesaj yazar (Chat)
    │
    ▼
Electron: chat.js → ipc-bridge.ts → WebSocket
    │
    ▼
Python: ws_server.py → EventBus("user_input")
    │
    ├── Director: Session kontrolü (aktif mi?)
    ├── Memory: Working memory'ye ekle
    ├── ContextBuilder: Prompt context oluştur
    │
    ▼
Brain: Gemini API çağrısı
    │
    ▼
ResponseParser: JSON validate + parse
    │
    ├── Memory: Episodic note kaydet (varsa)
    ├── Personality: Emotion güncelle
    ├── Narrative: narrative_signal işle
    ├── EffectDecider: Actions → efekt komutlarına çevir
    │
    ▼
WSServer → Electron'a gönder:
    ├── ai_response (chat'te göster)
    ├── effect (overlay'de render et)
    ├── tts_play (sesi çal)
    └── ambient_change (müziği değiştir)
```

### Timeline Olay Akışı (Kullanıcı Etkileşimsiz)

```
Timeline: Zamanlı olay tetiklendi
    │
    ▼
Triggers: Olay koşulları kontrol (idle süresi, faz, vb.)
    │
    ▼
Director: Sahneye uygun efekt zinciri oluştur
    │
    ▼
WSServer → Electron'a gönder:
    ├── effect_chain (sıralı efektler)
    ├── ambient_change
    └── ui_command (chat aç/kapat vb.)
```

---

## 6. State Yönetimi

### SQLite Schema

```sql
-- Oturum bilgisi
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    current_phase INTEGER DEFAULT 1,    -- 1, 2, 3
    current_path TEXT,                   -- curious, fear, attack
    language TEXT DEFAULT 'tr',
    intensity TEXT DEFAULT 'medium',     -- mild, medium, extreme
    status TEXT DEFAULT 'active'         -- active, completed, crashed
);

-- Working memory (geçici, oturum boyunca)
CREATE TABLE working_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,                  -- user, ai
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Episodic memory (kalıcı)
CREATE TABLE episodic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL,               -- AI tarafından üretilmiş özet
    importance REAL DEFAULT 0.5,         -- 0.0-1.0
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Semantic memory / kullanıcı profili (kalıcı)
CREATE TABLE user_profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Checkpoint (save/load)
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    label TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Olay logu
CREATE TABLE event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### ⚠️ SQLite Eşzamanlılık Yapılandırması

> [!WARNING]
> Olay logları, episodic memory ve checkpoint yazımları async worker'lar tarafından yoğun yapıldığında `database is locked` hatası oluşabilir.

**Çözüm (zorunlu):** `aiosqlite` bağlantısı açılır açılmaz aşağıdaki PRAGMA'ları uygulayın:

```python
async def init_database(db_path: str) -> aiosqlite.Connection:
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL;")       # Write-Ahead Logging
    await db.execute("PRAGMA busy_timeout=5000;")       # 5 saniye bekle, hemen hata verme
    await db.execute("PRAGMA synchronous=NORMAL;")      # WAL ile güvenli, daha hızlı
    await db.execute("PRAGMA cache_size=-64000;")        # 64MB cache
    return db
```

**WAL modunun faydaları:**
- Eşzamanlı okuma/yazma desteği (reader'lar writer'ı bloklamaz)
- Crash durumunda veri bütünlüğü korunur
- `busy_timeout` sayesinde geçici kilitlenmelerde otomatik retry

### Checkpoint Stratejisi

| Olay | Otomatik Kayıt |
|------|---------------|
| Katman geçişi (1→2, 2→3) | ✅ Tam checkpoint |
| Her 5 dakikada | ✅ Hafif checkpoint (sadece memory) |
| Crash/kill switch | ✅ Emergency checkpoint |
| Kullanıcı "kaydet" derse | ✅ Manuel checkpoint |
| Oturum sonu | ✅ Final checkpoint |

---

## 7. Tasarım Prensipleri

### Kesin Kurallar

1. **Global state yok.** Singleton pattern kullanılmayacak. Tüm bağımlılıklar constructor'dan enjekte edilecek.

2. **Interface-first.** Dış servislere (Gemini API, SQLite, Win32) erişen her modülün bir abstract base class'ı olacak. Test'te mock'lanabilir.

3. **Async-native.** Python backend tamamen `asyncio` üzerine kurulu. Blocking I/O (dosya okuma, API çağrısı, TTS) async wrapper'lar ile sarmalanacak.

4. **Event-driven.** Modüller birbirini doğrudan çağırmaz; EventBus üzerinden mesaj gönderir. Tek istisna: Director diğer modülleri koordine edebilir.

5. **Fail-safe.** Her dış çağrı (API, dosya, Win32) try-except ile sarılı. Hata → graceful degradation, asla crash değil.

6. **Immutable events.** EventBus üzerinden gönderilen mesajlar dataclass/frozen — alıcı tarafından değiştirilemez.

7. **Tek sorumluluk.** Bir dosya 300 satırı, bir sınıf 200 satırı aşarsa bölünmeli.

8. **DPI-aware.** Tüm ekran koordinatları DPI ölçeklemesine duyarlı olmalı.

---

## 7.1. ⚠️ DPI & Multi-Monitor Uyarısı

> [!WARNING]
> Birden fazla monitör veya %125/%150 Windows DPI ölçeklemesi olan sistemlerde `SetCursorPos` ve tam ekran overlay kayabilir.

**Çözüm (zorunlu):**

**Python tarafı (Win32):**
```python
import ctypes

# main.py başında, tüm Win32 çağrılarından ÖNCE çağrılmalı
try:
    awareness = ctypes.c_int()
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    # Windows 8.1 öncesi fallback
    ctypes.windll.user32.SetProcessDPIAware()
```

**Electron tarafı:**
```typescript
// main.ts — overlay penceresi oluştururken
const { screen } = require('electron');
const primaryDisplay = screen.getPrimaryDisplay();
const { width, height } = primaryDisplay.workAreaSize;
const scaleFactor = primaryDisplay.scaleFactor;

const overlay = new BrowserWindow({
    width: width,
    height: height,
    // scaleFactor'ü hesaba kat
    x: 0,
    y: 0,
    // ...
});
```

**Bu yapılmazsa:**
- Overlay penceresi ekranın %75'ini kaplayabilir (%125 DPI'da)
- Mouse drift efekti yanlış koordinatlara kayar
- Fake notification yanlış köşede belirir
- İkinci monitörde efektler hiç görünmez

---

## 8. Teknoloji Stack'i

### Python Backend

| Kütüphane | Versiyon | Amaç |
|-----------|---------|------|
| `google-generativeai` | ≥0.8.0 | Gemini API istemcisi |
| `edge-tts` | ≥6.1.0 | Microsoft Edge TTS |
| `websockets` | ≥12.0 | WebSocket sunucusu |
| `pydantic` | ≥2.0 | Config + veri validasyonu |
| `pydantic-settings` | ≥2.0 | Environment-aware ayarlar |
| `aiosqlite` | ≥0.19.0 | Async SQLite erişimi |
| `pywin32` | ≥306 | Windows API entegrasyonu |
| `psutil` | ≥5.9 | Sistem kaynak izleme |
| `pyyaml` | ≥6.0 | YAML config okuma |
| `pytest` | ≥8.0 | Test framework |
| `pytest-asyncio` | ≥0.23 | Async test desteği |

### Electron Frontend

| Paket | Versiyon | Amaç |
|-------|---------|------|
| `electron` | ≥30.0.0 | Masaüstü uygulama shell |
| `electron-builder` | ≥24.0.0 | Paketleme ve dağıtım |
| `typescript` | ≥5.0.0 | Type-safe geliştirme |

---

## 9. Proje Dizin Yapısı

```
sentient_v2/
├── python-engine/                    # Python Headless Backend
│   ├── src/
│   │   ├── main.py                   # Entry point
│   │   ├── config/                   # Ayar yönetimi
│   │   ├── core/                     # Orchestration katmanı
│   │   ├── ai/                       # AI domain
│   │   ├── story/                    # Hikaye domain
│   │   ├── infrastructure/           # Altyapı katmanı
│   │   └── locales/                  # i18n dosyaları
│   ├── tests/                        # Python testleri
│   ├── pyproject.toml
│   └── requirements.txt
│
├── electron-app/                     # Electron Frontend
│   ├── main/                         # Main process
│   ├── renderer/                     # Renderer process
│   ├── assets/                       # Statik kaynaklar
│   ├── package.json
│   └── electron-builder.yml
│
├── docs/                             # Proje dokümanları
├── installer/                        # Paketleme scriptleri
├── SENTIENT_OS_docs/                 # V1 referans
├── README.md
├── LICENSE
└── .gitignore
```

Detaylı dosya listesi için [implementation_plan.md](file:///C:/Users/muham/.gemini/antigravity-ide/brain/e4ce6fd0-004b-4d70-bd17-d465a2e7fc32/implementation_plan.md) Bölüm 7'ye bakınız.
