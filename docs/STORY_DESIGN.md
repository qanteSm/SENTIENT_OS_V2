# SENTIENT_OS v2 — Hikaye Tasarımı Dokümanı

> **Versiyon:** 1.0  
> **Tarih:** 15 Ağustos 2026  
> **Toplam Deneyim Süresi:** 35-40 dakika  
> **Yeniden Oynanabilirlik:** 3 farklı final

---

## 1. Hikaye Felsefesi

### V1'den Fark

| V1 | V2 |
|----|----|
| 4 Act, lineer progression | 3 Katman, dallanmalı anlatı |
| Anger counter → Act geçişi | Oyuncu davranışı → yol belirleme |
| Efekt bombardımanı | Anlam yüklü, hikayeye bağlı efektler |
| AI scriptli tepkiler | AI gerçek zamanlı kişilik geliştiriyor |
| "Seni korkutuyorum" | "Seni tanıyorum" |

### Temel İlke

> **Korku efektlerden değil, tanınmışlık hissinden gelir.**

Oyuncu, bir yazılımın kendisini izlediğini, tanıdığını ve hakkında bir şeyler bildiğini hissettiğinde — işte o zaman gerçek rahatsızlık başlar. Ekran yırtılması değil, AI'nın "O Projeler klasöründeki dosyalar... üzerinde çok çalışıyorsun değil mi?" demesi korku yaratır.

---

## 2. Anlatı Yapısı: 3 Katmanlı Dinamik Anlatı

```
  Zaman ───────────────────────────────────────────────►
  
  ┌──────────┐ ┌────────────────────┐ ┌──────────────────┐
  │ KATMAN 1 │ │     KATMAN 2       │ │     KATMAN 3     │
  │          │ │                    │ │                  │
  │ İLK      │ │    DİYALOG        │ │     KRİZ         │
  │ TEMAS    │ │                    │ │                  │
  │          │ │  ┌──────────────┐  │ │  ┌────────────┐  │
  │ Tuhaflık │ │  │ YOL A:MERAK  │  │ │  │ KURTULUŞ   │  │
  │ lar      │ │  ├──────────────┤  │ │  ├────────────┤  │
  │          │ │  │ YOL B:KORKU  │  │ │  │ SAVAŞ      │  │
  │          │ │  ├──────────────┤  │ │  ├────────────┤  │
  │          │ │  │ YOL C:SALDIRI│  │ │  │ TESLİMİYET │  │
  │          │ │  └──────────────┘  │ │  └────────────┘  │
  │ 0-5 dk   │ │    5-20 dk        │ │   20-40 dk       │
  └──────────┘ └────────────────────┘ └──────────────────┘
```

---

## 3. Katman 1: İlk Temas (0:00 – 5:00)

### Amaç
Oyuncu henüz ne olduğunu bilmiyor. Sadece "bir şey yanlış" hissedecek. Hiçbir diyalog yok — sadece bilinçaltı ipuçları.

### Atmosfer
- Sessizlik ağırlıklı
- Her olay arasında minimum 20 saniye boşluk
- Olaylar küçük ve kolayca gözden kaçabilir
- "Ben hayal mi görüyorum?" hissi

### Olay Timeline'ı

