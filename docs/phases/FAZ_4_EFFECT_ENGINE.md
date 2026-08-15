# SENTIENT_OS v2 — Faz 4: Effect Engine + Audio (Hafta 7-8)

> **Hedef:** Tüm efektler Electron'da çalışır, ses sistemi aktif, TTS konuşur.  
> **Süre:** 2 hafta  
> **Ön Koşul:** Faz 3 tamamlanmış (hikaye motoru, director, timeline)

---

## Faz Özeti

Bu fazda Electron renderer tarafındaki tüm efektleri, ses motorunu ve TTS entegrasyonunu tamamlıyoruz. Ayrıca Python tarafındaki Win32 operasyonları (mouse drift, wallpaper, brightness) da bu fazda yazılır. Faz 4 sonunda Python'dan gelen efekt komutları Electron'da gerçek zamanlı render edilir.

---

## Görev Listesi

### 4.1. Overlay Efekt Motoru

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/engine.js` | Efekt render motoru — tüm efektleri koordine eder |

**Sorumluluklar:**
- WS'den gelen efekt komutlarını almak
- Priority kuyruğu yönetimi (critical > high > normal > low)
- Efekt zamanlaması (delay_ms)
- Efekt zinciri çalıştırma (effect_chain)
- Aktif efekt takibi ve temizleme

**Interface:**
```javascript
class EffectEngine {
    constructor(wsClient) { ... }
    
    enqueue(effectCommand, priority) { ... }
    executeChain(chainPayload) { ... }
    stopAll() { ... }
    reduceIntensity(factor) { ... }
}
```

**Kabul Kriteri:** Python'dan gelen her efekt komutu doğru sıra ve zamanlamada render edilir.

---

### 4.2. Glitch Efekti

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/effects/glitch.js` | Ekran bozulma efekti |

**Desteklenen Tipler:**
- `tear` — Yatay çizgiler kayar (clip-path + translateX)
- `static` — TV karıncalanması (Canvas noise)
- `invert` — Renk tersine (filter: invert)
- `desaturate` — Renkler solar (filter: grayscale)
- `rgb_split` — RGB kanalları ayrılır (3 katmanlı offset)
- `scanlines` — CRT tarama çizgileri (CSS gradient)

**Intensity → Parametre Mapping:**
```javascript
// intensity 0.0-1.0 range
tear:       sliceCount = 2 + intensity * 20, maxOffset = intensity * 50px
static:     coverage = intensity, pixelSize = 5 - intensity * 4
rgb_split:  channelOffset = intensity * 10px
```

**Kabul Kriteri:** Her tip ve intensity seviyesi görsel olarak doğru çalışır.

---

### 4.3. Text Overlay Efekti

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/effects/text-overlay.js` | Ekranda animasyonlu metin |

**Desteklenen Stiller:** `normal`, `ghostly`, `glitched`, `bloody`, `terminal`, `whisper`

**Desteklenen Animasyonlar:** `fade_in_out`, `typewriter`, `glitch_in`, `dissolve`, `shake`

**Her Stil İçin CSS:**
- `ghostly` — opacity 0.3, blur 0.5px, soğuk mavi renk
- `glitched` — monospace, yeşil, titreyen animasyon
- `bloody` — serif font, koyu kırmızı, text-shadow glow
- `terminal` — monospace, yeşil, glow efekti
- `whisper` — küçük, italik, çok düşük opacity

**Kabul Kriteri:** Her stil + animasyon kombinasyonu görsel olarak doğru çalışır.

---

### 4.4. Fade Efekti

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/effects/fade.js` | Ekran kararma/aydınlanma |

