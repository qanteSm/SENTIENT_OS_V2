# SENTIENT_OS v2 — Efekt Kataloğu

> **Versiyon:** 1.0  
> **Tarih:** 15 Ağustos 2026  
> **Render Engine:** Electron (Chromium) — CSS/Canvas/WebGL

---

## 1. Efekt Felsefesi

### Temel Kural

> **Her efekt hikayeye bağlı olmalıdır. Rastgele efekt YOKTUR.**

| Yaklaşım | V1 | V2 |
|-----------|----|----|
| Tetikleyici | Zamanlayıcı / rastgele | AI kararı / hikaye anı |
| Amaç | "Korkut" | "Hissettir" |
| Yoğunluk | Sabit | Dinamik — duyguya bağlı |
| Restore | Manuel InvalidateRect | Otomatik CSS/Canvas reset |

### Efekt-Duygu Eşleme

| AI Emotion | Uygun Efektler | Uygunsuz Efektler |
|------------|---------------|-------------------|
| `curious` | overlay_text (soluk), mouse_drift | screen_glitch, fake_bsod |
| `amused` | overlay_text (eğlenceli) | — |
| `hurt` | screen_fade (kararma), ambient_shift | screen_shake, fake_bsod |
| `angry` | screen_glitch, screen_shake, play_stinger | fade, mouse_drift |
| `calm` | — (minimal efekt) | Agresif efektler |
| `sinister` | mouse_drift, overlay_text (tehditkar), ambient_shift | — |
| `sad` | screen_fade, ambient_shift (melankolik) | glitch, shake |
| `excited` | screen_fade (parlama), play_sfx | — |

---

## 2. Görsel Efektler

### 2.1. `overlay_text`

**Açıklama:** Ekranda yarı saydam metin gösterir.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `text` | string | (zorunlu) | Gösterilecek metin |
| `position` | enum | `"center"` | `center`, `top`, `bottom`, `top_left`, `top_right`, `bottom_left`, `bottom_right`, `random` |
| `style` | enum | `"normal"` | `normal`, `ghostly`, `glitched`, `bloody`, `terminal`, `whisper` |
| `duration_ms` | int | 3000 | Görünür kalma süresi |
| `animation` | enum | `"fade_in_out"` | `fade_in_out`, `typewriter`, `glitch_in`, `dissolve`, `shake` |
| `font_size` | string | `"2rem"` | CSS font boyutu |
| `color` | string | `"#ffffff"` | CSS renk |
| `opacity` | float | 0.8 | 0.0-1.0 |

**Stil Tanımları:**

```css
/* normal */
.overlay-text--normal {
  font-family: 'Inter', sans-serif;
  color: white;
  text-shadow: 0 0 10px rgba(255,255,255,0.5);
}

/* ghostly — çok soluk, neredeyse görünmez */
.overlay-text--ghostly {
  font-family: 'Inter', sans-serif;
  color: rgba(200, 220, 255, 0.3);
  text-shadow: 0 0 20px rgba(200, 220, 255, 0.1);
  filter: blur(0.5px);
}

/* glitched — bozuk, titreyen */
.overlay-text--glitched {
  font-family: 'Courier New', monospace;
  color: #00ff41;
  animation: glitch-text 0.1s infinite;
}

/* bloody — kırmızı, akan */
.overlay-text--bloody {
  font-family: 'Creepster', cursive;
  color: #8b0000;
  text-shadow: 0 0 10px #ff0000, 0 2px 4px #8b0000;
}

/* terminal — hacker/matrix */
.overlay-text--terminal {
  font-family: 'Courier New', monospace;
  color: #00ff41;
  text-shadow: 0 0 5px #00ff41;
}

/* whisper — küçük, soluk, altta */
.overlay-text--whisper {
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.2);
  font-style: italic;
}
```

---

### 2.2. `screen_glitch`

**Açıklama:** Ekranı çeşitli şekillerde bozar.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `intensity` | float | 0.5 | 0.0-1.0 — bozulma şiddeti |
| `duration_ms` | int | 1000 | Efekt süresi |
| `type` | enum | `"tear"` | `tear`, `static`, `invert`, `desaturate`, `rgb_split`, `scanlines` |

**Glitch Tipleri:**

| Tip | Açıklama | CSS/Canvas Tekniği |
|-----|----------|-------------------|
| `tear` | Yatay çizgiler kayar | `clip-path` + `transform: translateX` animasyonu |
| `static` | TV karıncalanması | Canvas noise pattern |
| `invert` | Renk tersine döner | `filter: invert(1)` |
| `desaturate` | Renkler solar | `filter: grayscale(intensity)` |
| `rgb_split` | RGB kanalları ayrılır | 3 katmanlı `mix-blend-mode` + offset |
| `scanlines` | CRT tarama çizgileri | CSS gradient overlay |

**Intensity Mapping:**

