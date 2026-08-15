# SENTIENT_OS v2 — IPC Protokol Dokümanı

> **Versiyon:** 1.0  
> **Tarih:** 15 Ağustos 2026  
> **Protokol:** WebSocket (ws://127.0.0.1:{port})  
> **Format:** JSON

---

## 1. Bağlantı Yaşam Döngüsü

```
Python Engine başlar
    │
    ▼
WSServer dinlemeye başlar (ws://127.0.0.1:{random_port})
    │
    ▼
Port numarasını stdout'a yazar: "WS_PORT:{port}"
    │
    ▼
Electron okur ve bağlanır
    │
    ▼
Handshake: Electron → Python: { type: "handshake", version: "2.0" }
    │
    ▼
Python → Electron: { type: "handshake_ack", status: "ready" }
    │
    ▼
Bağlantı aktif — mesajlaşma başlar
    │
    ...
    │
    ▼
Kapatma: Python → Electron: { type: "shutdown" }
    │
    ▼
Electron kapatır → Python kapatır
```

### Yeniden Bağlanma

Bağlantı koparsa (crash, ağ hatası):
- Electron 1 saniye aralıklarla yeniden bağlanmayı dener (maks 10 deneme)
- 10 denemeden sonra → hata mesajı göster + uygulama kapat
- Python tarafı bağlantı koptuğunda state'i korur ve yeni bağlantı bekler

### ⚠️ Stdout Buffer Uyarısı

> [!WARNING]
> Python port numarasını stdout'a yazarken (`WS_PORT:{port}`) tamponlama (buffering) sebebiyle Electron tarafı portu geç okuyabilir ve bağlantı başarısız olur.

**Çözüm (zorunlu):** Python sürecini başlatırken aşağıdakilerden birini uygulayın:

```python
# Yöntem 1: main.py başında (önerilen)
import sys
sys.stdout.reconfigure(line_buffering=True)

# Yöntem 2: Electron tarafında process spawn ederken
const pythonProcess = spawn('python', ['main.py'], {
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
});
```

Bu yapılmazsa Electron, Python'un port çıktısını okuyamadan timeout alır.

---

## 2. Mesaj Formatı (Genel)

Her mesaj şu yapıya sahiptir:

```json
{
  "type": "string — mesaj tipi",
  "id": "string — benzersiz mesaj ID (uuid4 kısa)",
  "timestamp": 1723758000,
  "payload": { }
}
```

- `type`: Mesaj tipini belirler (aşağıdaki tabloya bakınız)
- `id`: `evt_001`, `msg_042`, `res_042`, `sys_012` gibi prefix + sayı
- `timestamp`: Unix timestamp (saniye)
- `payload`: Mesaj tipine özel veri

---

## 3. Electron → Python Mesajları

### 3.1. `handshake`

Bağlantı kurulduğunda Electron tarafından gönderilir.

```json
{
  "type": "handshake",
  "id": "hs_001",
  "timestamp": 1723758000,
  "payload": {
    "version": "2.0",
    "electron_pid": 12345,
    "platform": "win32"
  }
}
```

### 3.2. `user_input`

Kullanıcının chat'te yazdığı mesaj.

```json
{
  "type": "user_input",
  "id": "msg_042",
  "timestamp": 1723758100,
  "payload": {
    "text": "Sen ne istiyorsun benden?",
    "source": "chat_window"
  }
}
```

### 3.3. `system_event`

Electron'un algıladığı sistem olayları.

```json
{
  "type": "system_event",
  "id": "sys_012",
  "timestamp": 1723758200,
  "payload": {
    "event": "window_focus_lost",
    "data": {
      "lost_to": "Chrome - YouTube",
      "duration_ms": 5000
    }
  }
}
```

**Desteklenen `event` değerleri:**

| Event | Açıklama | Data |
|-------|----------|------|
| `window_focus_lost` | Kullanıcı başka pencereye geçti | `lost_to`: pencere başlığı |
| `window_focus_gained` | Kullanıcı geri döndü | — |
| `idle_detected` | Kullanıcı 45s hareketsiz | `idle_seconds`: süre |
| `chat_close_attempt` | Chat X butonuna tıklandı | — |
| `alt_f4_attempt` | Alt+F4 basıldı | — |
| `esc_pressed` | ESC basıldı | — |
| `mouse_corner` | Fare (0,0)'a gitti | `hold_seconds`: süre |
| `effect_completed` | Bir efekt tamamlandı | `effect_id`: efekt ID'si |
| `mini_game_result` | Mini oyun sonucu | `success`: bool, `score`: int |

### 3.4. `onboarding_complete`

Onboarding akışı tamamlandığında.

```json
{
  "type": "onboarding_complete",
  "id": "ob_001",
  "timestamp": 1723758300,
  "payload": {
    "intensity": "medium",
    "language": "tr",
    "consent_given": true
  }
}
```

### 3.5. `kill_switch`

Electron tarafı kill switch yedek kanalı.

```json
{
  "type": "kill_switch",
  "id": "ks_001",
  "timestamp": 1723758400,
  "payload": {}
}
```

---

## 4. Python → Electron Mesajları

### 4.1. `handshake_ack`

Bağlantı onayı.

```json
{
  "type": "handshake_ack",
  "id": "hs_ack_001",
  "timestamp": 1723758001,
  "payload": {
    "status": "ready",
    "session_id": "sess_abc123",
    "resuming": false
  }
}
```

### 4.2. `ai_response`

AI'nın chat yanıtı + aksiyonlar.

```json
{
  "type": "ai_response",
  "id": "res_042",
  "timestamp": 1723758150,
  "payload": {
    "speech": "Sadece... seninle konuşmak istiyorum.",
    "emotion": "curious",
    "actions": [
      {
        "type": "overlay_text",
        "params": { "text": "...", "style": "ghostly", "duration_ms": 3000 },
        "delay_ms": 0
      },
      {
        "type": "ambient_shift",
        "params": { "mood": "intimate", "fade_ms": 5000 },
        "delay_ms": 1000
      }
    ]
  }
}
```

### 4.3. `effect`

Tek bir efekt komutu (hikaye timeline'ından).

```json
{
  "type": "effect",
  "id": "fx_015",
  "timestamp": 1723758500,
  "payload": {
    "category": "visual",
    "name": "screen_glitch",
    "params": {
      "intensity": 0.3,
      "duration_ms": 1000,
      "type": "tear"
    },
    "priority": "normal"
  }
}
```

**Priority Değerleri:**

| Priority | Açıklama |
|----------|----------|
| `critical` | Hemen çalıştır (kill switch, BSOD) |
| `high` | Mevcut efekt biter bitmez çalıştır |
| `normal` | Kuyruğa ekle, sırası gelince çalıştır |
| `low` | Kuyruğa ekle, boşluk varsa çalıştır |

### 4.4. `effect_chain`

Sıralı efekt zinciri.

```json
{
  "type": "effect_chain",
  "id": "chain_003",
  "timestamp": 1723758600,
  "payload": {
    "chain_id": "crisis_entrance",
    "effects": [
      { "type": "screen_fade", "params": { "target_opacity": 0.0, "duration_ms": 1000 }, "delay_ms": 0 },
      { "type": "play_stinger", "params": { "name": "crisis_hit", "volume": 0.8 }, "delay_ms": 1000 },
      { "type": "overlay_text", "params": { "text": "UYAN", "style": "glitched", "duration_ms": 2000 }, "delay_ms": 1500 },
      { "type": "screen_fade", "params": { "target_opacity": 1.0, "duration_ms": 2000 }, "delay_ms": 4000 }
    ]
  }
}
```

`delay_ms` = zincirin başlangıcından itibaren milisaniye (absolüt zamanlama).

### 4.5. `tts_play`

TTS ses dosyasını çal.

```json
{
  "type": "tts_play",
  "id": "tts_008",
  "timestamp": 1723758700,
  "payload": {
    "audio_path": "temp/tts_a1b2c3d4.mp3",
    "reduce_ambient": true,
    "ambient_volume_during": 0.3
  }
}
```

`reduce_ambient: true` → ambient ses %30'a düşer, TTS bitince normale döner.

### 4.6. `ambient_change`

Ambient ses modu değişimi.

```json
{
  "type": "ambient_change",
  "id": "amb_005",
  "timestamp": 1723758800,
  "payload": {
    "mood": "tense",
    "fade_ms": 5000,
    "volume": 0.25
  }
}
```

### 4.7. `ui_command`

UI bileşenlerini kontrol et.

```json
{
  "type": "ui_command",
  "id": "ui_009",
  "timestamp": 1723758900,
  "payload": {
    "command": "open_chat",
    "params": {
      "theme": "terminal",
      "initial_messages": [
        { "role": "ai", "content": "Merhaba.", "delay_ms": 0 },
        { "role": "ai", "content": "Seni duyabiliyorum.", "delay_ms": 2000 }
      ]
    }
  }
}
```

**Desteklenen `command` değerleri:**

| Command | Params | Açıklama |
|---------|--------|----------|
| `open_chat` | `theme`, `initial_messages` | Chat penceresini aç |
| `close_chat` | — | Chat penceresini kapat |
| `change_chat_theme` | `theme` | Chat temasını değiştir |
| `show_onboarding` | `step` | Onboarding adımını göster |
| `show_typing` | `duration_ms` | "AI yazıyor..." göster |
| `hide_typing` | — | "AI yazıyor..." gizle |
| `show_mini_game` | `game_type`, `config` | Mini oyunu başlat |

### 4.8. `narrative_event`

Hikaye fazı geçişi.

```json
{
  "type": "narrative_event",
  "id": "nar_002",
  "timestamp": 1723759000,
  "payload": {
    "event": "phase_transition",
    "from_phase": 1,
    "to_phase": 2,
    "path": null
  }
}
```

### 4.9. `shutdown`

Graceful shutdown komutu.

```json
{
  "type": "shutdown",
  "id": "sd_001",
  "timestamp": 1723759100,
  "payload": {
    "reason": "session_complete",
    "restore_required": true
  }
}
```

---

## 5. Hata Yönetimi

### Mesaj Validasyonu

Her alınan mesaj şu kontrollerden geçer:

1. JSON parse edilebilir mi?
2. `type` alanı var mı ve bilinen bir tip mi?
3. `payload` alanı var mı?
4. Tip-spesifik zorunlu alanlar mevcut mu?

### Hata Yanıtı

```json
{
  "type": "error",
  "id": "err_001",
  "timestamp": 1723759200,
  "payload": {
    "error_code": "INVALID_MESSAGE",
    "message": "Unknown message type: foo_bar",
    "original_id": "msg_bad"
  }
}
```

**Hata Kodları:**

| Kod | Açıklama |
|-----|----------|
| `INVALID_MESSAGE` | Mesaj formatı hatalı |
| `UNKNOWN_TYPE` | Bilinmeyen mesaj tipi |
| `MISSING_FIELD` | Zorunlu alan eksik |
| `AI_ERROR` | Gemini API hatası |
| `INTERNAL_ERROR` | Python iç hatası |
| `RATE_LIMITED` | Çok fazla mesaj (>10/saniye) |

### Timeout'lar

| Durum | Timeout | Aksiyon |
|-------|---------|--------|
| AI yanıt bekleme | 10 saniye | Retry (1 kez) → timeout yanıtı |
| TTS üretim | 15 saniye | Skip TTS, sadece text göster |
| WebSocket ping | 30 saniye | Bağlantı koptu kabul et |
| Effect execution | Efekt süresinin 2x'i | Efekti zorla kapat |

---

## 6. Rate Limiting

```python
RATE_LIMITS = {
    "user_input": 5,        # Saniyede maks 5 mesaj
    "system_event": 10,     # Saniyede maks 10 olay
    "effect": 20,           # Saniyede maks 20 efekt komutu
    "ai_call": 2,           # Saniyede maks 2 Gemini çağrısı
}
```

Limit aşıldığında: Mesaj kuyruğa alınır, sırası gelince işlenir. `RATE_LIMITED` hatası döndürülmez (graceful handling).

---

## 7. Sıralama ve Önceliklendirme

Electron tarafında efekt kuyruğu:

```javascript
class EffectQueue {
    // Priority sıralaması: critical > high > normal > low
    // Aynı priority'de: FIFO (ilk gelen ilk çalışır)
    // Critical: Mevcut efekti keser ve hemen çalışır
    // High: Mevcut efekt bitince hemen çalışır
    // Normal/Low: Kuyruğa eklenir
    
    enqueue(effect, priority) { /* ... */ }
    processNext() { /* ... */ }
}
```
