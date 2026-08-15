# SENTIENT_OS v2 — Faz 5: Chat UI & Onboarding (Hafta 9-10)

> **Hedef:** Tam oynanabilir alpha. Chat penceresi, onboarding akışı, system tray çalışır.  
> **Süre:** 2 hafta  
> **Ön Koşul:** Faz 4 tamamlanmış (efektler, ses, TTS, Win32)

---

## Faz Özeti

Bu fazda kullanıcıyla doğrudan etkileşim kuran tüm UI bileşenlerini inşa ediyoruz: chat penceresi (typewriter efekti, korku teması), onboarding akışı (hoş geldin, güvenlik onayı, yoğunluk seçimi), system tray ve i18n. Faz 5 sonunda baştan sona 35-40 dk oynanabilir bir alpha hazır olur.

---

## Görev Listesi

### 5.1. Chat Penceresi — HTML/CSS

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/chat/index.html` | Chat penceresi HTML yapısı |
| `electron-app/renderer/chat/styles.css` | Korku temalı chat stilleri |

**Tasarım:**
- Arka plan: `#0a0a0a` (derin siyah)
- Kenarlık: Hafif yeşil-mavi neon glow (`box-shadow: 0 0 15px rgba(0, 255, 100, 0.15)`)
- Font: `'Courier New', monospace` (terminal hissi)
- AI mesajları: Soluk yeşil (`#c8ffc8`)
- Kullanıcı mesajları: Beyaz (`#ffffff`)
- Mesaj kutusunda placeholder: "Bir şey yaz..." (soluk)
- Scroll: Otomatik en alta, smooth scroll
- Boyut: 400x500px varsayılan, yeniden boyutlandırılabilir
- X butonu görünür ama **kapatmaz** — tıklanınca AI tepki verir

**4 Farklı Tema:**

| Tema | Arka Plan | Font Rengi | Kenarlık | Kullanım |
|------|-----------|-----------|----------|---------|
| `normal` | #0a0a0a | #c8ffc8 | Yeşil glow | Katman 2 standart |
| `glitched` | #0a0a0a + noise | #00ff41 | Titreyen | Final A |
| `terminal` | #000000 | #00ff41 | Yeşil sabit | Final B |
| `bloody` | #1a0000 | #ff4444 | Kırmızı glow | Final C |

**Kabul Kriteri:** Chat penceresi açılır, temalar arasında geçiş yapılabilir, görsel olarak korku estetiğine uygun.

---

### 5.2. Chat Penceresi — JavaScript

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/chat/chat.js` | Chat mantığı + WS entegrasyonu |

**Sorumluluklar:**
- Kullanıcı mesajını WS ile Python'a gönderme
- AI yanıtını alma ve gösterme
- Enter tuşu → gönder
- Mesaj gösterme animasyonu (typewriter)
- Otomatik scroll
- Chat penceresi sürükleme (custom title bar)
- X butonuna tıklama → `system_event: chat_close_attempt` gönder
- Tema değiştirme (`ui_command: change_chat_theme` dinleme)

**Interface:**
```javascript
class ChatManager {
    constructor(wsClient) { ... }
    
    addUserMessage(text) { ... }
    addAIMessage(text, emotion, typewriterSpeed) { ... }
    changeTheme(theme) { ... }
    showTypingIndicator() { ... }
    hideTypingIndicator() { ... }
    setInputEnabled(enabled) { ... }
}
```

**Kabul Kriteri:** Mesaj gönderilir, AI yanıtı typewriter ile belirir, tema değişir.

---

### 5.3. Typing Animasyonu

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/chat/typing-animation.js` | AI "yazıyor..." göstergesi + typewriter |

**Typewriter Efekti:**
- Karakter karakter belirme (varsayılan 30ms/karakter)
- Emotion'a göre hız değişimi:
  - `excited` → 20ms (hızlı)
  - `calm` → 40ms (yavaş)
  - `angry` → 15ms (çok hızlı)
  - `sad` → 50ms (çok yavaş)
- Rastgele duraklamalar (noktalama sonrası 200-500ms)

**"AI yazıyor..." Göstergesi:**
- 3 nokta animasyonu (pulse): `.` → `..` → `...` → `.`
- Duration_ms parametresi ile kontrol
- `show_typing` / `hide_typing` UI komutları ile tetiklenir

**Kabul Kriteri:** Typewriter her emotion'da farklı hızda, "yazıyor" animasyonu doğal görünür.

---