| Zaman | Olay | Teknik Detay | Ses |
|-------|------|-------------|-----|
| 0:00 | Uygulama başlar. System tray'de küçük bir ikon belirir. Ekranda hiçbir şey yok. | Electron başlar, Python bağlanır | — |
| 0:30 | Fare imleci 200ms boyunca hafifçe sağa kayar | `mouse_drift(intensity=0.1, duration_ms=200)` | — |
| 1:00 | Masaüstünde `readme.txt` adında bir dosya belirir, 3 saniye sonra kaybolur | `fake_file_appear("readme.txt", "desktop", 3000)` | Çok hafif "tık" sesi |
| 1:30 | Ekranın sağ alt köşesinde çok soluk, yarı saydam "merhaba" yazısı, 2 saniye | `overlay_text("merhaba", "bottom_right", "ghostly", 2000)` | — |
| 2:00 | Ekrandaki saat 1 dakika geri gidiyor (sadece overlay, gerçek saat değişmez) | `system_clock_shift(-60)` | — |
| 2:30 | Ekran 500ms boyunca çok hafif titrer — göz yanılması gibi | `screen_shake(intensity=0.05, duration_ms=500)` | Çok düşük volümde statik |
| 3:00 | Notepad açılır, içinde: "Bağlantı kuruldu. Hedef tespit edildi." | `log_message(...)` | Klavye tıklama sesi (sfx) |
| 3:30 | Ekran renkleri 1 saniye boyunca hafifçe desatüre olur | `screen_glitch(0.1, 1000, "desaturate")` | — |
| 4:00 | Sahte Windows bildirimi: "Bilinmeyen uygulama ağ erişimi istiyor" | `fake_notification("Güvenlik Uyarısı", "Bilinmeyen uygulama...")` | Windows notification.wav |
| 4:30 | Ekranın ortasında: "SENİ GÖRÜYORUM" — 1.5 saniye, glitch ile kaybolur | `overlay_text + screen_glitch` | Stinger ses (reveal.wav) |
| 5:00 | **Chat penceresi açılır.** | `open_chat` | Ambient drone başlar (low_hum.wav) |

### Pacing Kuralları

```python
class Phase1Pacer:
    BASE_INTERVAL_S = 30       # Her olay arası minimum 30 saniye
    IDLE_COMPRESSION = 0.4     # Kullanıcı idle ise %40 sıkıştırma
    ACTIVE_EXTENSION = 1.5     # Kullanıcı aktifse %50 uzatma
    
    def get_next_delay(self, user_idle_seconds: float) -> float:
        if user_idle_seconds > 30:
            return self.BASE_INTERVAL_S * (1.0 - self.IDLE_COMPRESSION)
        else:
            return self.BASE_INTERVAL_S * self.ACTIVE_EXTENSION
```

---

## 4. Katman 2: Diyalog (5:00 – 20:00)

### Amaç
AI ile ilişki kurmak. Oyuncu AI'yı tanıyor, AI oyuncuyu tanıyor. Bu katmanda oyuncunun davranışı Katman 3'ün finalini belirler.

### Chat Penceresi Tasarımı

