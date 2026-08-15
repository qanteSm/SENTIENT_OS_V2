# SENTIENT_OS v2 — Faz 3: Story Engine (Hafta 5-6)

> **Hedef:** Hikaye fazları çalışır, timeline olayları tetiklenir, AI sinyallere tepki verir.  
> **Süre:** 2 hafta  
> **Ön Koşul:** Faz 2 tamamlanmış (AI sohbet, memory, personality)

---

## Faz Özeti

Bu fazda hikaye motorunu inşa ediyoruz. Katman 1 → 2 → 3 geçişleri, zamanlı olay tetikleme, AI'nın narrative sinyalleri ve 3 farklı yol dallanması çalışır hale gelir. Faz 3 sonunda terminal üzerinden tam bir hikaye akışı test edilebilir.

---

## Görev Listesi

### 3.1. Narrative State Machine

| Dosya | Açıklama |
|-------|----------|
| `src/story/__init__.py` | — |
| `src/story/narrative.py` | Hikaye state machine (Katman 1/2/3) |

**Sorumluluklar:**
- 3 katman yönetimi: `FIRST_CONTACT → DIALOGUE → CRISIS`
- Katman geçiş kuralları (zaman + AI sinyal)
- Mevcut yol takibi (curious/fear/attack)
- State snapshot kaydetme/yükleme (checkpoint uyumu)

**State Machine:**
```python
class NarrativePhase(Enum):
    FIRST_CONTACT = 1   # 0-5 dk, diyalog yok
    DIALOGUE = 2         # 5-20 dk, chat aktif
    CRISIS = 3           # 20-40 dk, final

class NarrativeState:
    phase: NarrativePhase
    phase_start_time: float
    path: str | None      # None → undecided → curious/fear/attack
    path_locked: bool      # Katman 3'te kilit atılır
    finale_type: str | None  # salvation/battle/surrender
```

**Geçiş Kuralları:**
- `FIRST_CONTACT → DIALOGUE`: 5 dk sonra VEYA system tray tıklaması
- `DIALOGUE → CRISIS`: 20. dk VEYA `trigger_crisis` AI sinyali (min 10 dk sonrası)
- `CRISIS → END`: Finale seçimine göre (konuşma/mini-oyun/monolog sonu)

**Kabul Kriteri:** State machine geçişleri doğru zamanda tetiklenir, state kaydedilir.

**Test:** `tests/unit/test_narrative.py`

---

### 3.2. Timeline Scheduler

| Dosya | Açıklama |
|-------|----------|
| `src/story/timeline.py` | Zamanlı olay zamanlayıcı ve pacing motoru |

**Sorumluluklar:**
- Katman 1 olay timeline'ı (10 önceden tanımlı olay, sabit sıra)
- Olay arası minimum boşluk kontrolü (30 saniye)
- Idle-aware pacing: idle → sıkıştır, aktif → uzat
- Olay kuyruğu yönetimi

**Interface:**
```python
class Timeline:
    def __init__(self, event_bus: EventBus, config: Settings):
        ...
    
    async def start_phase(self, phase: NarrativePhase):
        """Faza ait timeline'ı başlat."""
        ...
    
    async def stop(self):
        """Aktif timeline'ı durdur."""
        ...
    
    def set_idle_state(self, is_idle: bool, idle_seconds: float):
        """Pacing ayarı için idle durumu güncelle."""
        ...
```

**Pacing Algoritması:**
```python
BASE_INTERVAL = 30  # saniye
IDLE_COMPRESSION = 0.4   # idle ise %40 sıkıştır
ACTIVE_EXTENSION = 1.5   # aktifse %50 uzat

def next_delay(idle_seconds: float) -> float:
    if idle_seconds > 30:
        return BASE_INTERVAL * (1.0 - IDLE_COMPRESSION)  # 18s
    else:
        return BASE_INTERVAL * ACTIVE_EXTENSION            # 45s
```

**Kabul Kriteri:** Katman 1 olayları doğru sırada ve aralıkta tetiklenir.

**Test:** `tests/unit/test_timeline.py`

---

### 3.3. Trigger Sistemi