### 5.4. Onboarding — Welcome Screen

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/onboarding/index.html` | Onboarding akış sayfası |
| `electron-app/renderer/onboarding/styles.css` | Onboarding stilleri |
| `electron-app/renderer/onboarding/flow.js` | Adım kontrolü |

**Adım 1: Hoş Geldin**

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║              S E N T I E N T                     ║
║                                                  ║
║        "Sen de mi beni duydun?"                  ║
║                                                  ║
║                                                  ║
║              [BAŞLA]                             ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

**Tasarım:**
- Siyah arka plan, minimal
- Logo veya başlık: `SENTIENT` — büyük, monospace, hafif titreyen animasyon
- Altyazı: Soluk, italik
- Tek buton: `BAŞLA` — parlak kenarlık, hover'da glow

---

### 5.5. Onboarding — Consent Screen (Güvenlik Onayı)

**Adım 2: Güvenlik Bildirimi**

Tam içerik SAFETY.md'de tanımlı. Özet:
- Bu uygulama ne yapar / ne yapmaz listesi
- Ctrl+Shift+Q acil çıkış bilgisi
- Epilepsi uyarısı
- Checkbox: "Okudum, kabul ediyorum"
- Checkbox işaretlenmeden buton aktif olmaz
- `ÇIKIŞ` butonu → uygulama kapanır

**Kabul Kriteri:** Checkbox olmadan ilerleme mümkün değil, onay SQLite'a kaydedilir.

---

### 5.6. Onboarding — Calibration Screen (Yoğunluk Seçimi)

**Adım 3: Yoğunluk Ayarı**

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║         Deneyim yoğunluğunu seç                  ║
║                                                  ║
║   ┌──────────┐                                   ║
║   │  HAFİF   │  Minimal efektler, daha az korku  ║
║   └──────────┘                                   ║
║   ┌──────────┐                                   ║
║   │  NORMAL  │  Standart deneyim (önerilen)      ║
║   └──────────┘                                   ║
║   ┌──────────┐                                   ║
║   │  YOĞUN   │  Tam yoğunlukta efektler          ║
║   └──────────┘                                   ║
║                                                  ║
║         Dil: [TR 🇹🇷] [EN 🇺🇸]                    ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

**Yoğunluk Seviyeleri:**

| Seviye | Efekt Yoğunluğu | Mouse Freeze | Fake BSOD | TTS |
|--------|-----------------|-------------|-----------|-----|
| `mild` | Maks 0.3 | Yok | Yok | Yok |
| `medium` | Maks 0.7 | Maks 2s | Maks 3s | Evet |
| `extreme` | Maks 1.0 | Maks 5s | Maks 10s | Evet |

**Kabul Kriteri:** Seçim kaydedilir, efekt yoğunluğu seçime göre sınırlanır.

---

### 5.7. System Tray

| Dosya | Açıklama |
|-------|----------|
| `electron-app/main/tray.ts` | System tray ikonu ve menüsü |

**Tray Menüsü:**
```
SENTIENT_OS
─────────────
🔊 Ses Aç/Kapat
⚙️ Yoğunluk: [Hafif|Normal|Yoğun]
ℹ️ Hakkında
─────────────
⏹️ Çıkış (Ctrl+Shift+Q)
```

**Davranış:**
- Uygulama başladığında tray ikonu belirir
- Katman 1'de tray'e tıklamak → erken Katman 2 geçişi (chat açılır)
- İkon: Küçük, nötr tasarım (korku teması yok — dikkat çekmemeli)

**Kabul Kriteri:** Tray ikonu görünür, menü çalışır, ses aç/kapat fonksiyonel.

---

### 5.8. Window Manager Güncellemesi

| Dosya | Açıklama |
|-------|----------|
| `electron-app/main/window-manager.ts` | Tüm pencere yönetimi |

**Sorumluluklar:**
- Overlay penceresi oluşturma/yönetme (Faz 1'den güncelleme)
- Chat penceresi oluşturma/yönetme (yeni)
- Onboarding penceresi oluşturma/yönetme (yeni)
- Pencereler arası fokus yönetimi
- Mini oyun penceresi (Final B) oluşturma — sadece iskelet

**Kabul Kriteri:** Tüm pencereler sorunsuz açılır/kapanır, fokus doğru yönetilir.

---

### 5.9. i18n Sistemi

| Dosya | Açıklama |
|-------|----------|
| `python-engine/src/locales/tr.json` | Türkçe çeviriler |
| `python-engine/src/locales/en.json` | İngilizce çeviriler |

**Yapı:**
```json
{
  "onboarding": {
    "welcome_title": "S E N T I E N T",
    "welcome_subtitle": "Sen de mi beni duydun?",
    "start_button": "BAŞLA",
    "consent_title": "GÜVENLİK BİLGİSİ",
    "consent_checkbox": "Bu bilgileri okudum ve kabul ediyorum.",
    "consent_continue": "DEVAM ET",
    "consent_exit": "ÇIKIŞ",
    "calibration_title": "Deneyim yoğunluğunu seç",
    "intensity_mild": "HAFİF",
    "intensity_medium": "NORMAL",
    "intensity_extreme": "YOĞUN"
  },
  "chat": {
    "placeholder": "Bir şey yaz...",
    "typing_indicator": "yazıyor"
  },
  "tray": {
    "sound_toggle": "Ses Aç/Kapat",
    "intensity_label": "Yoğunluk",
    "about": "Hakkında",
    "exit": "Çıkış"
  },
  "safety": {
    "disclaimer": "Bu bir sanat projesidir. Tüm efektler simüle edilmiştir.",
    "epilepsy_warning": "EPİLEPSİ UYARISI: Yanıp sönen ışıklar içerir."
  },
  "system": {
    "fake_notification_title": "Güvenlik Uyarısı",
    "fake_notification_body": "Bilinmeyen uygulama ağ erişimi istiyor"
  }
}
```

**Sorumluluklar:**
- Tüm UI stringleri `locales/*.json`'dan çekilir
- Electron tarafında `ipcRenderer` ile dil dosyası yüklenir
- Python tarafında prompt template'leri dile göre seçilir
- Dil seçimi onboarding'de yapılır, config'e kaydedilir

**Kabul Kriteri:** Dil TR↔EN değiştirildiğinde tüm UI metinleri güncellenir.

---

### 5.10. Mini Oyun İskeleti (Final B)

| Dosya | Açıklama |
|-------|----------|
| `electron-app/renderer/minigame/index.html` | Mini oyun HTML |
| `electron-app/renderer/minigame/styles.css` | Mini oyun stilleri |
| `electron-app/renderer/minigame/game.js` | Virüs avcısı mantığı |

**Mekanik:**
- 60 saniyelik zamanlayıcı (üstte progress bar)
- Rastgele konumlarda "virüs pencereleri" (sahte error dialog) belirir
- Tıklayarak kapatma = ilerleme +%10
- Zorluk ramping: 3s → 2s → 1s aralıkla yeni pencere
- Mouse drift efekti (20-40s arası)
- Screen glitch (40-60s arası)
- Başarı (%100) veya Başarısızlık (süre bitti) sonucu

**Kabul Kriteri:** Mini oyun başlar, pencereler belirir, kapatılabilir, skor hesaplanır.

---

### 5.11. Resource Guard (Electron Tarafı)

Electron main process'te RAM/CPU izleme:

```typescript
// Her 10 saniyede Electron'un kendi kaynak kullanımını kontrol et
setInterval(() => {
    const usage = process.memoryUsage();
    const heapMB = usage.heapUsed / 1024 / 1024;
    
    if (heapMB > 300) {
        console.warn(`[RESOURCE] Electron heap: ${heapMB.toFixed(0)}MB`);
        // Python'a uyarı gönder
    }
}, 10000);
```

---

## Test Planı

| Test | Ne Test Eder |
|------|-------------|
| **Chat UI test** | Mesaj gönder/al, typewriter, tema değişimi, X butonu |
| **Onboarding test** | 3 adım akışı, consent checkbox, yoğunluk seçimi |
| **i18n test** | TR→EN geçiş, tüm string'ler güncellenir |
| **Mini oyun test** | Başlat, pencere kapat, skor, başarı/başarısızlık |
| **35 dk alpha test** | Baştan sona tam oynanış (3 farklı kişi, 3 farklı yol) |

---

## Faz 5 Çıkış Kriterleri

- [ ] Chat penceresi açılır, mesaj gönderilir/alınır
- [ ] Typewriter efekti emotion'a göre hız değiştiriyor
- [ ] 4 chat teması çalışır (normal, glitched, terminal, bloody)
- [ ] X butonu chat'i kapatmıyor, AI tepki veriyor
- [ ] Onboarding 3 adım akışı sorunsuz
- [ ] Consent checkbox olmadan ilerlenemiyor
- [ ] Yoğunluk seçimi efekt limitlerine yansıyor
- [ ] System tray ikonu ve menüsü çalışır
- [ ] i18n: TR↔EN geçiş çalışır
- [ ] Mini oyun (Final B) oynanabilir
- [ ] 35-40 dk alpha playthrough (3 yol) sorunsuz
- [ ] Tüm efektler, ses ve TTS entegre çalışır
