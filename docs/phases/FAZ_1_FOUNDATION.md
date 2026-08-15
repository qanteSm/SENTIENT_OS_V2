# SENTIENT_OS v2 — Faz 1: Foundation (Hafta 1-2)

> **Hedef:** Çalışan bir iskelet — Electron başlar, Python başlar, ikisi WebSocket'te konuşur.  
> **Süre:** 2 hafta  
> **Ön Koşul:** Yok (ilk faz)

---

## Faz Özeti

Bu fazda projenin teknik temeli atılır. Hiçbir iş mantığı (AI, hikaye, efekt) yazılmaz. Amaç:
- Python backend'in ayağa kalkması
- Electron frontend'in ayağa kalkması
- İkisinin WebSocket üzerinden mesaj gönderip alabilmesi
- Güvenlik altyapısının (kill switch, resource guard) çalışması
- Veritabanının hazır olması

Faz 1 sonunda `npm run dev` + `python -m src.main` ile iki süreç başlar, "hello world" mesajı WebSocket üzerinden gider-gelir.

---

## Görev Listesi

### 1.1. Python Proje İskeleti

| Dosya | Açıklama |
|-------|----------|
| `python-engine/pyproject.toml` | Proje metadata, bağımlılıklar, scripts |
| `python-engine/requirements.txt` | pip bağımlılık listesi |
| `python-engine/src/__init__.py` | Paket init |
| `python-engine/src/main.py` | Entry point — WS server başlatır, DPI awareness ayarlar |

**Kabul Kriteri:** `pip install -e .` başarılı çalışır, `python -m src.main` hata vermeden başlar.

**DPI Awareness (main.py başında zorunlu):**
```python
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()
```

**Stdout Buffer (main.py başında zorunlu):**
```python
import sys
sys.stdout.reconfigure(line_buffering=True)
```

---

### 1.2. Pydantic Config Sistemi

| Dosya | Açıklama |
|-------|----------|
| `src/config/__init__.py` | — |
| `src/config/settings.py` | Pydantic BaseSettings sınıfı |
| `src/config/defaults.yaml` | Varsayılan config değerleri |

**Settings Sınıfı:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    gemini_api_key: str = ""
    
    # Server
    ws_host: str = "127.0.0.1"
    ws_port: int = 0  # 0 = random port
    
    # Safety
    kill_switch_enabled: bool = True
    cpu_critical: int = 90
    ram_critical_mb: int = 750
    
    # Horror
    intensity: str = "medium"  # mild, medium, extreme
    language: str = "tr"
    
    # TTS
    tts_voice: str = "tr-TR-AhmetNeural"
    
    # Paths
    db_path: str = "data/sentient.db"
    temp_dir: str = "temp/"
    log_dir: str = "logs/"
    
    class Config:
        env_prefix = "SENTIENT_"
        env_file = ".env"
```

**Kabul Kriteri:** `Settings()` objesini oluşturabilir, `.env` dosyasından ve environment variable'lardan okuyabilir.

---

### 1.3. Structured Logging

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/logger.py` | JSON formatında structured logging |

**Format:**
```json
{"timestamp": "2026-08-16T00:15:00", "level": "INFO", "module": "kernel", "message": "Session started", "session_id": "sess_abc"}
```

**Kabul Kriteri:** Log dosyası `logs/sentient.log`'a yazılır, JSON parse edilebilir.

---

### 1.4. Event Bus

| Dosya | Açıklama |
|-------|----------|
| `src/core/__init__.py` | — |
| `src/core/event_bus.py` | Async pub/sub event sistemi |

**Interface:**
```python
class EventBus:
    async def subscribe(self, event_type: str, callback: Callable)
    async def publish(self, event_type: str, **kwargs)
    async def unsubscribe(self, event_type: str, callback: Callable)
```

**Kabul Kriteri:** `publish("test", data="hello")` → subscriber callback tetiklenir.

**Test:** `tests/unit/test_event_bus.py`

---

### 1.5. WebSocket Server

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/ws_server.py` | WebSocket sunucusu |

**Davranış:**
1. Random port'ta dinlemeye başlar
2. `stdout`'a `WS_PORT:{port}` yazar (unbuffered)
3. Bağlantı geldiğinde handshake bekler
4. Mesajları EventBus'a yayınlar
5. EventBus'tan gelen mesajları client'a gönderir

**Kabul Kriteri:** `wscat -c ws://127.0.0.1:{port}` ile bağlanılabilir, JSON mesaj gönderip alınabilir.

---