```javascript
// intensity 0.0-1.0 → efekt parametrelerine çevrilir
function mapIntensity(intensity, type) {
    switch(type) {
        case 'tear':
            return {
                sliceCount: Math.floor(intensity * 20) + 2,  // 2-22 dilim
                maxOffset: intensity * 50,  // 0-50px kayma
            };
        case 'static':
            return {
                coverage: intensity,  // 0-100% ekran
                pixelSize: Math.max(1, 5 - intensity * 4),  // 5-1px
            };
        case 'rgb_split':
            return {
                offset: intensity * 10,  // 0-10px kanal ayrımı
            };
    }
}
```

---

### 2.3. `screen_fade`

**Açıklama:** Ekranı karartır veya aydınlatır.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `target_opacity` | float | 0.5 | 0.0 (tam siyah) – 1.0 (normal) – 1.2 (parlak) |
| `duration_ms` | int | 3000 | Geçiş süresi |
| `color` | string | `"#000000"` | Fade rengi |

**Kullanım Örnekleri:**

```javascript
// Ekranı %50 karart (3 saniyede)
{ type: "screen_fade", params: { target_opacity: 0.5, duration_ms: 3000, color: "#000" }}

// Ekranı tamamen karart
{ type: "screen_fade", params: { target_opacity: 0.0, duration_ms: 5000, color: "#000" }}

// Kırmızı flash
{ type: "screen_fade", params: { target_opacity: 0.7, duration_ms: 200, color: "#ff0000" }}

// Normale dön
{ type: "screen_fade", params: { target_opacity: 1.0, duration_ms: 2000, color: "#000" }}
```

---

### 2.4. `screen_shake`

**Açıklama:** Ekranı sarsar.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `intensity` | float | 0.3 | 0.0-1.0 — sarsıntı şiddeti |
| `duration_ms` | int | 500 | Sarsıntı süresi |

**Implementasyon:**

```javascript
function shake(intensity, durationMs) {
    const maxOffset = intensity * 15;  // 0-15px
    const interval = 50;  // 50ms per frame
    const frames = durationMs / interval;
    
    for (let i = 0; i < frames; i++) {
        setTimeout(() => {
            const x = (Math.random() - 0.5) * maxOffset * 2;
            const y = (Math.random() - 0.5) * maxOffset * 2;
            document.body.style.transform = `translate(${x}px, ${y}px)`;
        }, i * interval);
    }
    
    setTimeout(() => {
        document.body.style.transform = 'none';
    }, durationMs);
}
```

---

### 2.5. `fake_bsod`

**Açıklama:** Sahte Windows mavi ekranı gösterir.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `error_code` | string | `"SENTIENT_VIOLATION"` | Hata kodu metni |
| `duration_ms` | int | 5000 | BSOD görünme süresi |

**Tasarım:** Gerçek Windows 11 BSOD'ye birebir benzer HTML/CSS. Üzgün yüz `:(`  + QR kodu + hata kodu.

---

### 2.6. `fake_file_appear`

**Açıklama:** Masaüstünde sahte bir dosya/klasör ikonu belirir ve kaybolur.

**Parametreler:**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `filename` | string | (zorunlu) | Dosya adı |
| `location` | enum | `"desktop"` | `desktop`, `random` |
| `duration_ms` | int | 3000 | Görünür kalma süresi |

**Implementasyon:** Overlay penceresi üzerinde Windows dosya ikonu + isim render edilir. Gerçek dosya sistemi değişmez.

---

## 3. Sistem Efektleri

### 3.1. `mouse_drift`

**Açıklama:** Fare imlecini hafifçe kaydırır.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `intensity` | float | 0.1 | 0.0-1.0 — kayma miktarı |
| `duration_ms` | int | 500 | Kayma süresi |

**Implementasyon:** Python backend `ctypes` ile `SetCursorPos` çağırır. Küçük, sinüzoidal hareket.

### 3.2. `mouse_freeze`

**Açıklama:** Fare imlecini geçici olarak dondurur.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `duration_ms` | int | 2000 | Donma süresi |

**Güvenlik:** Maksimum 5 saniye. Kill switch her zaman aktif.

### 3.3. `wallpaper_change`

**Açıklama:** Masaüstü duvar kağıdını değiştirir.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `effect` | enum | `"darken"` | `darken`, `glitch`, `invert`, `original` |

**Restore:** Orijinal wallpaper her zaman kaydedilir, oturum sonunda geri yüklenir.

### 3.4. `brightness_shift`

**Açıklama:** Ekran parlaklığını değiştirir.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `target` | float | 0.5 | 0.0-1.0 — hedef parlaklık |
| `duration_ms` | int | 2000 | Geçiş süresi |

**Restore:** Orijinal parlaklık kaydedilir, oturum sonunda geri yüklenir.

### 3.5. `system_clock_shift`

**Açıklama:** Overlay üzerinde saatin kaymış gibi gösterilmesi. **Gerçek sistem saati DEĞİŞMEZ.**

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `offset_seconds` | int | -60 | Saat kayması (saniye) |

### 3.6. `fake_notification`

**Açıklama:** Sahte Windows bildirimi gösterir.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `title` | string | (zorunlu) | Bildirim başlığı |
| `body` | string | (zorunlu) | Bildirim metni |
| `icon_type` | enum | `"warning"` | `info`, `warning`, `error`, `security` |
| `duration_ms` | int | 5000 | Görünme süresi |

