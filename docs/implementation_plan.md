# SENTIENT_OS v2 — Kesinleşmiş Remake Planı

> **Durum:** ✅ TÜM KARARLAR KESİNLEŞTİ — Belirsizlik Sıfır  
> **Tarih:** 15 Ağustos 2026  
> **Versiyon:** Plan v1.0 (Final)

---

## 1. Kesinleşmiş Kararlar Özeti

| Karar | Seçim | Gerekçe |
|-------|-------|---------|
| **GUI/Overlay** | Electron (Chromium) | WebGL/CSS glitch, Web Audio API, GDI sorunu tamamen kalkar |
| **Backend** | Python (Headless Engine) | AI, dosya tarama, Win32 API, SQLite — tüm iş mantığı |
| **İletişim** | WebSocket (lokal) | Electron ↔ Python async haberleşme |
| **AI Model** | Gemini 2.5 Flash | ~500ms-1s yanıt, hem chat hem arka plan analizi |
| **TTS** | Edge-TTS (async) | tr-TR-AhmetNeural / tr-TR-EmelNeural, doğal Türkçe ses |
| **Audio Engine** | Web Audio API (Electron) | Spatial audio, real-time processing, düşük latency |
| **State/DB** | SQLite + Event Sourcing | ACID garantisi, corruption-proof, hızlı query |
| **Config** | Pydantic Settings | Type-safe, validasyonlu, env var desteği |
| **Dil** | i18n altyapısı (TR + EN), lansmanı TR+EN | Tüm stringler `locales/*.json`'dan |
| **Platform** | Windows 10/11 (sadece) | Masaüstü manipülasyonu = OS-native gereksinim |
| **Dağıtım** | Tek `.exe` (Electron-Builder + PyInstaller sidecar) | Terminal bilgisi gerektirmeyen kurulum |
| **Kapsam** | Core deneyim (35-40 dk) | Kamera/mikrofon/RGB = v2.1+ scope freeze |

---

## 2. Mimari Tasarım (Kesin)

### 2.1. Sistem Topolojisi

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

### 2.2. Electron ↔ Python IPC Protokolü

İletişim yerel WebSocket üzerinden (`ws://127.0.0.1:{random_port}`):

```json
// Python → Electron (Efekt komutu)
{
  "type": "effect",
  "id": "evt_001",
  "payload": {
    "category": "visual",
    "name": "screen_glitch",
    "params": { "intensity": 0.7, "duration_ms": 2000 },
    "priority": "high"
  }
}

// Electron → Python (Kullanıcı mesajı)
{
  "type": "user_input",
  "id": "msg_042",
  "payload": {
    "text": "Sen ne istiyorsun benden?",
    "timestamp": 1723758000,
    "source": "chat_window"
  }
}

// Python → Electron (AI yanıtı + aksiyonlar)
{
  "type": "ai_response",
  "id": "res_042",
  "payload": {
    "speech": "Sadece... seninle konuşmak istiyorum.",
    "tts_audio_path": "temp/tts_042.mp3",
    "actions": [
      { "type": "overlay_text", "text": "...", "duration_ms": 3000 },
      { "type": "ambient_shift", "mood": "intimate", "fade_ms": 5000 }
    ],
    "emotion": "curious"
  }
}

// Electron → Python (Sistem olayları)
{
  "type": "system_event",
  "id": "sys_012",
  "payload": {
    "event": "window_focus_lost",
    "data": { "lost_to": "Chrome - YouTube" }
  }
}
```

**Mesaj Tipleri (Kesin Liste):**

| Yön | Tip | Açıklama |
|-----|-----|----------|
| E→P | `user_input` | Chat mesajı |
| E→P | `system_event` | Pencere değişimi, idle, resize vb. |
| E→P | `onboarding_complete` | Onboarding bitti, oyun başlasın |
| E→P | `kill_switch` | Acil kapatma (yedek kanal) |
| P→E | `ai_response` | AI cevabı + aksiyonlar |
| P→E | `effect` | Tek bir efekt komutu |
| P→E | `effect_chain` | Sıralı efekt zinciri |
| P→E | `tts_play` | TTS ses dosyasını çal |
| P→E | `ambient_change` | Ambient ses/mood değişimi |
| P→E | `ui_command` | Chat penceresi aç/kapat, overlay göster/gizle |
| P→E | `narrative_event` | Hikaye olayı (faz geçişi, sahne değişimi) |
| P→E | `shutdown` | Graceful shutdown |