### 1.6. SQLite Persistence

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/__init__.py` | — |
| `src/infrastructure/persistence/__init__.py` | — |
| `src/infrastructure/persistence/database.py` | SQLite bağlantı yönetimi + WAL config |
| `src/infrastructure/persistence/models.py` | Tablo tanımları (CREATE TABLE) |
| `src/infrastructure/persistence/state_store.py` | Session + checkpoint CRUD |

**Veritabanı init (zorunlu PRAGMA'lar):**
```python
await db.execute("PRAGMA journal_mode=WAL;")
await db.execute("PRAGMA busy_timeout=5000;")
await db.execute("PRAGMA synchronous=NORMAL;")
await db.execute("PRAGMA cache_size=-64000;")
```

**Kabul Kriteri:** Veritabanı oluşturulur, session kayıt/okuma çalışır, WAL mode aktif.

**Test:** `tests/unit/test_persistence.py`

---

### 1.7. Safety Sistemi

| Dosya | Açıklama |
|-------|----------|
| `src/core/safety.py` | Kill switch, resource guard, panic detection |

**Kill Switch:**
- `IsolatedKillSwitch` sınıfı — ayrı thread'de `RegisterHotKey(Ctrl+Shift+Q)`
- Tetiklendiğinde: restore → taskkill → os._exit(0)
- TTS temp dosya temizliği dahil

**Resource Guard:**
- 5 saniyede bir CPU/RAM kontrolü
- Eşik aşılırsa EventBus'a `safety.shutdown` yayınla

**Kabul Kriteri:** Ctrl+Shift+Q basıldığında process anında kapanır. CPU %95'e çıkarsa (stress test) shutdown tetiklenir.

---

### 1.8. Privacy Filter

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/privacy_filter.py` | Dosya/yol filtreleme |

**Davranış:**
1. Whitelist klasörleri tara (Desktop, Documents, Downloads)
2. Blacklist kalıplarına uyanları filtrele
3. Sadece dosya/klasör isimlerini döndür (maks 30)
4. Tam yol asla dışarı çıkmaz

**Kabul Kriteri:** `.env`, `.ssh`, `password` içeren dosyalar filtrelenir, sadece güvenli isimler döner.

**Test:** `tests/unit/test_privacy_filter.py`

---

### 1.9. Electron Proje İskeleti

| Dosya | Açıklama |
|-------|----------|
| `electron-app/package.json` | Electron bağımlılıkları |
| `electron-app/main/main.ts` | Electron entry point |
| `electron-app/main/ipc-bridge.ts` | WebSocket client → Python'a bağlanır |
| `electron-app/main/kill-switch.ts` | Yedek kill switch (globalShortcut) |
| `electron-app/main/tray.ts` | System tray ikonu (placeholder) |

**Davranış:**
1. Python process'i spawn eder (`PYTHONUNBUFFERED=1`)
2. stdout'tan `WS_PORT:{port}` okur
3. WebSocket ile bağlanır
4. Handshake yapar

**Kabul Kriteri:** `npm run dev` ile Electron başlar, Python otomatik başlar, WS bağlantısı kurulur.

---

### 1.10. Boş Overlay Penceresi

| Dosya | Açıklama |
|-------|----------|
| `electron-app/main/window-manager.ts` | Pencere oluşturma/yönetimi |
| `electron-app/renderer/overlay/index.html` | Boş overlay HTML |
| `electron-app/renderer/overlay/styles.css` | Temel overlay stilleri |
| `electron-app/renderer/overlay/engine.js` | Efekt render motoru (boş iskelet) |

**Overlay Penceresi:**
- `transparent: true`, `frame: false`, `alwaysOnTop: true`
- `setIgnoreMouseEvents(true, { forward: true })` — click-through
- DPI-aware boyutlandırma (`screen.getPrimaryDisplay()`)
- Tam ekran kaplıyor ama görünmez (boş)

**Kabul Kriteri:** Tam ekran şeffaf overlay açılır, fare tıklamaları altındaki pencereye geçer.

---

## Test Matrisi

| Test | Dosya | Ne Test Eder |
|------|-------|-------------|
| `test_event_bus.py` | `core/event_bus.py` | Pub/sub, birden fazla subscriber, unsubscribe |
| `test_privacy_filter.py` | `infrastructure/privacy_filter.py` | Blacklist filtreleme, whitelist tarama, isim çıkarma |
| `test_persistence.py` | `infrastructure/persistence/` | DB oluşturma, CRUD, WAL mode, concurrent write |
| `test_settings.py` | `config/settings.py` | Config yükleme, env var override, validation |
| `test_safety.py` | `core/safety.py` | Resource guard limitleri (mock psutil) |

---

## Faz 1 Çıkış Kriterleri

- [ ] `pip install -e .` başarılı
- [ ] `python -m src.main` hata vermeden başlar, WS dinler
- [ ] `npm run dev` Electron başlar, Python spawn eder
- [ ] WebSocket handshake başarılı (log'da görünür)
- [ ] JSON mesaj gönderip alınabilir (echo test)
- [ ] Ctrl+Shift+Q kill switch çalışır
- [ ] SQLite veritabanı oluşturulur, WAL mode aktif
- [ ] Privacy filter blacklist'i doğru filtreler
- [ ] Overlay penceresi tam ekran, şeffaf, click-through
- [ ] Tüm unit testler geçer
- [ ] DPI awareness ayarlanmış (Python + Electron)
- [ ] Stdout unbuffered (port gecikmesi yok)
