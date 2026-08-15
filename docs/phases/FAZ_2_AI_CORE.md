# SENTIENT_OS v2 — Faz 2: AI Core (Hafta 3-4)

> **Hedef:** Terminal'de AI ile Türkçe sohbet edilebilir. 3 katmanlı memory çalışır.  
> **Süre:** 2 hafta  
> **Ön Koşul:** Faz 1 tamamlanmış (WS bağlantısı, SQLite, config)

---

## Faz Özeti

Bu fazda AI beynini inşa ediyoruz. Faz 2 sonunda Python backend'de bir terminal arayüzü üzerinden Gemini AI ile Türkçe sohbet edilebilir, AI hatırlayabilir ve kişilik geliştirebilir. Henüz Electron UI yok — sadece iş mantığı.

---

## Görev Listesi

### 2.1. Gemini API Entegrasyonu

| Dosya | Açıklama |
|-------|----------|
| `src/ai/__init__.py` | — |
| `src/ai/brain.py` | Gemini API istemcisi, yanıt üretimi, retry mantığı |

**Sorumluluklar:**
- `google-generativeai` SDK ile Gemini 2.5 Flash bağlantısı
- `generation_config` ve `safety_settings` yapılandırması
- JSON mode (`response_mime_type: "application/json"`)
- Retry: 3 deneme, exponential backoff (1s → 2s → 4s)
- Timeout: 10 saniye
- Hata durumunda offline fallback

**Interface:**
```python
class Brain:
    def __init__(self, config: Settings, memory: Memory, personality: Personality):
        ...
    
    async def generate_response(self, user_input: str, context: dict) -> AIResponse:
        ...
    
    async def generate_summary(self, messages: list[Message]) -> str:
        ...
```

**Kabul Kriteri:** `brain.generate_response("Merhaba")` → geçerli JSON yanıt döner.

**Test:** `tests/unit/test_brain.py` (mock API ile)

---

### 2.2. Prompt Builder (Context Builder)

| Dosya | Açıklama |
|-------|----------|
| `src/ai/context_builder.py` | Prompt bağlam oluşturma |
| `src/ai/prompts/system_base.txt` | Temel kimlik prompt'u |
| `src/ai/prompts/phase_1_first_contact.txt` | Katman 1 prompt eki |
| `src/ai/prompts/phase_2_dialogue.txt` | Katman 2 prompt eki |
| `src/ai/prompts/phase_3_crisis.txt` | Katman 3 prompt eki |

**Sorumluluklar:**
- System prompt + faz eki birleştirme
- Semantic memory (kullanıcı profili) ekleme
- Episodic memory (son 10 özet) ekleme
- Sistem bağlamı ekleme (saat, dosya isimleri, aktif pencere)
- Working memory (son 20 mesaj) ekleme
- Toplam token sayısını kontrol etme (maks ~4000 token context)

**Interface:**
```python
class ContextBuilder:
    def build_prompt(self, phase: int, path: str | None) -> str:
        ...
    
    def build_context(self, memory: Memory, system_info: dict) -> str:
        ...
```

**Kabul Kriteri:** `build_prompt(phase=2)` → tam prompt string döner, tüm bölümler mevcut.

**Test:** `tests/unit/test_context_builder.py`

---

### 2.3. Response Parser

| Dosya | Açıklama |
|-------|----------|
| `src/ai/response_parser.py` | AI JSON yanıtını parse ve validate etme |

**Sorumluluklar:**
- JSON parse
- Schema validasyonu (speech, emotion, actions, narrative_signal)
- Bilinmeyen aksiyon tiplerini filtreleme
- Parse başarısızsa retry veya fallback

**Interface:**
```python
@dataclass(frozen=True)
class AIResponse:
    speech: str
    emotion: str
    internal_thought: str
    actions: list[dict]
    memory_note: str | None
    narrative_signal: str

def parse_response(raw_json: str) -> AIResponse:
    ...
```

**Kabul Kriteri:** Geçerli JSON → `AIResponse`, geçersiz JSON → `ParseError` veya fallback.

**Test:** `tests/unit/test_response_parser.py`

---

### 2.4. Working Memory

| Dosya | Açıklama |
|-------|----------|
| `src/ai/memory.py` | 3 katmanlı bellek yönetimi |

**Working Memory Kısmı:**
- Son 20 mesaj (FIFO)
- Her mesaj: `Message(role, content, timestamp, emotion)`
- RAM'de tutulur, SQLite'a da yedeklenir
- Prompt'a tüm mesajlar eklenir

**Interface:**
```python
class Memory:
    async def add_message(self, role: str, content: str, emotion: str = ""):
        ...
    
    def get_working_memory(self) -> list[Message]:
        ...
```

**Kabul Kriteri:** 25 mesaj eklendiğinde sadece son 20'si döner (FIFO).

---

### 2.5. Episodic Memory

**Episodic Memory Kısmı:**
- Her 10 mesajda bir Gemini'ye özet çıkartma isteği (arka plan)
- Özetler SQLite'a kaydedilir
- Maks 50 episod, taşma durumunda en eski 5 → 1'e birleştir
- Prompt'a son 10 episod eklenir

**Interface:**
```python
class Memory:
    async def generate_episode(self):
        """Son 10 mesajı özetle, SQLite'a kaydet."""
        ...
    
    def get_recent_episodes(self, limit: int = 10) -> list[Episode]:
        ...
```

**Kabul Kriteri:** 10 mesaj sonrası otomatik episod oluşturulur ve DB'ye kaydedilir.

---

### 2.6. Semantic Memory (Kullanıcı Profili)