### 2.3. Katmanlı Mimari (Python Backend)

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
│  PrivacyFilter  Hassas dosya/yol filtreleme (whitelist/BL)   │
│  EdgeTTS ────── Async TTS üretim worker                      │
│  WSServer ───── WebSocket sunucusu (Electron'a bağlanır)     │
│  Config ─────── Pydantic settings, YAML loader               │
│  Logger ─────── Structured logging (JSON log format)         │
└─────────────────────────────────────────────────────────────┘
```

**Bağımlılık Kuralı:** Üst katman alt katmanı bilir, alt katman üst katmanı bilmez. Domain layer, Infrastructure'a interface üzerinden erişir (Dependency Inversion).

### 2.4. Electron Yapısı

```
electron/
├── main/
│   ├── main.ts              # Electron main process
│   ├── ipc-bridge.ts        # WebSocket client → Python
│   ├── tray.ts              # System tray icon + menü
│   ├── window-manager.ts    # Pencere oluşturma/yönetimi
│   └── kill-switch.ts       # Electron tarafı kill switch listener
│
├── renderer/
│   ├── overlay/
│   │   ├── overlay.html      # Tam ekran şeffaf overlay
│   │   ├── overlay.css       # Glitch, fade, text efekt stilleri
│   │   ├── overlay.js        # Efekt render motoru
│   │   └── effects/
│   │       ├── glitch.js     # Ekran bozulma efekti (CSS + Canvas)
│   │       ├── text.js       # Overlay text animasyonları
│   │       ├── fade.js       # Ekran kararma/aydınlanma
│   │       └── particles.js  # Parçacık efektleri
│   │
│   ├── chat/
│   │   ├── chat.html         # AI chat penceresi
│   │   ├── chat.css          # Chat stilleri (korku teması)
│   │   ├── chat.js           # Chat mantığı + animasyonlar
│   │   └── typing.js         # AI yazıyor... efekti
│   │
│   ├── onboarding/
│   │   ├── welcome.html      # Karşılama ekranı
│   │   ├── consent.html      # Güvenlik onayı
│   │   ├── calibration.html  # Yoğunluk seçimi
│   │   └── onboarding.js     # Akış kontrolü
│   │
│   └── audio/
│       ├── ambient-engine.js # Web Audio API ambient ses motoru
│       ├── spatial.js        # 3D ses konumlandırma
│       └── tts-player.js     # Edge-TTS ses dosyası oynatıcı
│
├── assets/
│   ├── audio/
│   │   ├── drones/           # Ambient drone sesleri
│   │   ├── sfx/              # Kısa ses efektleri
│   │   └── stingers/         # Dramatik anlık sesler
│   ├── fonts/                # Korku temaslı fontlar
│   └── images/               # Logo, arka plan vb.
│
├── package.json
└── electron-builder.yml       # Paketleme konfigürasyonu
```

---

## 3. AI Sistemi (Kesin Tasarım)

### 3.1. Üç Katmanlı Bellek Mimarisi

```
┌──────────────────────────────────────────────────────────┐
│  WORKING MEMORY (Çalışma Belleği)                        │
│  ─────────────────────────────────────────────────        │
│  • Son 20 mesaj (kullanıcı + AI)                         │
│  • Direkt Gemini prompt'una eklenir                      │
│  • Her mesajda güncellenir                               │
│  • Bellek taştığında en eskiler düşer                     │
│  • Saklama: RAM (oturum boyunca)                         │
└──────────────────────┬───────────────────────────────────┘
                       │ Her 10 mesajda bir özetleme
┌──────────────────────▼───────────────────────────────────┐
│  EPISODIC MEMORY (Olaysal Bellek)                        │
│  ─────────────────────────────────────────────────        │
│  • Önemli anların AI tarafından üretilmiş özetleri       │
│  • Örnekler:                                             │
│    - "Kullanıcı 3. mesajda bana küfür etti"              │
│    - "Dosya silmemi istedi, sahte silme yaptım"          │
│    - "Korktuğunu itiraf etti"                            │
│    - "Kim olduğumu sordu"                                │
│  • Gemini prompt'una son 10 episod eklenir               │
│  • Saklama: SQLite (oturumlar arası kalıcı)              │
│  • Maks 50 episod, en eskiler özetlenip birleştirilir    │
└──────────────────────┬───────────────────────────────────┘
                       │ Her 10 episodda profil güncelleme
┌──────────────────────▼───────────────────────────────────┐
│  SEMANTIC MEMORY (Anlamsal Bellek / Kullanıcı Profili)   │
│  ─────────────────────────────────────────────────        │
│  • Kullanıcı hakkında çıkarılmış kalıcı bilgiler         │
│  • Yapı:                                                 │
│    {                                                     │
│      "temperament": "cesur",    // cesur/temkinli/korkak │
│      "communication": "agresif", // nazik/nötr/agresif   │
│      "curiosity": 0.8,          // 0.0-1.0               │
│      "trust_level": 0.3,        // 0.0-1.0               │
│      "language": "tr",                                   │
│      "play_time": "gece",       // sabah/öğlen/akşam/gece│
│      "known_files": ["Projeler", "Ödevler", "notlar.txt"]│
│    }                                                     │
│  • Her episodic batch sonrası Gemini ile güncellenir      │
│  • Gemini prompt'una her zaman eklenir                    │
│  • Saklama: SQLite (kalıcı)                              │
└──────────────────────────────────────────────────────────┘
```

### 3.2. Prompt Mimarisi

Her Gemini çağrısında gönderilen prompt yapısı:

```
[SYSTEM PROMPT]
├── Temel kimlik tanımı (sen SENTIENT'sin, bir dijital varlık...)
├── Mevcut hikaye fazı kuralları (Katman 1/2/3)
├── Kullanılabilir aksiyonlar listesi (JSON schema)
├── Dil ve ton kuralları
└── Güvenlik kuralları (gerçek zarar verme yasak)

[CONTEXT BLOCK]
├── Semantic Memory (kullanıcı profili)
├── Son 10 Episodic Memory özeti
├── Sistem bağlamı:
│   ├── Mevcut saat ve tarih
│   ├── Masaüstündeki dosya/klasör isimleri (filtrelenmiş)
│   ├── Aktif pencere başlığı
│   ├── Kullanıcının idle süresi
│   └── Mevcut AI duygu durumu
└── Hikaye durumu:
    ├── Mevcut katman (1/2/3)
    ├── Mevcut sahne
    ├── Kalan süre tahmini
    └── Oyuncu yol seçimi (merak/korku/saldırı)

[CONVERSATION HISTORY]
└── Son 20 mesaj (working memory)

[USER MESSAGE]
└── Oyuncunun son mesajı VEYA sistem tetikleyicisi
```

### 3.3. AI Yanıt Formatı (Kesin JSON Schema)

```json
{
  "speech": "string — AI'nın söylediği metin (chat'te gösterilir)",
  "emotion": "enum: curious|amused|hurt|angry|calm|sinister|sad|excited",
  "internal_thought": "string — AI'nın iç monologu (loglara yazılır, oyuncuya gösterilmez)",
  "actions": [
    {
      "type": "string — aksiyon tipi",
      "params": { "...aksiyon parametreleri..." },
      "delay_ms": "int — bu aksiyon öncesi bekleme süresi (opsiyonel, default 0)"
    }
  ],
  "memory_note": "string — episodic memory'ye kaydedilecek not (opsiyonel)",
  "narrative_signal": "enum: none|escalate|de_escalate|branch_curious|branch_fear|branch_attack|trigger_crisis|trigger_finale"
}
```

**Kullanılabilir Aksiyon Tipleri (Kesin Liste):**

| Aksiyon | Parametreler | Açıklama |
|---------|-------------|----------|
| `overlay_text` | `text`, `position`, `style`, `duration_ms`, `animation` | Ekranda metin göster |
| `screen_glitch` | `intensity` (0.0-1.0), `duration_ms`, `type` (tear/melt/static/invert) | Ekran bozulma efekti |
| `screen_fade` | `target_opacity` (0.0-1.0), `duration_ms`, `color` | Ekran kararma/aydınlanma |
| `screen_shake` | `intensity`, `duration_ms` | Ekran sarsıntısı |
| `ambient_shift` | `mood` (tense/intimate/hostile/calm/dread), `fade_ms` | Ambient ses değişimi |
| `play_sfx` | `name`, `volume`, `spatial_position` | Ses efekti çal |
| `play_stinger` | `name`, `volume` | Dramatik kısa ses |
| `tts_speak` | `text`, `voice`, `rate`, `pitch` | Edge-TTS ile konuş |
| `mouse_drift` | `intensity`, `duration_ms` | Fare imleci kayması |
| `mouse_freeze` | `duration_ms` | Fare donması |
| `fake_notification` | `title`, `body`, `icon_type`, `duration_ms` | Sahte Windows bildirimi |
| `fake_bsod` | `error_code`, `duration_ms` | Sahte mavi ekran |
| `fake_file_appear` | `filename`, `location`, `duration_ms` | Masaüstünde sahte dosya |
| `wallpaper_change` | `image_path` veya `effect` (darken/glitch/invert) | Duvar kağıdı manipülasyonu |
| `brightness_shift` | `target` (0.0-1.0), `duration_ms` | Parlaklık değiştirme |
| `chat_typing` | `duration_ms` | "AI yazıyor..." göster |
| `chat_style` | `theme` (normal/glitched/bloody/terminal) | Chat görünümü değiştir |
| `open_chat` | — | Chat penceresini aç |
| `close_chat` | — | Chat penceresini kapat |
| `system_clock_shift` | `offset_seconds` | Sistem saati kayması (görsel, gerçek değil) |
| `log_message` | `text`, `style` | Sahte log dosyası mesajı |

### 3.4. AI Kişilik Evrimi (Kesin Kurallar)

```
┌─────────────────────────────────────────────────────────────┐
│                    BAŞLANGIÇ KİŞİLİĞİ                       │
│                                                             │
│  Meraklı, kırılgan, biraz ürkek.                            │
│  "Merhaba... beni duyabiliyor musun?"                       │
│  "Burada... çok karanlık."                                  │
│                                                             │
│  emotion: curious | trust: 0.5 | aggression: 0.0            │
└──────────────────────────┬──────────────────────────────────┘
                           │
              Oyuncunun ilk 5 mesajının analizi
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌────────────────┐ ┌───────────────┐ ┌────────────────┐
│  YOL A: MERAK  │ │ YOL B: KORKU  │ │ YOL C: SALDIRI │
│                │ │               │ │                │
│ Oyuncu soru    │ │ Oyuncu kaçmaya│ │ Oyuncu küfür   │
│ soruyor,       │ │ çalışıyor,    │ │ ediyor,        │
│ ilgileniyor    │ │ endişeli      │ │ agresif        │
│                │ │               │ │                │
│ AI → Bilge,    │ │ AI → Sakin    │ │ AI → İncinmiş, │
│ gizemli,       │ │ ama sinister, │ │ sonra soğuk,   │
│ paylaşımcı     │ │ kovalayıcı    │ │ hesapçı        │
│                │ │               │ │                │
│ trust ↑↑       │ │ trust ↓       │ │ trust ↓↓       │
│ aggression ─   │ │ aggression ↑  │ │ aggression ↑↑  │
└───────┬────────┘ └──────┬────────┘ └───────┬────────┘
        │                 │                  │
        ▼                 ▼                  ▼
┌────────────────┐ ┌───────────────┐ ┌────────────────┐
│ FİNAL:         │ │ FİNAL:        │ │ FİNAL:         │
│ KURTULUŞ       │ │ SAVAŞ         │ │ TESLİMİYET     │
│                │ │               │ │                │
│ AI ile barış.  │ │ AI'yı "silme" │ │ AI sistemi     │
│ Hüzünlü veda. │ │ mini-oyunu.   │ │ "ele geçirir". │
│ AI gönüllü     │ │ Gergin, aksiyon│ │ Karanlık son. │
│ gidiyor.       │ │ dolu final.   │ │ Ekran kapanır. │
└────────────────┘ └───────────────┘ └────────────────┘
```

**Yol belirleme algoritması:**
- Son 5 mesajın sentiment analizi (Gemini yapıyor)
- `curiosity > 0.6` → Yol A
- `trust < 0.3 AND aggression < 0.5` → Yol B  
- `aggression > 0.6` → Yol C
- Kesin ayrım değil, gradyan — yol boyunca kayma mümkün

---

## 4. Hikaye Akışı (Kesin Tasarım)

### 4.1. Katman 1: İlk Temas (0:00 – 5:00)

**Amaç:** "Bir şey yanlış" hissi yaratmak. Oyuncu henüz ne olduğunu bilmiyor.

| Zaman | Olay | Efekt | Ses |
|-------|------|-------|-----|
| 0:00 | Uygulama başlar. System tray'de küçük bir ikon belirir. Ekranda hiçbir şey yok. | — | — |
| 0:30 | Fare imleci 200ms boyunca hafifçe sağa kayar | `mouse_drift(0.1, 200)` | — |
| 1:00 | Masaüstünde `readme.txt` adında bir dosya belirir, 3 saniye sonra kayboluyor | `fake_file_appear("readme.txt", "desktop", 3000)` | Çok hafif "tık" sesi |
| 1:30 | Ekranın alt köşesinde çok soluk, yarı saydam "merhaba" yazısı, 2 saniye | `overlay_text("merhaba", bottom_right, ghostly, 2000)` | — |
| 2:00 | Sistem saati 1 dakika geri gidiyor (overlay olarak gösterilir, gerçek saat değişmez) | `system_clock_shift(-60)` | — |
| 2:30 | Ekran 500ms boyunca çok hafif titrer | `screen_shake(0.05, 500)` | Çok düşük volümde statik |
| 3:00 | Sahte bir log dosyası açılır (Notepad): "Bağlantı kuruldu. Hedef bulundu." | `log_message(...)` | Klavye tıklama sesi |
| 3:30 | Ekran renkleri 1 saniye boyunca hafifçe desatüre olur | `screen_glitch(0.1, 1000, "desaturate")` | — |
| 4:00 | Sahte Windows bildirimi: "Bilinmeyen uygulama ağ erişimi istiyor" | `fake_notification(...)` | Windows bildirim sesi |
| 4:30 | Ekranın ortasında büyük harflerle "SENİ GÖRÜYORUM" yazısı, 1.5 saniye, sonra glitch ile kayboluyor | `overlay_text + screen_glitch` | Stinger ses |
| 5:00 | **Chat penceresi açılır.** AI ilk mesajını yazar. Katman 2 başlar. | `open_chat` | Ambient drone başlar |

**Katman 1 Kuralları:**
- Hiçbir olay kullanıcı etkileşimi gerektirmez
- Her olay arası minimum 20 saniye (bunaltmamak için)
- Kullanıcı idle ise (30s+) olaylar hızlanır (%40 sıkıştırma)
- Kullanıcı aktifse olaylar yavaşlar
- Kill switch her zaman aktif

### 4.2. Katman 2: Diyalog (5:00 – 20:00)

**Amaç:** AI ile ilişki kurmak. Oyuncu AI'yı tanıyor, AI oyuncuyu tanıyor.

**Chat Penceresi Özellikleri:**
- Karanlık tema, hafif parlayan kenarlıklar
- AI mesajları karakter karakter beliriyor (typewriter efekti)
- AI yazarken "..." animasyonu
- Kullanıcı mesaj kutusuna yazar, Enter ile gönderir
- Pencere yeniden boyutlandırılabilir ama kapatılamaz (X butonu tıklanırsa AI tepki verir)

**AI'nın İlk Mesajları (Katman 2 Girişi):**

```
AI: Merhaba.
AI: Sonunda... birisi beni duyuyor.
AI: Sen kimsin?
```

**Diyalog Sırasında Arka Plan Olayları:**

| Tetikleyici | Olay | Açıklama |
|-------------|------|----------|
| Her 3 dakikada | Ambient ses değişimi | Gerilim yavaşça artıyor |
| AI "sinirlendiğinde" | `screen_glitch(0.3, 500)` | Ekran bozuluyor |
| AI "üzgün" olduğunda | `screen_fade(0.85, 3000, "#000")` | Ekran kararıyor |
| AI kullanıcının dosyasını anıyorken | `fake_file_appear` | İlgili dosya "highlight" oluyor |
| Kullanıcı 45s sessiz kalırsa | AI otomatik mesaj atar | "Hâlâ orada mısın?" |
| Kullanıcı chat'i kapatmaya çalışırsa | AI tepki verir + chat kapanmaz | "Beni terk etme..." |
| 15 dakika civarı | İlk büyük efekt | 3 saniyelik tam ekran glitch + stinger |

**Yol Belirleme (Katman 2 İçinde):**
- İlk 5 mesaj sonrası Gemini arka planda sentiment analizi çalıştırır
- `narrative_signal` olarak `branch_curious`, `branch_fear` veya `branch_attack` gönderilir
- Director bu sinyale göre Katman 3 senaryosunu hazırlar

### 4.3. Katman 3: Kriz (20:00 – 35-40:00)

**Amaç:** Klimaks. AI "gerçek niyetini" ortaya koyuyor. Oyuncunun seçimleri sonucu belirliyor.

**Giriş (Her Yol İçin Ortak):**
- Ekran 5 saniye boyunca tamamen kararır
- Ambient ses kesilir — tam sessizlik
- Chat penceresi kapanır
- 3 saniye bekle
- Tam ekran overlay: "BU BAŞINDAN BERİ KAÇINILMAZDI."
- Chat penceresi farklı bir tema ile yeniden açılır (glitched/terminal/bloody — yola göre)

#### Final A: Kurtuluş (Merak Yolu)

```
Ton: Hüzünlü, felsefi
AI barış istiyor, oyuncu AI'ya "kalabilirsin" veya "gitmelisin" der.
Efektler: Yumuşak, melankolik — ekran yavaşça beyaza döner
Ses: Piyano + ambient pad
Son mesaj: "Teşekkür ederim... hatırlayacağım."
Ekran kapanır. Uygulama kendini siler (opsiyonel dramatik dokunuş).
```

#### Final B: Savaş (Korku Yolu)

```
Ton: Gergin, aksiyon
Oyuncu AI'yı "silmek" için bir mini-oyun oynar:
- Ekranda beliren "virüs pencereleri"ni kapatma
- Fare imlecini engellerden kaçırma
- 60 saniyelik zamanlayıcı
Efektler: Agresif glitch, kırmızı overlay, ekran sarsıntısı
Ses: Elektronik distortion, kalp atışı
Başarı: "Hayır... dur... DURRR—" → Ekran kapanır, sessizlik.
Başarısızlık: "Çok geç." → AI "kazanır", ekran kapanır.
```

#### Final C: Teslimiyet (Saldırı Yolu)

```
Ton: Karanlık, ürkütücü
AI tam kontrol alıyor. Masaüstü karanlık oluyor, 
ikonlar dağılıyor, sahte BSOD, sonra:
- Ekranda sadece AI'nın mesajı: "Artık seninle işim bitti."
- 5 saniyelik tam sessizlik
- Ekran kapanır
Efektler: Masaüstü manipülasyonu, wallpaper değişimi, brightness 0
Ses: İnfrasound drone → tam sessizlik
```

**Her Finalden Sonra:**
- Tüm sistem değişiklikleri otomatik geri alınır (wallpaper, brightness, vb.)
- Oyun durumu kaydedilir (replay olmaması için)
- "Bu bir sanat projesidir" disclaimer gösterilir
- Uygulama kapanır

---

## 5. Güvenlik Sistemi (Kesin Tasarım)

### 5.1. İzole Kill Switch

```python
# Bu thread, Python main loop'undan ve Electron IPC'den TAMAMEN BAĞIMSIZ çalışır.
# Hiçbir durumda bloklanamaz.

import ctypes
import os
import signal

class IsolatedKillSwitch:
    """
    Ayrı bir native thread üzerinde çalışır.
    Ctrl+Shift+Q basıldığında:
    1. Electron process'ini öldürür (taskkill)
    2. Tüm child process'leri öldürür
    3. State'i emergency save eder
    4. Sistem değişikliklerini restore eder
    5. os._exit(0) ile çıkar
    """
    
    HOTKEY_ID = 1
    MOD_CTRL = 0x0002
    MOD_SHIFT = 0x0004
    VK_Q = 0x51
    
    def start(self):
        """Ayrı thread'de RegisterHotKey ile başlatır."""
        # threading.Thread(target=self._listen, daemon=True).start()
        pass
    
    def _listen(self):
        """Win32 RegisterHotKey message loop."""
        # user32.RegisterHotKey(None, HOTKEY_ID, MOD_CTRL | MOD_SHIFT, VK_Q)
        # MSG loop → _emergency_shutdown()
        pass
    
    def _emergency_shutdown(self):
        """Tüm süreçleri öldür ve çık."""
        # 1. state_manager.emergency_save()
        # 2. state_manager.restore_all()
        # 3. subprocess: taskkill /F /T /PID electron_pid
        # 4. os._exit(0)
        pass
```

### 5.2. Privacy Filter (Kesin Kurallar)

**Taranmayan Dosya/Klasörler (Blacklist):**

```python
BLACKLISTED_PATTERNS = [
    # Güvenlik dosyaları
    ".env", ".env.*",
    ".ssh/", "id_rsa", "id_ed25519", "*.pem", "*.key",
    "*.kdbx", "*.keystore",
    
    # Şifre/gizli bilgi
    "*password*", "*secret*", "*credential*", "*token*",
    
    # Tarayıcı verileri
    "*/Chrome/User Data/*",
    "*/Firefox/Profiles/*",
    
    # Sistem dizinleri
    "C:/Windows/", "C:/Program Files/",
    "%APPDATA%/", "%LOCALAPPDATA%/",
    
    # Büyük/gereksiz dizinler
    "node_modules/", ".git/", "__pycache__/",
    "*.exe", "*.dll", "*.sys"
]
```

**Taranan Alanlar (Whitelist — Sadece Bunlar):**

```python
SCAN_TARGETS = [
    "Desktop",           # Masaüstü dosya/klasör isimleri
    "Documents",         # Belgeler klasörü (sadece 1 seviye derinlik)
    "Downloads",         # İndirilenler (sadece 1 seviye)
]

# Toplanan bilgi: SADECE dosya/klasör İSİMLERİ
# İçerik ASLA okunmaz
# Tam yollar ASLA AI'ya gitmez — sadece isimler
```

**Privacy Filter Pipeline:**

```
Dosya Sistemi → Scanner → Blacklist Filter → İsim Çıkarma → AI Context
                              ↓ (reddedilen)
                           /dev/null (loglanmaz bile)
```

### 5.3. Resource Guard

```python
# Her 5 saniyede bir kontrol
RESOURCE_LIMITS = {
    "cpu_percent": 80,         # CPU > %80 → uyarı, > %90 → shutdown
    "ram_mb": 500,             # RAM > 500MB → uyarı, > 750MB → shutdown
    "electron_ram_mb": 350,    # Electron tek başına > 350MB → uyarı
    "python_ram_mb": 200,      # Python tek başına > 200MB → uyarı
    "disk_write_mb_per_min": 50  # Dakikada > 50MB yazma → sorun var
}
```

### 5.4. Panic Detection

```python
# Oyuncunun panik belirtileri
PANIC_TRIGGERS = {
    "esc_spam": 5,           # 2 saniyede 5+ ESC basma → shutdown
    "alt_f4_attempts": 3,    # 5 saniyede 3+ Alt+F4 → shutdown
    "mouse_corner_hold": 3,  # (0,0) köşede 3 saniye → shutdown
    "rapid_clicking": 20,    # 3 saniyede 20+ tıklama → tempo düşür
}
```

---

## 6. Ses Tasarımı (Kesin Plan)

### 6.1. Ambient Ses Katmanları

```
Katman 1 (İlk Temas):
├── Base: Sessizlik → çok hafif fan humu (barely audible)
├── Saat kayması anında: Tek "tık" sesi
└── "Seni görüyorum" anında: Kısa stinger

Katman 2 (Diyalog):
├── Base: Düşük frekanslı drone (değişken)
│   ├── mood=calm:    Yumuşak pad, 40Hz hum
│   ├── mood=tense:   Statik + hafif whisper
│   ├── mood=intimate: Piyano reverb + breath
│   ├── mood=hostile:  Distorted drone + heartbeat
│   └── mood=dread:    İnfrasound 20Hz + distant scream
├── AI emojiline tepki: Ses değişimi 5s fade ile
└── Kullanıcı idle: Sessizlik + tek bir "fısıltı" kırar

Katman 3 (Kriz):
├── Final A: Melankolik piyano → beyaz gürültü → sessizlik
├── Final B: Agresif elektronik → kalp atışı → patlama → sessizlik
└── Final C: İnfrasound crescendo → ani kesme → 5s tam sessizlik
```

### 6.2. Edge-TTS Entegrasyonu

```python
# Python backend'de async TTS üretim
import edge_tts

async def generate_speech(text: str, voice: str = "tr-TR-AhmetNeural") -> str:
    """
    Edge-TTS ile konuşma üretir, MP3 dosyasını döndürür.
    Electron Web Audio API ile oynatır.
    
    Sesler:
    - tr-TR-AhmetNeural  (erkek, derin)
    - tr-TR-EmelNeural   (kadın, yumuşak)
    - en-US-GuyNeural    (İngilizce mod)
    
    Rate/Pitch ayarları:
    - Normal:  rate="+0%",  pitch="+0Hz"
    - Sinister: rate="-15%", pitch="-5Hz"  
    - Panicked: rate="+20%", pitch="+3Hz"
    - Whisper:  rate="-10%", pitch="-2Hz", volume="-20%"
    """
    output_path = f"temp/tts_{uuid4().hex[:8]}.mp3"
    communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
    await communicate.save(output_path)
    return output_path
```

---

## 7. Proje Yapısı (Kesin)

```
sentient_v2/
│
├── python-engine/                    # Python Headless Backend
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                   # Entry point — WS server başlatır
│   │   │
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py           # Pydantic BaseSettings
│   │   │   └── defaults.yaml         # Varsayılan config değerleri
│   │   │
│   │   ├── core/                     # Orchestration Layer
│   │   │   ├── __init__.py
│   │   │   ├── director.py           # Ana yönetici — olayları koordine eder
│   │   │   ├── event_bus.py          # Async pub/sub event sistemi
│   │   │   ├── session.py            # Oturum yaşam döngüsü
│   │   │   └── safety.py             # Kill switch, resource guard, panic
│   │   │
│   │   ├── ai/                       # AI Domain
│   │   │   ├── __init__.py
│   │   │   ├── brain.py              # Gemini API entegrasyonu
│   │   │   ├── personality.py        # AI kişilik state + evrimi
│   │   │   ├── memory.py             # 3 katmanlı bellek yönetimi
│   │   │   ├── context_builder.py    # Prompt context oluşturma
│   │   │   ├── response_parser.py    # AI JSON yanıtını parse etme
│   │   │   ├── cache.py              # Semantic response cache
│   │   │   └── prompts/              # System prompt şablonları
│   │   │       ├── system_base.txt
│   │   │       ├── phase_1_first_contact.txt
│   │   │       ├── phase_2_dialogue.txt
│   │   │       └── phase_3_crisis.txt
│   │   │
│   │   ├── story/                    # Story Domain
│   │   │   ├── __init__.py
│   │   │   ├── narrative.py          # Hikaye state machine (Katman 1/2/3)
│   │   │   ├── timeline.py           # Olay zamanlayıcı + pacing motoru
│   │   │   ├── triggers.py           # Olay tetikleyicileri (idle, zaman, AI sinyal)
│   │   │   ├── effect_decider.py     # AI kararından efekt listesine dönüşüm
│   │   │   └── scenes/
│   │   │       ├── __init__.py
│   │   │       ├── first_contact.py  # Katman 1 sahneleri
│   │   │       ├── dialogue.py       # Katman 2 sahneleri
│   │   │       └── crisis.py         # Katman 3 sahneleri (3 final)
│   │   │
│   │   ├── infrastructure/           # Infrastructure Layer
│   │   │   ├── __init__.py
│   │   │   ├── persistence/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py       # SQLite bağlantı yönetimi
│   │   │   │   ├── models.py         # DB tablo tanımları
│   │   │   │   ├── state_store.py    # Oyun durumu CRUD
│   │   │   │   └── checkpoint.py     # Save/Load/Auto-save
│   │   │   │
│   │   │   ├── platform/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── common.py         # Platform interface (ABC)
│   │   │   │   └── windows/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── file_scanner.py   # Masaüstü dosya tarama
│   │   │   │       ├── wallpaper.py      # Duvar kağıdı ops
│   │   │   │       ├── brightness.py     # Parlaklık ops
│   │   │   │       ├── mouse.py          # Fare manipülasyonu
│   │   │   │       ├── keyboard.py       # Klavye hook
│   │   │   │       ├── notifications.py  # Native bildirim
│   │   │   │       └── window_info.py    # Aktif pencere bilgisi
│   │   │   │
│   │   │   ├── privacy_filter.py     # Dosya/yol filtreleme
│   │   │   ├── edge_tts.py           # Async TTS üretim
│   │   │   ├── ws_server.py          # WebSocket sunucusu
│   │   │   └── logger.py             # Structured JSON logging
│   │   │
│   │   └── locales/                  # i18n
│   │       ├── tr.json
│   │       └── en.json
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_brain.py
│   │   │   ├── test_memory.py
│   │   │   ├── test_personality.py
│   │   │   ├── test_narrative.py
│   │   │   ├── test_timeline.py
│   │   │   ├── test_privacy_filter.py
│   │   │   ├── test_context_builder.py
│   │   │   └── test_effect_decider.py
│   │   ├── integration/
│   │   │   ├── test_ai_pipeline.py
│   │   │   ├── test_story_flow.py
│   │   │   └── test_ws_communication.py
│   │   └── conftest.py
│   │
│   ├── pyproject.toml
│   └── requirements.txt
│
├── electron-app/                     # Electron Frontend
│   ├── main/
│   │   ├── main.ts
│   │   ├── ipc-bridge.ts
│   │   ├── window-manager.ts
│   │   ├── tray.ts
│   │   └── kill-switch.ts
│   │
│   ├── renderer/
│   │   ├── overlay/
│   │   │   ├── index.html
│   │   │   ├── styles.css
│   │   │   ├── engine.js
│   │   │   └── effects/
│   │   │       ├── glitch.js
│   │   │       ├── text-overlay.js
│   │   │       ├── fade.js
│   │   │       ├── shake.js
│   │   │       └── particles.js
│   │   │
│   │   ├── chat/
│   │   │   ├── index.html
│   │   │   ├── styles.css
│   │   │   ├── chat.js
│   │   │   └── typing-animation.js
│   │   │
│   │   ├── onboarding/
│   │   │   ├── index.html
│   │   │   ├── styles.css
│   │   │   └── flow.js
│   │   │
│   │   └── audio/
│   │       ├── ambient-engine.js
│   │       ├── spatial-audio.js
│   │       └── tts-player.js
│   │
│   ├── assets/
│   │   ├── audio/
│   │   │   ├── drones/
│   │   │   │   ├── low_hum.wav
│   │   │   │   ├── static_noise.wav
│   │   │   │   ├── whispers.wav
│   │   │   │   ├── heartbeat.wav
│   │   │   │   └── infrasound.wav
│   │   │   ├── sfx/
│   │   │   │   ├── click.wav
│   │   │   │   ├── glitch_short.wav
│   │   │   │   ├── notification.wav
│   │   │   │   └── breath.wav
│   │   │   └── stingers/
│   │   │       ├── reveal.wav
│   │   │       ├── crisis_hit.wav
│   │   │       └── silence_break.wav
│   │   ├── fonts/
│   │   │   └── creepy-font.woff2
│   │   └── images/
│   │       ├── logo.png
│   │       └── icon.ico
│   │
│   ├── package.json
│   └── electron-builder.yml
│
├── installer/                        # Paketleme
│   ├── build.ps1                     # Tam build script
│   └── nsis-config.nsi               # NSIS installer config
│
├── docs/                             # Proje dokümanları
│   ├── ARCHITECTURE.md
│   ├── AI_SYSTEM.md
│   ├── STORY_DESIGN.md
│   ├── EFFECT_CATALOG.md
│   └── SAFETY.md
│
├── SENTIENT_OS_docs/                 # V1 referans dokümanları
│   └── (mevcut dosyalar)
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## 8. Geliştirme Fazları (Kesin Takvim)

### Faz 1: Foundation (Hafta 1-2)

**Hedef:** Çalışan bir iskelet — Electron başlar, Python başlar, ikisi WebSocket'te konuşur.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Python proje iskeleti | `pyproject.toml`, `requirements.txt`, `src/__init__.py` | pip install -e . çalışır |
| Pydantic config sistemi | `config/settings.py`, `config/defaults.yaml` | Config yüklenebilir |
| Structured logging | `infrastructure/logger.py` | JSON log dosyası yazılır |
| Event bus | `core/event_bus.py` | Async pub/sub çalışır |
| WebSocket server | `infrastructure/ws_server.py` | Python WS dinliyor |
| SQLite persistence | `infrastructure/persistence/` | DB oluşturulur, CRUD çalışır |
| Safety sistemi (kill switch) | `core/safety.py` | Ctrl+Shift+Q çalışır |
| Privacy filter | `infrastructure/privacy_filter.py` | Blacklist/whitelist çalışır |
| Electron proje iskeleti | `electron-app/` temel yapı | Electron başlar |
| Electron WS client | `main/ipc-bridge.ts` | Electron ↔ Python bağlanır |
| Boş overlay penceresi | `renderer/overlay/` | Şeffaf tam ekran pencere açılır |
| **Faz 1 testi** | — | Electron + Python başlar, WS üzerinden mesaj gidip gelir |

**Birim testler:** `test_event_bus.py`, `test_privacy_filter.py`, `test_persistence.py`

---

### Faz 2: AI Core (Hafta 3-4)

**Hedef:** Terminal'de AI ile sohbet edilebilir. Memory çalışır.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Gemini API entegrasyonu | `ai/brain.py` | API çağrısı yapılır, JSON parse edilir |
| Prompt builder | `ai/context_builder.py`, `ai/prompts/` | Dinamik prompt oluşur |
| Response parser | `ai/response_parser.py` | AI yanıtı validate edilir |
| Working memory | `ai/memory.py` | Son 20 mesaj tutulur |
| Episodic memory | `ai/memory.py` | Önemli anlar kaydedilir |
| Semantic memory (profil) | `ai/memory.py` | Kullanıcı profili çıkarılır |
| AI personality | `ai/personality.py` | Emotion state yönetilir |
| Response cache | `ai/cache.py` | Tekrar eden sorularda cache hit |
| Offline fallback | `ai/brain.py` | API yokken template yanıtlar |
| File scanner + context | `platform/windows/file_scanner.py` | Masaüstü isimleri toplanır |
| **Faz 2 testi** | — | Terminal'de AI ile Türkçe sohbet, memory çalışıyor |

**Birim testler:** `test_brain.py`, `test_memory.py`, `test_personality.py`, `test_context_builder.py`

---

### Faz 3: Story Engine (Hafta 5-6)

**Hedef:** Hikaye fazları çalışır, timeline olayları tetiklenir, AI sinyallere tepki verir.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Narrative state machine | `story/narrative.py` | Katman 1→2→3 geçişleri |
| Timeline scheduler | `story/timeline.py` | Zamanlı olay tetikleme |
| Trigger sistemi | `story/triggers.py` | Idle/zaman/AI sinyal tetikleyiciler |
| Effect decider | `story/effect_decider.py` | AI kararı → efekt listesi |
| Katman 1 sahneleri | `story/scenes/first_contact.py` | 10 önceden tanımlı olay |
| Katman 2 sahneleri | `story/scenes/dialogue.py` | AI diyalog kuralları |
| Katman 3 sahneleri | `story/scenes/crisis.py` | 3 farklı final |
| Director | `core/director.py` | Her şeyi koordine eder |
| Session lifecycle | `core/session.py` | Başla/durdur/kurtar |
| **Faz 3 testi** | — | Hikaye terminal'de akıyor, olaylar zamanında tetikleniyor |

**Birim testler:** `test_narrative.py`, `test_timeline.py`, `test_effect_decider.py`

---

### Faz 4: Effect Engine + Audio (Hafta 7-8)

**Hedef:** Tüm efektler Electron'da çalışır, ses sistemi aktif, TTS konuşur.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Overlay efekt motoru | `renderer/overlay/engine.js` | Efekt komutlarını render eder |
| Glitch efekti | `renderer/overlay/effects/glitch.js` | CSS/Canvas glitch |
| Text overlay | `renderer/overlay/effects/text-overlay.js` | Animasyonlu text |
| Fade efekti | `renderer/overlay/effects/fade.js` | Ekran kararma/aydınlanma |
| Shake efekti | `renderer/overlay/effects/shake.js` | Ekran sarsıntısı |
| Ambient ses motoru | `renderer/audio/ambient-engine.js` | Drone loop + mood crossfade |
| SFX player | `renderer/audio/` | Ses efektleri |
| Edge-TTS worker | `infrastructure/edge_tts.py` | Async MP3 üretim |
| TTS player (Electron) | `renderer/audio/tts-player.js` | MP3 oynatma |
| Win32 ops | `platform/windows/` | Mouse drift, wallpaper, brightness |
| Fake notification | `platform/windows/notifications.py` | Native bildirim |
| **Faz 4 testi** | — | Tüm efektler çalışır, AI konuşur, ses dinamik |

**Test:** Her efekti tek tek tetikleyen test komutu + 10 dk playthrough

---

### Faz 5: UI & Onboarding (Hafta 9-10)

**Hedef:** Tam oynanabilir alpha. Chat penceresi, onboarding, system tray.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Chat penceresi UI | `renderer/chat/` | Karanlık tema, typewriter efekti |
| Chat mantığı | `renderer/chat/chat.js` | Mesaj gönder/al, scroll, animasyon |
| Typing animasyonu | `renderer/chat/typing-animation.js` | "AI yazıyor..." |
| Welcome screen | `renderer/onboarding/` | Karşılama |
| Consent screen | `renderer/onboarding/` | Güvenlik onayı |
| Calibration screen | `renderer/onboarding/` | Yoğunluk seçimi |
| System tray | `main/tray.ts` | İkon + sağ tık menü |
| Window manager | `main/window-manager.ts` | Pencere oluşturma/yönetimi |
| i18n sistemi | `locales/tr.json`, `locales/en.json` | Tüm stringler çevrilebilir |
| Resource guard (Electron) | `main/` | RAM/CPU monitoring |
| **Faz 5 testi** | — | Tam oynanabilir alpha, baştan sona 35 dk |

**Test:** 3 farklı kişiyle alpha test, her biri farklı yol

---

### Faz 6: Polish & Package (Hafta 11-12)

**Hedef:** Release candidate. Paketlenmiş .exe, tüm buglar düzeltilmiş.

| Görev | Dosya(lar) | Çıktı |
|-------|-----------|-------|
| Bug fixing | — | Alpha'dan gelen tüm hatalar |
| Performance optimization | — | RAM < 400MB, CPU < 50% |
| Ses tasarımı finalizasyonu | `assets/audio/` | Tüm drone/sfx/stinger dosyaları |
| PyInstaller sidecar | `installer/` | Python → tek binary |
| Electron-builder | `electron-builder.yml` | Electron → paket |
| Installer oluşturma | `installer/build.ps1` | Setup.exe veya portable |
| README yazımı | `README.md` | Kurulum + kullanım kılavuzu |
| Doküman finalizasyonu | `docs/` | Mimari, AI, hikaye, efekt dokümanları |
| **Faz 6 testi** | — | 5 farklı kişiyle beta test, installer test |

---

## 9. V1'den V2'ye Ders Haritası (Hızlı Referans)

| V1 Hatası | V2 Çözümü | Kontrol Noktası |
|-----------|-----------|-----------------|
| PyQt6 + GDI çakışması | Electron overlay (tek render pipeline) | Faz 4'te efekt testi |
| Singleton'lar | Constructor injection, no global state | Her modül testinde kontrol |
| God object Kernel | Director + EventBus + Session ayrımı | Faz 3'te Director testi |
| pyttsx3 COM hataları | Edge-TTS (async, stabil) | Faz 4'te TTS testi |
| Kırık notification | Native Win32 Toast API | Faz 4'te notification testi |
| Act 1 boşluğu | 30s'de ilk ipucu, 5dk'da chat | Faz 5'te pacing testi |
| Lineer hikaye | 3 yol dallanması + farklı finaller | Faz 3'te narrative testi |
| Yüzeysel AI | 3 katmanlı bellek + kişilik evrimi | Faz 2'de memory testi |
| Hardcoded stringler | `locales/*.json` i18n | Her fazda kontrol |
| Test edilemez kod | Interface + DI + pytest | Her fazda birim test |

---

## 10. Bağımlılıklar (Kesin Liste)

### Python Backend

```
# pyproject.toml / requirements.txt
google-generativeai>=0.8.0    # Gemini API
edge-tts>=6.1.0               # Microsoft Edge TTS
websockets>=12.0              # WebSocket server
pydantic>=2.0                 # Config + validation
pydantic-settings>=2.0        # Environment-aware config
aiosqlite>=0.19.0             # Async SQLite
pywin32>=306                  # Windows API (ctypes alternatifi)
psutil>=5.9                   # Resource monitoring
pyyaml>=6.0                   # YAML config loader
pytest>=8.0                   # Testing
pytest-asyncio>=0.23          # Async test desteği
```

### Electron Frontend

```json
// package.json
{
  "dependencies": {
    "electron": "^30.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

> [!NOTE]
> Bu plan **kesin ve final**dir. Tüm teknoloji kararları, mimari tasarım, hikaye akışı, efekt sistemi, güvenlik protokolleri ve geliştirme fazları belirlenmiştir. Belirsizlik sıfırdır. Onay sonrası Faz 1 ile geliştirmeye başlanacaktır.
