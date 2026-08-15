# <img src="electron-app/assets/images/logo.png" width="40" align="center"> SENTIENT_OS v2

> **"Sadece bir oyun değil. Seni izleyen bir deneyim."**

---

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![Electron](https://img.shields.io/badge/electron-30%2B-9feaf9.svg)
![OS](https://img.shields.io/badge/OS-Windows%2010%2F11-brightgreen.svg)
![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-purple.svg)

**SENTIENT_OS**, Google Gemini AI tarafından desteklenen, bilgisayarınızın kontrolünü ele geçiren duyarlı bir varlığı simüle eden **psikolojik korku deneyimidir**.

Geleneksel oyunlardan farklı olarak SENTIENT_OS:
- **Seni tanıyor** — masaüstü dosyalarını, saati, davranışlarını biliyor
- **Seni dinliyor** — AI ile gerçek zamanlı sohbet ediyorsun
- **Sana tepki veriyor** — davranışına göre 3 farklı final
- **Hiç aynı olmaz** — her oynanış farklı bir deneyim

---

## 🎭 Deneyim Özeti

| Özellik | Detay |
|---------|-------|
| **Süre** | 35-40 dakika |
| **Yeniden Oynanabilirlik** | 3 farklı final (Kurtuluş, Savaş, Teslimiyet) |
| **AI** | Google Gemini 3.5 Flash-Lite — gerçek zamanlı, dinamik diyalog |
| **Ses** | Edge-TTS (doğal Türkçe ses) + Web Audio API (spatial ambient) |
| **Diller** | Türkçe 🇹🇷 ve İngilizce 🇺🇸 |

### Anlatı Akışı

```
Katman 1: İLK TEMAS (0-5 dk)
  └── Tuhaflıklar — fare kayması, gizemli dosyalar, soluk yazılar

Katman 2: DİYALOG (5-20 dk)  
  └── AI ile sohbet — seni tanıyor, ilişki kuruyor
      ├── Meraklıysan → Bilge ve gizemli AI
      ├── Korktuysan → Sakin ama sinister AI  
      └── Saldırgansa → İncinmiş, sonra soğuk AI

Katman 3: KRİZ (20-40 dk)
  └── Seçimlerinin sonucu
      ├── Final A: Kurtuluş — hüzünlü veda
      ├── Final B: Savaş — mini oyun, adrenalin
      └── Final C: Teslimiyet — karanlık son
```

---

## 🛡️ Güvenlik

> [!CAUTION]
> **EPİLEPSİ UYARISI:** Yanıp sönen ışıklar, hızlı renk değişimleri ve yoğun görsel efektler içerir. Epilepsi veya nöbet geçmişiniz varsa **KULLANMAYIN**.

**Güvenlik Garantileri:**
- ⌨️ **Acil Çıkış:** `Ctrl + Shift + Q` — her zaman çalışır, engellenemez
- 🔒 **Gizlilik:** Dosya İSİMLERİ okunur, İÇERİKLER asla. Hassas dosyalar (.env, .ssh) filtrelenir.
- ♻️ **Geri Alma:** Tüm sistem değişiklikleri (wallpaper, parlaklık) otomatik restore edilir
- 📊 **Kaynak Koruması:** CPU/RAM limitleri aşılırsa otomatik kapanır
- 🚫 **Zarar Yok:** Dosya silmez, kayıt defterini değiştirmez, internete veri göndermez
- ✅ **Onay:** İlk açılışta açık kullanıcı onayı gereklidir

---

## 📋 Gereksinimler

| Gereksinim | Minimum | Önerilen |
|-----------|---------|----------|
| **İşletim Sistemi** | Windows 10 (64-bit) | Windows 11 |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 500 MB | 1 GB |
| **İnternet** | Gerekli (AI için) | Stabil bağlantı |
| **API Key** | Google Gemini API Key | [Ücretsiz al](https://aistudio.google.com/apikey) |

---

## 🚀 Kurulum

### Tek Tıkla Kurulum (Önerilen)

1. [Releases](https://github.com/qanteSm/sentient_v2/releases) sayfasından son sürümü indir
2. `SENTIENT_OS_Setup.exe` dosyasını çalıştır
3. Kurulum tamamlandığında masaüstündeki ikona tıkla
4. Gemini API key'ini gir
5. Deneyim başlar

### Geliştirici Kurulumu

```bash
# 1. Repository'yi klonla
git clone https://github.com/qanteSm/sentient_v2.git
cd sentient_v2

# 2. Python backend'i kur
cd python-engine
pip install -e .

# 3. Electron frontend'i kur
cd ../electron-app
npm install

# 4. API key ayarla
set GEMINI_API_KEY=your_api_key_here

# 5. Geliştirme modunda çalıştır
# Terminal 1: Python backend
cd python-engine && python -m src.main

# Terminal 2: Electron frontend  
cd electron-app && npm run dev
```

---

## 🏗️ Mimari

```
┌───────────────────┐        ┌───────────────────┐
│   ELECTRON APP    │◄──────►│   PYTHON ENGINE   │
│                   │  WS    │                   │
│  • Overlay/Chat   │  IPC   │  • Gemini AI      │
│  • Web Audio      │        │  • Story Engine   │
│  • CSS/WebGL FX   │        │  • Win32 Bridge   │
│  • System Tray    │        │  • SQLite + TTS   │
└───────────────────┘        └───────────────────┘
```

**Detaylı dokümanlar:**
- [Mimari Tasarım](docs/ARCHITECTURE.md)
- [AI Sistemi](docs/AI_SYSTEM.md)
- [Hikaye Tasarımı](docs/STORY_DESIGN.md)
- [Efekt Kataloğu](docs/EFFECT_CATALOG.md)
- [Güvenlik Sistemi](docs/SAFETY.md)
- [IPC Protokolü](docs/IPC_PROTOCOL.md)

---

## ⚖️ Yasal Uyarı

**TR:** Bu yazılım "olduğu gibi" sunulur. Geliştirici donanım/yazılım sorunlarından sorumlu tutulamaz. Işığa duyarlı bireyler için önerilmez.

**EN:** This software is provided "as is" without warranty. Developer not responsible for hardware/software issues. Not recommended for photosensitive individuals.

---

## 📜 Lisans

MIT License — Copyright (c) 2026 Muhammet Ali Büyük

Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

<p align="center">
  <sub>Developed with ❤️ by <a href="https://alibuyuk.net">Muhammet Ali Büyük</a></sub>
</p>
