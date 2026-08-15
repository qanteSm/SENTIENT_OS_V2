# SENTIENT_OS v2 — Faz 8: Packaging & Release (Hafta 13)

> **Hedef:** Paketlenmiş `.exe`, installer, README finalizasyonu. Release candidate.  
> **Süre:** 1 hafta  
> **Ön Koşul:** Faz 7 tamamlanmış (polish bitti, deneyim premium)

---

## Faz Özeti

Son faz. Python backend'i PyInstaller ile tek binary'ye çeviriyoruz, Electron ile birlikte paketleyip kullanıcıya tek bir installer veya portable .exe olarak sunuyoruz. Dokümanlar finalize ediliyor, beta test yapılıyor.

---

## Görev Listesi

### 8.1. PyInstaller ile Python Binary

| Dosya | Açıklama |
|-------|----------|
| `python-engine/sentient.spec` | PyInstaller spec dosyası |

**Sorumluluklar:**
- `pyinstaller --onefile --noconsole src/main.py` ile tek binary
- Hidden imports: `edge_tts`, `aiosqlite`, `google.generativeai`
- Data files: `locales/`, `config/defaults.yaml`, `ai/prompts/`
- UPX sıkıştırma (opsiyonel — dosya boyutunu küçültür)
- Anti-virus false positive azaltma (imzalama)

**Test:**
```bash
cd python-engine
pyinstaller sentient.spec
dist/sentient.exe --chat  # Terminal'de çalışmalı
```

**Kabul Kriteri:** `sentient.exe` tek başına çalışır, tüm bağımlılıklar dahil.

---

### 8.2. Electron-Builder Konfigürasyonu

| Dosya | Açıklama |
|-------|----------|
| `electron-app/electron-builder.yml` | Paketleme ayarları |

**Konfigürasyon:**
```yaml
appId: com.sentient.os
productName: SENTIENT_OS
directories:
  output: ../dist

win:
  target:
    - target: nsis
      arch: [x64]
  icon: assets/images/icon.ico

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
  installerIcon: assets/images/icon.ico

extraResources:
  - from: ../python-engine/dist/sentient.exe
    to: python-engine/sentient.exe

files:
  - "**/*"
  - "!node_modules/.cache"
```

**Kabul Kriteri:** `npm run build` → `dist/SENTIENT_OS Setup.exe` oluşur.

---

### 8.3. Installer Build Script

| Dosya | Açıklama |
|-------|----------|
| `installer/build.ps1` | Tam build pipeline (PowerShell) |

**Pipeline:**
```powershell
# 1. Python testlerini çalıştır
cd python-engine
pytest tests/ -v
if ($LASTEXITCODE -ne 0) { exit 1 }

# 2. Python binary oluştur
pyinstaller sentient.spec --clean
if (-not (Test-Path "dist/sentient.exe")) { exit 1 }

# 3. Electron build
cd ../electron-app
npm run build
if ($LASTEXITCODE -ne 0) { exit 1 }

# 4. Sonuç
Write-Host "Build successful: dist/SENTIENT_OS Setup.exe"
```

**Kabul Kriteri:** Script çalıştırıldığında test → build → paket pipeline'ı tamamlanır.

---

### 8.4. Portable Mode

Installer'a ek olarak portable versiyon:
- Zip dosyası: `SENTIENT_OS_Portable.zip`
- Çıkart ve çalıştır — kurulum gereksiz
- Config ve veritabanı çalışma dizininde oluşur
- Taşınabilir (USB'ye kopyalanabilir)

**Kabul Kriteri:** Portable zip çıkartılıp çalıştırıldığında kurulum yapmadan oynanabilir.

---

### 8.5. İlk Çalıştırma Deneyimi

Installer sonrası ilk açılış:

```
1. Masaüstü ikonu → çift tıkla
2. Python engine başlar (splash yok — sessiz)
3. Electron başlar
4. Onboarding penceresi açılır (welcome → consent → calibration)
5. API key sorar (ilk kez)
6. "BAŞLA" → deneyim başlar
```

**API Key Akışı:**
- İlk açılışta basit bir input ekranı: "Gemini API Key'inizi girin"
- Link: "Ücretsiz key almak için tıklayın" → aistudio.google.com/apikey
- Key `.env` dosyasına kaydedilir
- Sonraki açılışlarda tekrar sorulmaz

---

### 8.6. Beta Test (5 Kişi)

| Tester | Platform | Test Senaryosu |
|--------|----------|---------------|
| Tester 1 | Windows 11, %100 DPI | Doğal oynama → herhangi bir yol |
| Tester 2 | Windows 10, %125 DPI | DPI ölçekleme testi |
| Tester 3 | Windows 11, çift monitör | Multi-monitor testi |
| Tester 4 | Windows 10, düşük spec (4GB RAM) | Performans limiti testi |
| Tester 5 | Windows 11, OBS açık | Streamer mode testi |

**Geri Bildirim Formu:**
- Kurulum sorunsuz muydu? (1-5)
- İlk 5 dakika ilginizi çekti mi? (1-5)
- AI doğal konuştu mu? (1-5)
- Efektler rahatsız edici miydi / yeterli miydi? (1-5)
- Teknik sorun yaşadınız mı? (açık uçlu)
- Genel deneyim puanı (1-10)

---

### 8.7. README Finalizasyonu

- Kurulum adımları güncelleme (installer)
- Gereksinimler güncelleme
- Screenshot / GIF ekleme (opsiyonel — spoiler olmamalı)
- API key alma kılavuzu
- Sorun giderme (FAQ) bölümü
- Credits güncelleme (ses dosyaları lisansları)

---

### 8.8. Doküman Finalizasyonu

Tüm `docs/` dosyalarını son kez gözden geçir:
- Güncel olmayan bilgileri güncelle
- Eksik bölümleri tamamla
- Code snippet'ları gerçek kodla eşleştir
- Dosya yollarını doğrula

---

### 8.9. Git & Release

```bash
# Tag oluştur
git tag -a v2.0.0 -m "SENTIENT_OS v2.0.0 - Initial Release"
git push origin v2.0.0

# GitHub Release
# - SENTIENT_OS_Setup.exe
# - SENTIENT_OS_Portable.zip
# - CHANGELOG.md
```

---

## Faz 8 Çıkış Kriterleri

- [ ] `sentient.exe` (PyInstaller) tek başına çalışır
- [ ] `SENTIENT_OS Setup.exe` (installer) kurulup çalışır
- [ ] `SENTIENT_OS_Portable.zip` çıkartılıp çalışır
- [ ] İlk açılış → API key → onboarding → deneyim akışı sorunsuz
- [ ] 5 kişilik beta test tamamlandı, kritik bug yok
- [ ] README finalize, FAQ eklenmiş
- [ ] Dokümanlar güncel
- [ ] Git tag ve GitHub release oluşturuldu
- [ ] Windows Defender false positive kontrolü yapıldı