**Sorumluluklar:**
- Overlay div'i üzerinden tam ekran renk katmanı
- Smooth CSS transition ile opacity değişimi
- Farklı renk desteği (#000, #ff0000, #fff)
- Parlama efekti (opacity > 1.0 → beyaz flash)

**Kabul Kriteri:** Kararma, aydınlanma, kırmızı flash ve beyaz flash sorunsuz çalışır.

---

### 4.5. Shake Efekti

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/effects/shake.js` | Ekran sarsıntısı |

**Sorumluluklar:**
- `document.body.style.transform` ile rastgele offset
- 50ms frame aralığı
- Intensity → max offset mapping (0.0 → 0px, 1.0 → 15px)
- Efekt bittiğinde transform reset

**Kabul Kriteri:** Farklı intensity seviyelerinde ekran sallanır, bittiğinde normale döner.

---

### 4.6. Fake BSOD

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/overlay/effects/bsod.js` | Sahte mavi ekran |

**Sorumluluklar:**
- Windows 11 BSOD replikası (HTML/CSS)
- Üzgün yüz `:(`  + hata kodu + sahte QR
- ESC ile çıkılabilir
- Maks 10 saniye timeout

**Kabul Kriteri:** Gerçekçi BSOD belirir ve zamanında kaybolur.

---

### 4.7. Ambient Ses Motoru

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/audio/ambient-engine.js` | Web Audio API ambient ses motoru |

**Sorumluluklar:**
- Mood bazlı drone loop yönetimi (calm, tense, intimate, hostile, dread, silence)
- Crossfade geçişi (varsayılan 5 saniye)
- Volume kontrol
- Birden fazla ses katmanı desteği (base drone + ek katman)

**Mood → Audio Mapping:**

| Mood | Base Drone | Ek Katman | Volume |
|------|-----------|-----------|--------|
| `calm` | low_hum.wav | — | 0.15 |
| `tense` | static_noise.wav | whispers.wav (düşük) | 0.25 |
| `intimate` | — | breath.wav | 0.20 |
| `hostile` | low_hum.wav (pitch shift) | heartbeat.wav | 0.35 |
| `dread` | infrasound.wav | — | 0.40 |
| `silence` | — | — | 0.00 |

**Kabul Kriteri:** Mood değişiminde 5 saniyelik crossfade, volume doğru.

---

### 4.8. SFX ve Stinger Player

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/audio/spatial-audio.js` | Stereo konumlandırma + SFX oynatma |

**Sorumluluklar:**
- Kısa ses efektlerini çalma (click, glitch_short, notification, breath vb.)
- Stereo konumlandırma (left, center, right) — Web Audio API `StereoPannerNode`
- Stinger çalma (1-3 saniyelik dramatik sesler)
- Volume kontrol

**Kabul Kriteri:** SFX doğru stereo konumda çalar, stinger ambient'i kesmeden üstüne çalar.

---

### 4.9. Edge-TTS Worker (Python)

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/edge_tts.py` | Async TTS üretim worker |

**Sorumluluklar:**
- `edge-tts` kütüphanesi ile async MP3 üretim
- Ses profilleri: Normal, Sinister, Whisper, Panicked, Sad
- Rate/pitch ayarları
- Temp dosya yönetimi (`temp/tts_{uuid}.mp3`)
- Üretim kuyruğu (aynı anda 1 TTS, geri kalanı bekler)

**Kabul Kriteri:** `generate_speech("Merhaba")` → `temp/tts_xxx.mp3` dosyası oluşur, doğal Türkçe ses.

---

### 4.10. TTS Player (Electron)

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/audio/tts-player.js` | TTS MP3 oynatma |

**Sorumluluklar:**
- Python'dan gelen `tts_play` komutunu işleme
- MP3 dosyasını Web Audio API ile çalma
- Çalma sırasında ambient volume'u düşürme (%30)
- Çalma bittiğinde ambient'i geri yükseltme
- Dosya oynatıldıktan sonra Python'a `effect_completed` gönderme

**Kabul Kriteri:** TTS sesi doğal çalar, ambient otomatik alçalıp yükselir.

---

### 4.11. Win32 Operasyonları (Python)

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/platform/windows/mouse.py` | Fare manipülasyonu |
| `src/infrastructure/platform/windows/wallpaper.py` | Duvar kağıdı ops |
| `src/infrastructure/platform/windows/brightness.py` | Parlaklık ops |
| `src/infrastructure/platform/windows/notifications.py` | Native bildirim |
| `src/infrastructure/platform/windows/keyboard.py` | Klavye hook |

**mouse.py:**
- `drift(intensity, duration_ms)` — sinüzoidal kayma
- `freeze(duration_ms)` — ClipCursor ile sınırlama (maks 5s)
- DPI-aware koordinatlar (SetProcessDpiAwareness)

**wallpaper.py:**
- `save_original()` — mevcut wallpaper'ı kaydet
- `apply_effect(effect)` — darken/glitch/invert
- `restore()` — orijinali geri yükle
- SystemParametersInfoW API

**brightness.py:**
- WMI üzerinden parlaklık okuma/yazma
- Minimum 0.2 (tamamen karartma engeli)
- Orijinal değer kaydetme/geri yükleme

**notifications.py:**
- Electron overlay üzerinden render (gerçek Windows API değil — tam kontrol)
- Windows 11 toast notification replikası

**keyboard.py:**
- `ctypes` `SetWindowsHookEx` ile düşük seviye hook
- Panic detection (ESC spam, Alt+F4 sayacı)
- Director'a olay bildirimi

**Kabul Kriteri:** Her Win32 operasyonu çalışır ve oturum sonunda restore edilir.

---

## Ses Dosyaları (Assets)

Bu fazda ihtiyaç duyulan ses dosyaları:

| Dosya | Süre | Açıklama |
|-------|------|----------|
| `drones/low_hum.wav` | loop | Düşük frekanslı hum |
| `drones/static_noise.wav` | loop | Statik/parazit |
| `drones/whispers.wav` | loop | Hafif fısıltılar |
| `drones/heartbeat.wav` | loop | Kalp atışı |
| `drones/infrasound.wav` | loop | 20Hz infrasound |
| `sfx/click.wav` | <1s | Mekanik tık |
| `sfx/glitch_short.wav` | <1s | Kısa dijital bozulma |
| `sfx/notification.wav` | <1s | Windows bildirim sesi |
| `sfx/breath.wav` | 2s | Nefes alma |
| `sfx/keyboard_type.wav` | 1s | Klavye tıklama |
| `sfx/static_burst.wav` | <1s | Statik patlama |
| `sfx/whisper.wav` | 1s | Fısıltı |
| `stingers/reveal.wav` | 2s | Dramatik ortaya çıkma |
| `stingers/crisis_hit.wav` | 2s | Darbe hissi |
| `stingers/silence_break.wav` | 1s | Sessizlik kırıcı |

> **Not:** Ses dosyaları ücretsiz kaynaklardan (freesound.org, pixabay.com/sound-effects) temin edilecek veya Web Audio API ile prosedürel olarak üretilecek.

---

## Test Planı

| Test | Ne Test Eder |
|------|-------------|
| **Manuel efekt testi** | Her efekti tek tek tetikleyen Python script'i |
| **Ses testi** | Her mood'u 5 saniyelik crossfade ile test |
| **TTS testi** | 5 farklı cümle, 3 farklı profil |
| **Win32 testi** | Mouse drift → restore, wallpaper → restore, brightness → restore |
| **10 dk playthrough** | Katman 1 tam akış + Katman 2 giriş (5 dk + 5 dk) |

---

## Faz 4 Çıkış Kriterleri

- [ ] Tüm 6 glitch tipi çalışır (tear, static, invert, desaturate, rgb_split, scanlines)
- [ ] Tüm 6 text overlay stili çalışır (normal, ghostly, glitched, bloody, terminal, whisper)
- [ ] Tüm 5 animasyon çalışır (fade_in_out, typewriter, glitch_in, dissolve, shake)
- [ ] Fade efekti çalışır (kararma, aydınlanma, kırmızı flash, beyaz flash)
- [ ] Shake efekti çalışır (3 farklı intensity)
- [ ] Fake BSOD çalışır (ESC ile çıkılabilir)
- [ ] Ambient ses motoru çalışır (6 mood, crossfade)
- [ ] SFX ve stinger çalar (stereo konumlandırma)
- [ ] Edge-TTS Türkçe konuşur (5 farklı profil)
- [ ] TTS sırasında ambient volume düşer, sonra yükselir
- [ ] Mouse drift/freeze çalışır ve restore edilir
- [ ] Wallpaper değişir ve restore edilir
- [ ] Brightness değişir ve restore edilir
- [ ] Efekt kuyruğu priority sıralaması doğru
- [ ] Efekt zinciri (effect_chain) doğru zamanlamada çalışır
- [ ] 10 dk playthrough sorunsuz
