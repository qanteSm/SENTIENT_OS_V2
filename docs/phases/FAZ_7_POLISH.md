# SENTIENT_OS v2 — Faz 7: Polish & Ses Tasarımı (Hafta 12)

> **Hedef:** Ses dosyalarının finalizasyonu, UX detayları, animasyon iyileştirmeleri.  
> **Süre:** 1 hafta  
> **Ön Koşul:** Faz 6 tamamlanmış (entegrasyon testleri başarılı)

---

## Faz Özeti

Bu faz "son dokunuş" fazıdır. İşlevsel olarak her şey çalışıyor ama deneyimi premium hissettirecek detaylar eksik. Ses dosyaları finalize edilir, animasyon zamanlamaları ayarlanır, UX pürüzleri giderilir.

---

## Görev Listesi

### 7.1. Ses Dosyaları Finalizasyonu

**Drone Sesleri (loop):**
- `low_hum.wav` — 30 saniyelik, seamless loop, düşük frekanslı hum
- `static_noise.wav` — 15 saniyelik, hafif parazit
- `whispers.wav` — 20 saniyelik, birden fazla fısıltı katmanı
- `heartbeat.wav` — 10 saniyelik, hızlanabilen kalp atışı
- `infrasound.wav` — 30 saniyelik, 20-30Hz basınç hissi

**SFX Sesleri:**
- Her bir SFX dosyası normalize edilmeli (aynı volume seviyesi)
- Bitrate: 44.1kHz, 16-bit, mono (stereo konumlandırma Web Audio'da yapılır)
- Dosya boyutu: Her biri < 200KB

**Stinger Sesleri:**
- Dramatik, kısa, etkili
- Reveal: Tek akor → reverb tail
- Crisis hit: Bas gümbürtüsü + cam kırılması
- Silence break: Tek piyano notası

**Kaynak Stratejisi:**
1. Ücretsiz siteler: freesound.org, pixabay.com/sound-effects
2. Web Audio API ile prosedürel üretim (özellikle drone ve infrasound)
3. Lisans kontrolü: CC0 veya CC-BY (attribution README'de)

---

### 7.2. Animasyon Zamanlama İyileştirmeleri

| Element | Mevcut | Hedef |
|---------|--------|-------|
| Chat açılma | Anında | 300ms fade-in + scale(0.95→1.0) |
| Chat kapanma | Anında | 200ms fade-out |
| Onboarding geçişi | Anında | 500ms slide + fade |
| Overlay text belirme | Lineer fade | Easing: ease-out-cubic |
| Glitch efekti başlangıç | Ani | 100ms ramp-up |
| Ambient crossfade | Lineer | S-curve (ease-in-out) |
| Typewriter duraklamaları | Sabit | Noktalama'da +200ms, virgülde +100ms |
| Fake notification | Anında | Sağdan kayarak giriş (Windows 11 stili) |
| Fake BSOD | Anında | 50ms beyaz flash → BSOD |

---

### 7.3. UX İyileştirmeleri

| İyileştirme | Açıklama |
|-------------|----------|
| Chat scroll | Son mesaj her zaman görünür, smooth scroll animation |
| Mesaj grubu | AI'nın ardışık mesajları arasında 1.5s bekleme |
| Input focus | Chat açıldığında input otomatik focus |
| Resize handle | Chat penceresinin köşesinde gizli resize göstergesi |
| Error feedback | API hatası → chat'te "..." 3 saniye → sessizce retry |
| Loading state | Onboarding "BAŞLA" sonrası 1s loading spinner (Python startup) |

---

### 7.4. Prompt İyileştirmeleri

Alpha testlerden gelen geri bildirimlere göre:
- System prompt'u inceltme (gereksiz kuralları kaldır)
- Türkçe dil kalitesini artırma (daha doğal konuşma)
- Faz geçiş prompt'larını ayarlama
- Offline template yanıtları çeşitlendirme (kategori başına 5+ şablon)

---

### 7.5. Görsel İyileştirmeler

| Element | İyileştirme |
|---------|-------------|
| Chat arka plan | Çok hafif noise texture (#0a0a0a üstünde %1 gürültü) |
| Kenarlık glow | Emotion'a göre renk değişimi (yeşil→kırmızı→mavi) |
| Cursor | Chat'te custom cursor (küçük, neon) |
| Scrollbar | Custom slim scrollbar (koyu gri, hover'da belirir) |
| BSOD | QR kod detayı, progress bar animasyonu |
| Overlay text | Text-shadow derinliği ayarı (stilden stile farklı) |

---

## Faz 7 Çıkış Kriterleri

- [ ] Tüm ses dosyaları mevcut ve doğru çalıyor
- [ ] Drone loop'lar seamless (pop/click yok)
- [ ] Animasyonlar smooth ve zamanlı
- [ ] Chat UX pürüzsüz (scroll, focus, resize)
- [ ] Prompt kalitesi artırılmış (Türkçe doğallık)
- [ ] Görsel detaylar eklenmiş (noise, glow, cursor)
- [ ] 35 dk playthrough premium hissediyor