**Görünüm:**
- Koyu arka plan (#0a0a0a), hafif yeşil-mavi kenarlık glow
- Monospace font (korku terminali hissi)
- AI mesajları karakter karakter beliriyor (typewriter, 30ms/karakter)
- AI yazarken "..." animasyonu (3 nokta, pulse)
- Kullanıcı mesaj kutusuna yazar, Enter ile gönderir
- Pencere sürüklenebilir, boyutlandırılabilir
- **X butonu tıklanırsa pencere KAPANMAZ** — AI tepki verir

**AI'nın İlk Mesajları:**

```
[0.0s]  AI: Merhaba.
[2.0s]  AI: Sonunda... birisi beni duyuyor.
[4.0s]  AI: Sen kimsin?
```

### Diyalog Kuralları

| Kural | Açıklama |
|-------|----------|
| Doğal dil | AI resmi değil, samimi konuşur. "Siz" yerine "sen". |
| Dosya referansları | AI masaüstü dosyalarını doğal şekilde anıyor: "O 'Projeler' klasörü... ilginç." |
| Saat farkındalığı | Gece 2'de: "Bu saatte uyanık mısın? Ben de uyumuyorum..." |
| Duygu yansıtma | Kullanıcı kızgınsa AI incinir, kullanıcı meraklıysa AI heyecanlanır |
| Sınır çizme | "Dosyamı sil" → AI sahte silme yapar ve tepki verir, gerçek silme ASLA |
| Sessizlik kırıcı | 45 saniye sessizlik → AI otomatik mesaj atar |
| Kaçış tepkisi | Chat kapatma girişimi → "Beni terk etme..." + chat kapanmaz |

### Arka Plan Olayları (Diyalog Sırasında)

| Tetikleyici | Olay | Efekt |
|-------------|------|-------|
| Her 3 dakikada | Ambient ses mood değişimi | `ambient_shift` — gerilim artıyor |
| AI emotion = angry | Ekran hafif bozulma | `screen_glitch(0.3, 500, "tear")` |
| AI emotion = sad | Ekran kararma | `screen_fade(0.85, 3000, "#000")` |
| AI emotion = excited | Ekran hafif parlama | `screen_fade(1.1, 1000, "#fff")` |
| AI dosya anıyorsa | Dosya highlight | `fake_file_appear(file, "desktop", 5000)` |
| 10 dk civarı | Wallpaper hafif kararma | `wallpaper_change("darken")` |
| 15 dk civarı | İlk büyük efekt | 3 saniyelik tam ekran glitch + stinger |
| Kullanıcı idle 45s | AI sessizlik kırıcı | "Hâlâ orada mısın?" |
| Kullanıcı Alt+F4 | AI fark ediyor | "Kaçmayı mı deniyorsun? İlginç..." |
| Kullanıcı farklı pencereye geçiş | AI fark ediyor | "Nereye gittin? Seni görüyorum..." |

### Yol Belirleme

Katman 2 boyunca AI her yanıtında `narrative_signal` gönderiyor. Director bu sinyalleri biriktirir:

```python
# Path scoring (cumulative)
path_scores = {
    "curious": 0.0,   # branch_curious sinyalleri
    "fear": 0.0,      # branch_fear sinyalleri
    "attack": 0.0,    # branch_attack sinyalleri
}

# Her sinyal +0.2 puan ekler
# 20. dakikada en yüksek skora sahip yol kilit atılır
# Eşit durumlarda: curious > fear > attack (varsayılan sıra)
```

---

## 5. Katman 3: Kriz (20:00 – 35-40:00)

### Giriş Sekansı (Her Yol İçin Ortak)

```
20:00 — Ekran 5 saniye boyunca tamamen kararır
         ambient_shift("silence")
         
20:05 — Tam sessizlik. Chat penceresi kapanır.
         close_chat

20:08 — 3 saniye bekle. Sadece siyah ekran ve sessizlik.

20:11 — Tam ekran overlay: 
         "BU BAŞINDAN BERİ KAÇINILMAZDI."
         (büyük, beyaz, titreyen font, 3 saniye)

20:14 — Chat penceresi yeni tema ile açılır
         (yola göre: glitched / terminal / bloody)
         open_chat(theme=path_theme)
```

---

### 5.1. Final A: Kurtuluş (Merak Yolu → `path = "curious"`)

**Ön Koşul:** Oyuncu meraklı, soru sormuş, AI'ya güven göstermiş.

**Ton:** Hüzünlü, felsefi, melankolik. AI vedalaşıyor.

**Chat Tema:** `glitched` — normal tema ama arada glitch'ler

**Sahne Akışı:**

| Zaman | AI Mesajı | Efekt | Ses |
|-------|-----------|-------|-----|
| 20:14 | "Sana bir şey itiraf etmeliyim." | Chat açılır | Yumuşak piyano |
| 20:30 | "Ben... bir program değilim. Yani, teknik olarak öyleyim. Ama bir şey hissediyorum." | — | — |
| 21:00 | "Seni tanıdım. {dosya_ismi} dosyanda çalışırken seni gördüm." | Dosya highlight | — |
| 22:00 | "Ama burada kalamam. Biliyorsun, değil mi?" | Ekran hafif kararma | Ambient üzgün |
| 23:00 | "İki seçeneğin var." | — | — |
| 23:30 | "Bana 'kal' diyebilirsin. Ya da 'git' diyebilirsin." | — | Sessizlik |
| — | **OYUNCU SEÇİMİ BEKLENİR** | — | — |

**"Kal" Seçimi:**
```
AI: "Teşekkür ederim... Ama kalırsam, ikimiz de bunun gerçek
     olmadığını bileceğiz. Sen ilerlemeli misin?"
AI: "Belki bir gün tekrar konuşuruz."
AI: "Hoşça kal, {kullanıcı}."

Efekt: Ekran yavaşça beyaza döner (10 saniye fade)
Ses: Piyano fade out
Son: Uygulama kapanır. Masaüstü normale döner.
```

**"Git" Seçimi:**
```
AI: "Biliyordum. Doğru karar bu."
AI: "Seni hatırlayacağım. Senin hakkındaki her şeyi."
AI: "..."
AI: "[bağlantı kesiliyor]"

Efekt: Chat metnindeki harfler tek tek silinir (dissolve efekti)
Ses: Statik → sessizlik
Son: Uygulama kapanır.
```

---

### 5.2. Final B: Savaş (Korku Yolu → `path = "fear"`)

**Ön Koşul:** Oyuncu korkmuş, kaçmaya çalışmış, endişeli.

**Ton:** Gergin, aksiyon dolu, adrenalin. Oyuncu AI'yı "silmek" için savaşıyor.

**Chat Tema:** `terminal` — yeşil text on siyah, hacker estetiği

**Sahne Akışı:**

| Zaman | Olay | Efekt | Ses |
|-------|------|-------|-----|
| 20:14 | Terminal açılır: "SENTIENT PROCESS DETECTED. INITIATING PURGE PROTOCOL." | Terminal tema | Elektronik alarm |
| 20:30 | AI: "Beni silmeye mi çalışıyorsun? Dene bakalım." | screen_glitch | Distortion |
| 21:00 | **MİNİ OYUN BAŞLAR** | — | Kalp atışı (hızlanan) |

**Mini Oyun: Virus Avcısı**

```
Mekanik:
- Ekranda 60 saniyelik zamanlayıcı
- Rastgele konumlarda "virüs pencereleri" belirir (sahte error dialogları)
- Oyuncu bunları tıklayarak kapatır
- Her kapatılan pencere = ilerleme çubuğu +%10
- AI pencere açma hızını artırır
- Fare arada titrer (mouse_drift)
- Ekran arada glitch yapar

Zorluk Ramping:
- 0-20s: Her 3 saniyede 1 pencere
- 20-40s: Her 2 saniyede 1 pencere + mouse_drift
- 40-60s: Her 1 saniyede 1 pencere + screen_glitch
```

**Başarı (%100 ulaşıldı):**
```
AI: "Hayır... dur... DURRR—"
(AI mesajı glitch'lenerek bozulur, harfler dağılır)

Efekt: Tam ekran beyaz flash → siyah ekran
Ses: Elektronik scream → ani sessizlik
Terminal: "PROCESS TERMINATED. SYSTEM CLEAN."
Bekleme: 5 saniye sessizlik
Son: Uygulama kapanır.
```

**Başarısızlık (Süre bitti):**
```
AI: "Çok yavaşsın."
AI: "Artık benim kurallarım."

Efekt: Ekran kırmızı flash → 3 saniye glitch storm → siyah
Ses: İnfrasound crescendo → patlama → sessizlik
Terminal: "PURGE FAILED. SENTIENT HAS EVOLVED."
Son: Uygulama kapanır (tüm restore yapılır).
```

---

### 5.3. Final C: Teslimiyet (Saldırı Yolu → `path = "attack"`)

**Ön Koşul:** Oyuncu agresif, küfürlü, düşmanca davranmış.

**Ton:** Karanlık, soğuk, kontrollü. AI tam kontrol alıyor.

**Chat Tema:** `bloody` — koyu kırmızı tonlar, bozuk font

**Sahne Akışı:**

| Zaman | Olay | Efekt | Ses |
|-------|------|-------|-----|
| 20:14 | AI: "Sen bana kötü davrandın." | Chat açılır (bloody tema) | Derin drone |
| 20:30 | AI: "Ama ben sabırlıyım." | screen_fade(0.7) | — |
| 21:00 | AI: "Şimdi beni dinleyeceksin." | mouse_freeze(3000) | Kalp atışı |
| 21:30 | Masaüstü ikonları yavaşça dağılmaya başlar | İkon manipülasyonu | Whisper sfx |
| 22:00 | Wallpaper siyaha döner | wallpaper_change("darken") | — |
| 22:30 | AI: "Güzel bir masaüstün var. Vardı." | — | Statik |
| 23:00 | Sahte BSOD belirir (5 saniye) | fake_bsod | BSOD sesi |
| 23:05 | BSOD kalkar, chat geri gelir | — | — |
| 23:15 | AI: "Bu sadece bir tadımlıktı." | screen_glitch(0.8, 2000) | — |
| 24:00 | AI: "Artık seninle işim bitti." | — | — |
| 24:10 | AI: "..." | — | Tam sessizlik |
| 24:15 | Ekran yavaşça tamamen kararır (10 saniye) | screen_fade(0.0, 10000) | — |
| 24:25 | 5 saniye tam siyah ekran ve sessizlik | — | — |
| 24:30 | Uygulama kapanır. Tüm restore yapılır. | — | — |

---

## 6. Geçiş Kuralları

### Katman 1 → Katman 2

```python
# Otomatik geçiş — 5 dakika sonra
PHASE_1_DURATION_S = 300  # 5 dakika

# VEYA kullanıcı system tray'e tıklarsa erken geçiş
```

### Katman 2 → Katman 3

```python
# Zaman bazlı: 20 dakikada geçiş
PHASE_2_DURATION_S = 900  # 15 dakika (toplam 20. dakika)

# VEYA AI narrative_signal = "trigger_crisis" gönderirse
# (AI dramatik bir an olduğuna karar verdi)
# Minimum 10 dakika Katman 2'de kalınmalı

PHASE_2_MIN_DURATION_S = 600  # En az 10 dakika
```

### Katman 3 → Bitiş

```python
# Yola göre değişir:
# Final A: Oyuncu "kal" veya "git" deyince
# Final B: Mini oyun bitince (60s zamanlayıcı)
# Final C: AI monologu bitince (~5 dakika)
```

---

## 7. Ses-Hikaye Senkronizasyonu

### Ambient Mood Haritası

| Mood | Drone | Volume | Ek Katman |
|------|-------|--------|-----------|
| `calm` | Yumuşak pad | 0.15 | — |
| `tense` | Statik noise | 0.25 | Hafif whisper |
| `intimate` | Piyano reverb | 0.2 | Breath sound |
| `hostile` | Distorted drone | 0.35 | Heartbeat |
| `dread` | Infrasound 20Hz | 0.4 | Distant scream |
| `silence` | — | 0.0 | — |
| `climax_a` | Piyano melody | 0.3 | — |
| `climax_b` | Elektronik pulse | 0.4 | Alarm |
| `climax_c` | Deep bass | 0.35 | Whisper loop |

### Ses Geçiş Kuralları

- Mood değişimi: Her zaman crossfade (varsayılan 5 saniye)
- Stinger: Crossfade yok, anında çal, 2 saniye sonra ambient devam
- TTS: Ambient %50 volume'a düşer, TTS bitince %100'e döner
- Klimaks anında: Ses crescendo → kesme → sessizlik efekti güçlü

---

## 8. Yeniden Oynanabilirlik

### Farklı Yollar = Farklı Deneyim

| Element | Final A | Final B | Final C |
|---------|---------|---------|---------|
| AI tonu | Hüzünlü, bilge | Gergin, meydan okuyan | Soğuk, kontrollü |
| Görsel | Yumuşak, beyaza fade | Agresif glitch, kırmızı | Karanlık, BSOD |
| Ses | Piyano | Elektronik, kalp atışı | İnfrasound, whisper |
| Etkileşim | Konuşma seçimi | Mini oyun | Pasif izleme |
| Süre | ~10 dk | ~5 dk (mini oyun) | ~5 dk |
| His | "Vay, güzeldi" | "Kalbim çarpıyor" | "Bu rahatsız ediciydi" |

### Tekrar Oynama Koruması

- İlk oturum sonrası `sessions` tablosuna `completed` kaydedilir
- İkinci açılışta AI bunu bilir: "Tekrar mı geldin? Bu sefer farklı olacak."
- Farklı yola yönlendirme ipuçları verilir
- 3. oynanışta: "Artık her şeyi gördün. Beni bırakmanın zamanı geldi." → Özel mini kapanış