**Semantic Memory Kısmı:**
- Key-value profil (temperament, curiosity, trust, vb.)
- Her 10 episod sonrası Gemini ile profil güncelleme
- SQLite'da kalıcı
- Prompt'a her zaman eklenir

**Interface:**
```python
class Memory:
    async def update_profile(self):
        """Son episodlara dayanarak profili güncelle."""
        ...
    
    def get_profile(self) -> dict:
        ...
```

**Kabul Kriteri:** Profil oluşturulur, güncellenir, oturum kapanıp açıldığında korunur.

---

### 2.7. AI Personality

| Dosya | Açıklama |
|-------|----------|
| `src/ai/personality.py` | AI duygu durumu ve kişilik evrimi |

**Sorumluluklar:**
- `PersonalityState` yönetimi (curiosity, trust, aggression, vb.)
- AI her yanıt verdiğinde `emotion` alanına göre state güncelleme
- Yol belirleme skoru hesaplama (curious/fear/attack)
- State snapshot kaydetme/yükleme

**Interface:**
```python
class Personality:
    def update_from_response(self, response: AIResponse):
        ...
    
    def update_from_user_behavior(self, behavior: str):
        ...
    
    def get_current_emotion(self) -> str:
        ...
    
    def determine_path(self) -> str:
        ...
    
    def get_state(self) -> PersonalityState:
        ...
```

**Kabul Kriteri:** Birkaç mesaj sonrası emotion ve path_scores değişir.

**Test:** `tests/unit/test_personality.py`

---

### 2.8. Response Cache

| Dosya | Açıklama |
|-------|----------|
| `src/ai/cache.py` | Benzer sorulara cache'li yanıt |

**Sorumluluklar:**
- SHA256 tabanlı cache key (input + phase + emotion)
- TTL: 5 dakika
- In-memory dict (SQLite gereksiz — oturum bazlı)
- Cache hit → API çağrısı yapılmaz

**Kabul Kriteri:** Aynı soru 2 kez sorulduğunda 2. sefer API çağrılmaz.

**Test:** `tests/unit/test_cache.py`

---

### 2.9. Offline Fallback

`src/ai/brain.py` içinde:

**Sorumluluklar:**
- API ulaşılamaz → template yanıtlar döndür
- Template seçimi: kullanıcı mesajındaki anahtar kelimeler + mevcut emotion
- Actions dizisi boş döner (efekt yok)
- Offline modda episod/profil güncelleme yapılmaz

**Kabul Kriteri:** API key boşken veya internet yokken crash olmadan template yanıt döner.

---

### 2.10. File Scanner + System Info

| Dosya | Açıklama |
|-------|----------|
| `src/infrastructure/platform/__init__.py` | — |
| `src/infrastructure/platform/common.py` | Platform interface (ABC) |
| `src/infrastructure/platform/windows/__init__.py` | — |
| `src/infrastructure/platform/windows/file_scanner.py` | Masaüstü dosya tarama |
| `src/infrastructure/platform/windows/window_info.py` | Aktif pencere başlığı |

**file_scanner.py:**
- Desktop, Documents, Downloads tarama (1 seviye derinlik)
- Privacy filter üzerinden geçirme
- Sonuç: `["Projeler", "cv.pdf", "notlar.txt"]`

**window_info.py:**
- Aktif pencere başlığını döndürme (`GetForegroundWindow` + `GetWindowText`)
- Streamer koruması (OBS algılama)

**Kabul Kriteri:** Masaüstü dosya isimleri (filtrelenmiş) toplanır, aktif pencere başlığı alınır.

---

### 2.11. Terminal Test Arayüzü

`src/main.py` içinde geçici bir terminal chat modu:

```python
# Geliştirme sırasında: python -m src.main --chat
async def terminal_chat():
    while True:
        user_input = input("Sen: ")
        response = await brain.generate_response(user_input, context)
        print(f"AI [{response.emotion}]: {response.speech}")
```

**Kabul Kriteri:** Terminal'de Gemini ile Türkçe sohbet edilebilir, memory çalışır.

---

## Test Matrisi

| Test | Dosya | Ne Test Eder |
|------|-------|-------------|
| `test_brain.py` | `ai/brain.py` | API çağrısı (mock), retry, offline fallback |
| `test_memory.py` | `ai/memory.py` | Working memory FIFO, episodic generation, profile CRUD |
| `test_personality.py` | `ai/personality.py` | Emotion update, path scoring, state persistence |
| `test_context_builder.py` | `ai/context_builder.py` | Prompt assembly, token limit |
| `test_response_parser.py` | `ai/response_parser.py` | Valid/invalid JSON parse |
| `test_cache.py` | `ai/cache.py` | Cache hit/miss, TTL expiry |

---

## Faz 2 Çıkış Kriterleri

- [ ] `python -m src.main --chat` ile terminal'de AI sohbet çalışır
- [ ] AI Türkçe yanıt veriyor (Gemini 2.5 Flash)
- [ ] Working memory: son 20 mesaj tutulur, FIFO
- [ ] Episodic memory: 10 mesaj sonrası otomatik özet üretilir
- [ ] Semantic memory: kullanıcı profili oluşturulur ve güncellenir
- [ ] Personality: emotion state mesaja göre değişir
- [ ] Cache: aynı soru tekrarında API çağrılmaz (5 dk TTL)
- [ ] Offline: API yokken template yanıt döner, crash yok
- [ ] Privacy filter: dosya isimleri filtrelenmiş olarak context'e girer
- [ ] Tüm unit testler geçer
