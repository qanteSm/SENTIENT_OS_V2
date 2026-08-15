# SENTIENT_OS v2 — Faz 6: Integration Testing (Hafta 11)

> **Hedef:** Tüm bileşenleri birleştir, entegrasyon testleri yap, kritik bugları düzelt.  
> **Süre:** 1 hafta  
> **Ön Koşul:** Faz 5 tamamlanmış (oynanabilir alpha)

---

## Faz Özeti

Bu fazda bireysel bileşenler bir araya getirilip uçtan uca test edilir. Faz 5'teki alpha'dan farklı olarak burada **kenar durumları** (edge case), **stress testleri** ve **hata kurtarma senaryoları** test edilir.

---

## Görev Listesi

### 6.1. Entegrasyon Testleri

| Test Dosyası | Ne Test Eder |
|-------------|-------------|
| `tests/integration/test_ai_pipeline.py` | Mesaj gönder → AI yanıt → efekt komutu → WS → Electron render |
| `tests/integration/test_story_flow.py` | Katman 1→2→3 tam akış, faz geçişleri, checkpoint |
| `tests/integration/test_ws_communication.py` | WS bağlantı kopması, yeniden bağlanma, mesaj kaybı |
| `tests/integration/test_memory_pipeline.py` | 50+ mesaj → episodic → profil güncelleme → prompt'a yansıma |
| `tests/integration/test_safety_integration.py` | Kill switch + restore + crash recovery entegre test |

---

### 6.2. Edge Case Testleri

| Senaryo | Beklenen Davranış |
|---------|-------------------|
| Gemini API 30 saniye yanıt vermezse | Timeout → offline fallback → "..." mesajı |
| İnternet bağlantısı oturum ortasında koparsa | Offline mod → template yanıtlar → efektler devam eder |
| Kullanıcı 5 dakika boyunca hiç yazmasa | 45s'de AI ilk mesaj, sonra 2 dk'da tekrar, max 3 kez |
| Kullanıcı saniyede 10 mesaj gönderirse | Rate limit → kuyruğa al → sırayla işle |
| SQLite dosyası kilitlenirse | busy_timeout 5s → retry → başarısız → log + devam |
| Edge-TTS API ulaşılamaz | TTS atlanır, sadece text gösterilir |
| Electron crash olursa | Python state korur, yeniden bağlanma bekler |
| Python crash olursa | Electron hata mesajı gösterir, 3 kez restart dener |
| Wallpaper restore başarısız olursa | Log kaydı + kullanıcıya bilgi notu |
| 2. monitörde overlay | DPI-aware boyutlandırma + primary display hedefle |

---

### 6.3. Performans Testleri

| Metrik | Hedef | Test Yöntemi |
|--------|-------|-------------|
| Python RAM kullanımı | < 200 MB (30 dk oturum) | psutil ile ölçüm |
| Electron RAM kullanımı | < 350 MB | Chrome DevTools |
| CPU kullanımı (idle) | < 5% | Efekt yok, sadece WS dinleme |
| CPU kullanımı (aktif efekt) | < 30% | 5 eş zamanlı efekt |
| AI yanıt süresi | < 2s (p95) | 50 mesaj benchmark |
| WS mesaj latency | < 50ms | Ping/pong ölçüm |
| TTS üretim süresi | < 3s (10 kelimelik cümle) | 20 cümle benchmark |
| Overlay render FPS | > 30 FPS (efekt sırasında) | requestAnimationFrame counter |

---

### 6.4. Memory Leak Testi

30 dakikalık oturum boyunca:
- Python heap boyutu büyümemeli (gc.collect() sonrası sabit)
- Electron heap boyutu büyümemeli (DevTools snapshot karşılaştırma)
- Event listener birikimi olmamalı
- WebSocket mesaj kuyruğu büyümemeli

**Test script'i:**
```python
# Her 5 dakikada snapshot al
import psutil, gc

snapshots = []
for minute in range(0, 35, 5):
    gc.collect()
    proc = psutil.Process()
    snapshots.append({
        "minute": minute,
        "rss_mb": proc.memory_info().rss / 1024 / 1024,
        "vms_mb": proc.memory_info().vms / 1024 / 1024,
    })

# Büyüme oranı: son snapshot / ilk snapshot < 1.3 (maks %30 büyüme)
```

---

### 6.5. Çoklu Oturum Testi

| Senaryo | Beklenen |
|---------|----------|
| 1. oturum tamamlandı → 2. açılış | AI: "Tekrar mı geldin?" + farklı yola yönlendirme |
| 1. oturum crash → 2. açılış | Crash recovery → restore → yeni oturum |
| 3. oturum | AI: "Artık her şeyi gördün." → mini kapanış |
| Kullanıcı profili kalıcı mı? | Evet — oturumlar arası korunuyor |

---

### 6.6. Güvenlik Testleri

| Test | Kontrol |
|------|---------|
| Kill switch (Ctrl+Shift+Q) | Efekt sırasında, chat açıkken, mini oyunda — her durumda çalışır |
| Privacy filter | .env, .ssh, password dosyaları ASLA AI context'te yok |
| Resource guard | Yapay CPU/RAM yükü → shutdown tetiklenir |
| Panic detection | ESC spam, Alt+F4 spam → shutdown veya intensity azaltma |
| Temp dosya temizliği | Kill switch sonrası orphan MP3 yok |
| Streamer modu | OBS açıkken dosya isimleri context'ten çıkar |
| Gerçek dosya sistemi | Hiçbir gerçek dosya oluşturulmuyor/silinmiyor/değiştirilmiyor |

---

## Faz 6 Çıkış Kriterleri

- [ ] Tüm entegrasyon testleri geçer
- [ ] Edge case'ler crash yapmaz (graceful degradation)
- [ ] Python RAM < 200 MB (30 dk oturum)
- [ ] Electron RAM < 350 MB
- [ ] CPU idle < 5%, aktif < 30%
- [ ] Memory leak yok (maks %30 büyüme)
- [ ] AI yanıt p95 < 2s
- [ ] Kill switch her durumda çalışır
- [ ] Privacy filter %100 doğru
- [ ] Çoklu oturum senaryoları çalışır
- [ ] Tüm güvenlik testleri geçer