**Implementasyon:** Electron overlay üzerinde Windows 11 toast notification replikası. Gerçek Windows notification API değil — tam kontrol için.

### 3.7. `log_message`

**Açıklama:** Sahte bir log dosyası oluşturur veya Notepad'de gösterir.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `text` | string | (zorunlu) | Log mesajı |
| `style` | enum | `"system"` | `system`, `hacker`, `corrupted` |

---

## 4. Ses Efektleri

### 4.1. `ambient_shift`

**Açıklama:** Arka plan ambient ses modunu değiştirir.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `mood` | enum | (zorunlu) | `calm`, `tense`, `intimate`, `hostile`, `dread`, `silence`, `climax_a`, `climax_b`, `climax_c` |
| `fade_ms` | int | 5000 | Crossfade süresi |

### 4.2. `play_sfx`

**Açıklama:** Kısa ses efekti çalar.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `name` | string | (zorunlu) | SFX dosya adı (uzantısız) |
| `volume` | float | 0.5 | 0.0-1.0 |
| `spatial_position` | enum | `"center"` | `left`, `center`, `right` — stereo konumlandırma |

**Mevcut SFX Dosyaları:**

| İsim | Açıklama | Kullanım |
|------|----------|---------|
| `click` | Mekanik tık sesi | Dosya belirmesi |
| `glitch_short` | Kısa dijital bozulma | Glitch efektleriyle |
| `notification` | Windows bildirim sesi | Sahte bildirimlerle |
| `breath` | Nefes alma/verme | Sessizlik kırıcı |
| `keyboard_type` | Klavye tıklama | Log mesajlarıyla |
| `static_burst` | Kısa statik patlama | Screen shake ile |
| `whisper` | Fısıltı ("buradayım") | Katman 1 bilinçaltı |

### 4.3. `play_stinger`

**Açıklama:** Dramatik kısa müzik/ses çalar (1-3 saniye).

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `name` | string | (zorunlu) | Stinger dosya adı |
| `volume` | float | 0.7 | 0.0-1.0 |

**Mevcut Stinger Dosyaları:**

| İsim | Açıklama | Kullanım |
|------|----------|---------|
| `reveal` | Dramatik ortaya çıkma | "SENİ GÖRÜYORUM" anı |
| `crisis_hit` | Darbe/patlama hissi | Katman 3 girişi |
| `silence_break` | Sessizliği kesen tek nota | Uzun sessizlik sonrası |

### 4.4. `tts_speak`

**Açıklama:** Edge-TTS ile konuşma üretir ve çalar.

| Param | Tip | Varsayılan | Açıklama |
|-------|-----|-----------|----------|
| `text` | string | (zorunlu) | Konuşulacak metin |
| `voice` | string | `"tr-TR-AhmetNeural"` | TTS ses profili |
| `rate` | string | `"+0%"` | Konuşma hızı |
| `pitch` | string | `"+0Hz"` | Ses tonu |

---

## 5. UI Komutları

### 5.1. `chat_typing`

Chat penceresinde "AI yazıyor..." gösterir.

| Param | Tip | Varsayılan |
|-------|-----|-----------|
| `duration_ms` | int | 2000 |

### 5.2. `chat_style`

Chat penceresinin görsel temasını değiştirir.

| Param | Tip | Varsayılan |
|-------|-----|-----------|
| `theme` | enum | `"normal"` |

Temalar: `normal`, `glitched`, `terminal`, `bloody`

### 5.3. `open_chat` / `close_chat`

Chat penceresini açar veya kapatır. Parametre yok.

---

## 6. Efekt Zincirleme

Birden fazla efekt sıralı olarak çalıştırılabilir:

```json
{
  "type": "effect_chain",
  "payload": {
    "effects": [
      { "type": "screen_fade", "params": { "target_opacity": 0.0, "duration_ms": 1000 }, "delay_ms": 0 },
      { "type": "play_stinger", "params": { "name": "crisis_hit" }, "delay_ms": 1000 },
      { "type": "overlay_text", "params": { "text": "UYAN", "style": "glitched" }, "delay_ms": 1500 },
      { "type": "screen_glitch", "params": { "intensity": 0.8, "type": "tear" }, "delay_ms": 1500 },
      { "type": "screen_fade", "params": { "target_opacity": 1.0, "duration_ms": 2000 }, "delay_ms": 4000 }
    ]
  }
}
```

`delay_ms` = zincirin başından itibaren bekleme süresi (absolüt, relatif değil).

---

## 7. Güvenlik Kuralları

1. **mouse_freeze** maksimum 5 saniye. Kill switch her zaman aktif.
2. **fake_bsod** maksimum 10 saniye. ESC ile çıkılabilir.
3. **wallpaper_change** → orijinal her zaman kaydedilir, restore garantili.
4. **brightness_shift** → minimum 0.2 (tamamen karartma yok), orijinal restore garantili.
5. **Overlay** → her zaman click-through (efekt anında bile fare kullanılabilir).
6. Gerçek dosya sistemi, registry, sistem saati ASLA değiştirilmez.
7. Tüm efektler oturum sonunda otomatik temizlenir.