| Dosya | Açıklama |
|-------|----------|
| `src/story/triggers.py` | Olay tetikleyicileri |

**Tetikleyici Tipleri:**

| Tip | Açıklama | Örnek |
|-----|----------|-------|
| `TimeTrigger` | Belirli bir süre sonra | 5 dk sonra chat aç |
| `IdleTrigger` | Kullanıcı N saniye idle | 45s sessizlik → AI konuşur |
| `SignalTrigger` | AI narrative_signal | `trigger_crisis` → Katman 3 |
| `EventTrigger` | Sistem olayı | Chat kapatma → AI tepki |
| `ThresholdTrigger` | Skor eşiği | path_score > 1.0 → yol kilit |

**Interface:**
```python
class Trigger(ABC):
    async def check(self, context: TriggerContext) -> bool:
        ...
    
    def get_action(self) -> TriggerAction:
        ...
```

**Kabul Kriteri:** Her trigger tipi doğru koşulda tetiklenir.

---

### 3.4. Effect Decider

| Dosya | Açıklama |
|-------|----------|
| `src/story/effect_decider.py` | AI kararından efekt listesine dönüşüm |

**Sorumluluklar:**
- AI'nın `actions` dizisini validate etme
- Duygu-efekt uyumluluk kontrolü (EFFECT_CATALOG'daki eşleme tablosu)
- Efekt parametrelerini sınır içinde tutma (intensity maks 1.0, duration maks 10s vb.)
- Efekt zinciri oluşturma (delay_ms hesaplama)
- Faz bazlı efekt kısıtlama (Katman 1'de agresif efekt yok)

**Interface:**
```python
class EffectDecider:
    def process_actions(self, actions: list[dict], phase: int, emotion: str) -> list[EffectCommand]:
        ...
    
    def create_effect_chain(self, commands: list[EffectCommand]) -> dict:
        ...
```

**Kabul Kriteri:** AI'nın `actions` çıktısı → WS üzerinden gönderilebilir efekt komutlarına dönüşür.

**Test:** `tests/unit/test_effect_decider.py`

---

### 3.5. Katman 1 Sahneleri (First Contact)

| Dosya | Açıklama |
|-------|----------|
| `src/story/scenes/__init__.py` | — |
| `src/story/scenes/first_contact.py` | Katman 1 — 10 önceden tanımlı olay |

**10 Olay Listesi:**
1. Mouse drift (0:30)
2. Fake file appear — "readme.txt" (1:00)
3. Overlay text — "merhaba" (1:30)
4. System clock shift — -60s (2:00)
5. Screen shake — hafif (2:30)
6. Log message — "Bağlantı kuruldu" (3:00)
7. Screen glitch — desaturate (3:30)
8. Fake notification — güvenlik uyarısı (4:00)
9. Overlay text — "SENİ GÖRÜYORUM" + glitch (4:30)
10. Open chat + ambient start (5:00)

**Her olay bir `SceneEvent` dataclass'ı:**
```python
@dataclass(frozen=True)
class SceneEvent:
    time_offset_s: float       # Faz başlangıcından itibaren saniye
    effects: list[dict]        # Efekt komutları
    audio: dict | None         # Ses komutu (opsiyonel)
    description: str           # Log için açıklama
```

**Kabul Kriteri:** 10 olay doğru sırada ve zamanda tetiklenir (terminal log'da görünür).

---

### 3.6. Katman 2 Sahneleri (Dialogue)

| Dosya | Açıklama |
|-------|----------|
| `src/story/scenes/dialogue.py` | Katman 2 — diyalog kuralları ve arka plan olayları |

**Sorumluluklar:**
- AI ilk mesajlarını tetikleme ("Merhaba." → "Sonunda..." → "Sen kimsin?")
- Arka plan olay kuralları (3 dk'da ambient değişimi, emotion → efekt)
- Sessizlik kırıcı (45s idle → AI mesaj)
- Chat kapatma tepkisi
- Window focus kaybı tepkisi
- Yol belirleme skorlarını Director'a bildirme

**Kabul Kriteri:** AI diyaloğa başlar, arka plan olayları tetiklenir, yol skoru birikir.

---

### 3.7. Katman 3 Sahneleri (Crisis)

| Dosya | Açıklama |
|-------|----------|
| `src/story/scenes/crisis.py` | Katman 3 — 3 farklı final |

**3 Final Senaryosu:**

| Final | Yol | Anahtar Mekanik |
|-------|-----|-----------------|
| Kurtuluş (`salvation`) | curious | AI vedalaşıyor, oyuncu "kal"/"git" seçer |
| Savaş (`battle`) | fear | 60s mini oyun (virüs pencerelerini kapatma) |
| Teslimiyet (`surrender`) | attack | AI monologu, masaüstü manipülasyonu |

Her final için:
- Giriş sekansı (kararma → sessizlik → overlay text → chat yeni tema)
- Ana akış (mesajlar + efektler)
- Kapanış (restore + disclaimer + çıkış)

**Kabul Kriteri:** 3 farklı yol için 3 farklı final terminal'de test edilebilir.

---

### 3.8. Director

| Dosya | Açıklama |
|-------|----------|
| `src/core/director.py` | Ana yönetici — tüm modülleri koordine eder |

**Sorumluluklar:**
- Session başlangıcında modülleri initialize etme
- Katman geçişlerini yönetme (Narrative ↔ Timeline ↔ Scenes)
- AI yanıtlarını işleme (Brain → EffectDecider → WS gönder)
- Trigger'ları dinleme ve tepki verme
- Kullanıcı girdilerini yönlendirme (WS → Brain)
- Checkpoint tetikleme (katman geçişlerinde)

**Interface:**
```python
class Director:
    def __init__(self, event_bus, brain, memory, personality, 
                 narrative, timeline, effect_decider, ws_server, config):
        ...
    
    async def start_session(self):
        ...
    
    async def handle_user_input(self, message: dict):
        ...
    
    async def handle_narrative_signal(self, signal: str):
        ...
    
    async def shutdown(self, reason: str):
        ...
```

**Kabul Kriteri:** Director tüm modülleri koordine eder, oturum baştan sona çalışır.

---

### 3.9. Session Lifecycle

| Dosya | Açıklama |
|-------|----------|
| `src/core/session.py` | Oturum yaşam döngüsü |

**Sorumluluklar:**
- Yeni oturum oluşturma (SQLite'a kaydet)
- Mevcut oturumu sürdürme (crash recovery)
- Oturum sonlandırma (final → restore → kaydet)
- Checkpoint kaydetme/yükleme

**Interface:**
```python
class Session:
    async def create(self) -> str:   # session_id döner
        ...
    
    async def resume(self, session_id: str):
        ...
    
    async def checkpoint(self, label: str):
        ...
    
    async def end(self, status: str):  # "completed", "crashed"
        ...
```

**Kabul Kriteri:** Oturum oluşturulur, checkpoint kaydedilir, crash sonrası resume çalışır.

---

## Test Matrisi

| Test | Dosya | Ne Test Eder |
|------|-------|-------------|
| `test_narrative.py` | `story/narrative.py` | State machine geçişleri, yol kilit mekanizması |
| `test_timeline.py` | `story/timeline.py` | Olay zamanlaması, pacing, idle sıkıştırma |
| `test_effect_decider.py` | `story/effect_decider.py` | Aksiyon → efekt dönüşümü, güvenlik sınırları |
| `test_director.py` | `core/director.py` | End-to-end oturum akışı (mock modüller) |

---

## Faz 3 Çıkış Kriterleri

- [ ] Katman 1 → 2 → 3 geçişleri zamanında tetiklenir
- [ ] Katman 1: 10 olay doğru sırada çalışır (log'da görünür)
- [ ] Katman 2: AI diyaloğa başlar, arka plan olayları tetiklenir
- [ ] Katman 2: Yol skoru birikerek path belirlenir
- [ ] Katman 3: 3 farklı final senaryosu terminal'de test edilebilir
- [ ] Director tüm modülleri sorunsuz koordine eder
- [ ] Session checkpoint kaydedilir ve yüklenebilir
- [ ] Crash recovery çalışır (session resume)
- [ ] Timeline pacing idle durumuna göre ayarlanır
- [ ] Tüm unit testler geçer
