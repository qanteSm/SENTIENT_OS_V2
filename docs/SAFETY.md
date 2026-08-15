# SENTIENT_OS v2 — Güvenlik Sistemi Dokümanı

> **Versiyon:** 1.0  
> **Tarih:** 15 Ağustos 2026  
> **Öncelik:** Güvenlik her zaman işlevsellikten önce gelir.

---

## 1. Güvenlik Felsefesi

SENTIENT_OS bir korku deneyimidir ama **gerçek zarar vermez**. Güvenlik sistemi 5 katmandan oluşur:

1. **Kill Switch** — Anında çıkış (izole thread)
2. **Resource Guard** — Sistem kaynaklarını izleme
3. **Panic Detection** — Oyuncu panik belirtileri algılama
4. **Privacy Filter** — Hassas dosya/veri filtreleme
5. **State Restore** — Tüm değişiklikleri geri alma

---

## 2. Kill Switch (İzole Thread)

### Tasarım

Kill switch, Python main loop'undan ve Electron IPC'sinden **tamamen bağımsız** çalışır. Hiçbir durumda bloklanamaz.

```
┌──────────────────────────────────┐
│        KILL SWITCH THREAD        │
│                                  │
│  RegisterHotKey(Ctrl+Shift+Q)    │
│           │                      │
│           ▼                      │
│  Tetiklendiğinde:                │
│  1. Emergency checkpoint kaydet  │
│  2. Sistem değişikliklerini      │
│     restore et (wallpaper,       │
│     brightness)                  │
│  3. Electron process'i öldür     │
│     (taskkill /F /T)             │
│  4. os._exit(0)                  │
│                                  │
│  Bu thread ASLA:                 │
│  • Event bus'a bağlı değil       │
│  • WebSocket'e bağlı değil       │
│  • AI response beklemez          │
│  • Herhangi bir lock tutmaz      │
└──────────────────────────────────┘
```

### Implementasyon

```python
import ctypes
import threading
import os
import subprocess

class IsolatedKillSwitch:
    HOTKEY_ID = 1
    MOD_CTRL = 0x0002
    MOD_SHIFT = 0x0004
    VK_Q = 0x51
    WM_HOTKEY = 0x0312
    
    def __init__(self, restore_callback, electron_pid: int = None):
        self._restore_callback = restore_callback
        self._electron_pid = electron_pid
        self._thread = threading.Thread(target=self._listen, daemon=True)
    
    def start(self):
        self._thread.start()
    
    def _listen(self):
        user32 = ctypes.windll.user32
        user32.RegisterHotKey(None, self.HOTKEY_ID, 
                             self.MOD_CTRL | self.MOD_SHIFT, self.VK_Q)
        
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == self.WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                self._emergency_shutdown()
                break
        
        user32.UnregisterHotKey(None, self.HOTKEY_ID)
    
    def _emergency_shutdown(self):
        # 1. Restore sistem değişiklikleri
        try:
            self._restore_callback()
        except Exception:
            pass  # Restore başarısız olsa bile çık
        
        # 2. Electron process'i öldür
        if self._electron_pid:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self._electron_pid)],
                    capture_output=True, timeout=3
                )
            except Exception:
                pass
        
        # 3. Anında çık
        os._exit(0)
```

### Yedek Kill Switch (Electron Tarafı)

Electron'da da bir yedek kill switch dinleyicisi var:

```typescript
// main/kill-switch.ts
import { globalShortcut, app } from 'electron';

export function registerKillSwitch() {
    globalShortcut.register('Ctrl+Shift+Q', () => {
        console.log('[KILL SWITCH] Emergency shutdown triggered');
        // Python process'e shutdown mesajı gönder
        ipcBridge.send({ type: 'kill_switch' });
        // 2 saniye bekle, sonra zorla kapat
        setTimeout(() => {
            app.exit(0);
        }, 2000);
    });
}
```

---

## 3. Resource Guard

### İzleme Metrikleri

```python
RESOURCE_LIMITS = {
    # CPU
    "cpu_warning": 80,       # %80 → uyarı logu
    "cpu_critical": 90,      # %90 → graceful shutdown
    
    # RAM
    "total_ram_warning_mb": 500,   # Toplam > 500MB → uyarı
    "total_ram_critical_mb": 750,  # Toplam > 750MB → shutdown
    "python_ram_max_mb": 200,      # Python > 200MB → bellek temizliği
    "electron_ram_max_mb": 350,    # Electron > 350MB → uyarı
    
    # Disk
    "disk_write_max_mb_per_min": 50,  # Dakikada > 50MB → sorun var
    
    # İzleme aralığı
    "check_interval_seconds": 5,
}
```

### İzleme Akışı

```python
async def resource_guard_loop():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.Process().memory_info().rss / 1024 / 1024
        
        if cpu > LIMITS["cpu_critical"]:
            logger.critical(f"CPU critical: {cpu}%")
            await event_bus.publish("safety.shutdown", reason="CPU overload")
            
        elif cpu > LIMITS["cpu_warning"]:
            logger.warning(f"CPU warning: {cpu}%")
        
        if ram > LIMITS["total_ram_critical_mb"]:
            logger.critical(f"RAM critical: {ram}MB")
            await event_bus.publish("safety.shutdown", reason="RAM overload")
            
        elif ram > LIMITS["total_ram_warning_mb"]:
            logger.warning(f"RAM warning: {ram}MB")
            # Bellek temizliği dene
            await event_bus.publish("safety.memory_pressure")
        
        await asyncio.sleep(LIMITS["check_interval_seconds"])
```

---

## 4. Panic Detection

### Panik Tetikleyicileri

| Tetikleyici | Eşik | Aksiyon |
|-------------|-------|--------|
| ESC spam | 2 saniyede 5+ ESC basma | Graceful shutdown |
| Alt+F4 spam | 5 saniyede 3+ Alt+F4 | Graceful shutdown |
| Mouse köşe | (0,0) köşede 3 saniye tutma | Graceful shutdown |
| Rapid clicking | 3 saniyede 20+ tıklama | Yoğunluk düşür (%50) |
| Task Manager açma | `taskmgr.exe` algılanırsa | Yoğunluk düşür |

### Panic Response

```python
async def handle_panic(trigger: str):
    logger.warning(f"Panic detected: {trigger}")
    
    if trigger in ["esc_spam", "alt_f4_spam", "mouse_corner"]:
        # Graceful shutdown — tüm efektleri kapat, restore et, çık
        await event_bus.publish("effects.stop_all")
        await event_bus.publish("session.graceful_shutdown")
    
    elif trigger in ["rapid_clicking", "task_manager"]:
        # Yoğunluk düşür — agresif efektleri azalt
        await event_bus.publish("effects.reduce_intensity", factor=0.5)
        # 30 saniye sonra normal yoğunluğa dön
        await asyncio.sleep(30)
        await event_bus.publish("effects.restore_intensity")
```

---

## 5. Privacy Filter

### Prensip

> **Oyuncunun bilgisayarında ne varsa onun mahremiyetidir. Biz sadece isimlerine bakıyoruz, içeriklerine asla.**

### Taranacak Alanlar (Whitelist)

```python
SCAN_WHITELIST = [
    # Sadece bu klasörler taranır
    "Desktop",       # Masaüstü
    "Documents",     # Belgelerim (1 seviye derinlik)
    "Downloads",     # İndirilenler (1 seviye derinlik)
]

# Toplanan bilgi: SADECE dosya/klasör İSİMLERİ
# Dosya İÇERİĞİ asla okunmaz
# Tam dosya yolları (C:\Users\...) AI'ya gönderilmez
# Sadece isimler gönderilir: ["Projeler", "cv.pdf", "notlar.txt"]
```

### Yasaklı Dosya/Yol Kalıpları (Blacklist)

```python
BLACKLISTED_PATTERNS = [
    # === Güvenlik Dosyaları ===
    ".env", ".env.*", ".env.local", ".env.production",
    ".ssh/", ".ssh\\",
    "id_rsa", "id_ed25519", "id_ecdsa",
    "*.pem", "*.key", "*.crt", "*.pfx",
    "*.kdbx",           # KeePass veritabanı
    "*.keystore",
    "*.jks",             # Java keystore
    
    # === Şifre/Gizli Bilgi ===
    "*password*",
    "*parola*",
    "*sifre*",
    "*şifre*",
    "*secret*",
    "*credential*",
    "*token*",
    "*api_key*",
    "*apikey*",
    
    # === Tarayıcı Verileri ===
    "*/Chrome/User Data/*",
    "*/Firefox/Profiles/*",
    "*/Edge/User Data/*",
    "*Cookies*",
    "*Login Data*",
    
    # === Sistem Dizinleri ===
    "C:/Windows/",
    "C:/Program Files/",
    "C:/Program Files (x86)/",
    "%APPDATA%/",
    "%LOCALAPPDATA%/",
    
    # === Büyük/Gereksiz ===
    "node_modules/",
    ".git/",
    "__pycache__/",
    "*.exe", "*.dll", "*.sys", "*.msi",
    
    # === Kişisel Medya (içerik anlamı çıkarılmasın) ===
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.mp4", "*.avi",
    # NOT: Dosya İSİMLERİ geçebilir (ör: "tatil_fotoğrafları/"),
    # ama dosya İÇERİĞİ (resimler) ASLA işlenmez.
]
```

### Filtreleme Pipeline

```
Dosya Sistemi
    │
    ▼
Scanner: Whitelist klasörleri tara (maks 1 seviye derinlik)
    │
    ▼
Blacklist Filter: Yasaklı kalıplara uyanları at
    │
    ▼
İsim Çıkarma: Tam yolları kaldır, sadece dosya/klasör ismini tut
    │
    ▼
Limitleme: Maks 30 isim (geri kalanı atılır)
    │
    ▼
AI Context'e ekle: ["Projeler", "Ödevler", "cv.pdf", "notlar.txt"]
```

### Uygulama Kuralları

1. Filtreleme **senkron** ve **başlangıçta bir kez** yapılır (sürekli tarama yok).
2. Reddedilen dosyalar **loglanmaz** bile (gizlilik).
3. Kullanıcıya hangi dosyaların tarandığı **gösterilmez** (immersion).
4. AI'ya gönderilen context'te tam yol ASLA yer almaz.
5. AI'nın `known_files` listesi oturum sonunda silinmez (kalıcı profil), ancak kullanıcı isterse silebilir.

---

## 6. State Restore (Geri Alma Garantisi)

### Kaydedilen Orijinal Durumlar

| Durum | Kaydetme Anı | Geri Alma Anı |
|-------|-------------|---------------|
| Masaüstü wallpaper yolu | Oturum başlangıcı | Oturum sonu / kill switch |
| Ekran parlaklığı | Oturum başlangıcı | Oturum sonu / kill switch |
| Fare hızı/hassasiyeti | Oturum başlangıcı | Oturum sonu / kill switch |
| Masaüstü ikon pozisyonları | Oturum başlangıcı | Oturum sonu / kill switch |

### Restore Sırası

```python
async def restore_all():
    """
    Bu fonksiyon şu durumlarda çağrılır:
    1. Normal oturum sonu (final sonrası)
    2. Kill switch tetiklendiğinde
    3. Crash recovery sırasında
    4. Resource guard shutdown'ında
    """
    restore_steps = [
        ("Wallpaper", restore_wallpaper),
        ("Brightness", restore_brightness),
        ("Mouse speed", restore_mouse_settings),
        ("Icon positions", restore_icon_positions),
        ("TTS temp files", cleanup_tts_temp_files),   # ← Edge-TTS orphan cleanup
        ("All temp files", cleanup_temp_files),
        ("Overlay windows", close_all_overlays),
    ]
    
    for name, func in restore_steps:
        try:
            await func()
            logger.info(f"Restored: {name}")
        except Exception as e:
            logger.error(f"Failed to restore {name}: {e}")
            # Devam et — diğer restore'ları da dene
```

### ⚠️ Edge-TTS Temp Dosya Yönetimi

> [!WARNING]
> Kullanıcı seri mesaj yazdığında veya acil çıkış (kill switch) yapıldığında diskte yetim (orphan) `.mp3` dosyaları kalabilir. Bu dosyalar birikerek disk alanını tüketir.

**Çözüm (zorunlu):** Temp dosyalar iki noktada temizlenir:

```python
import glob
import os

TEMP_DIR = "temp/"

async def cleanup_tts_temp_files():
    """
    Çağrılma noktaları:
    1. Oturum başlangıcında (önceki oturumdan kalan orphan'lar)
    2. restore_all() içinde (oturum sonu / kill switch)
    3. IsolatedKillSwitch._emergency_shutdown() içinde (acil çıkış)
    """
    pattern = os.path.join(TEMP_DIR, "tts_*.mp3")
    orphans = glob.glob(pattern)
    for f in orphans:
        try:
            os.remove(f)
        except OSError:
            pass  # Dosya kullanımda olabilir, geç
    
    if orphans:
        logger.info(f"Cleaned {len(orphans)} orphan TTS files")
```

**IsolatedKillSwitch güncellemesi:**

```python
def _emergency_shutdown(self):
    # 1. Restore sistem değişiklikleri
    try:
        self._restore_callback()
    except Exception:
        pass
    
    # 2. TTS temp dosyalarını temizle (sync, hızlı)
    import glob, os
    for f in glob.glob("temp/tts_*.mp3"):
        try:
            os.remove(f)
        except OSError:
            pass
    
    # 3. Electron process'i öldür
    # ... (mevcut kod)
```

### Crash Recovery

Uygulama beklenmedik şekilde kapanırsa (process kill, BSOD, güç kesintisi):

1. Sonraki açılışta `sessions` tablosunda `status = "active"` olan kayıt aranır
2. Bulunursa → crash recovery modu:
   - Orijinal durumlar restore edilir
   - Session `crashed` olarak işaretlenir
   - Log kaydı tutulur

```python
async def check_crash_recovery():
    active_sessions = await db.query(
        "SELECT * FROM sessions WHERE status = 'active'"
    )
    
    if active_sessions:
        logger.warning("Crash recovery: Previous session found")
        for session in active_sessions:
            await restore_session_state(session)
            await db.update(session.id, status="crashed")
```

---

## 7. Onboarding Güvenlik Onayı

### Consent Screen İçeriği

Oyuncu uygulamayı ilk açtığında gösterilecek onay ekranı:

```
╔══════════════════════════════════════════════════════════════╗
║                    ⚠️ GÜVENLİK BİLGİSİ                      ║
║                                                              ║
║  SENTIENT_OS bir psikolojik korku deneyimidir.               ║
║                                                              ║
║  Bu uygulama:                                                ║
║  ✅ Masaüstü dosya/klasör İSİMLERİNİZİ okur (içerik değil)  ║
║  ✅ Ekranda görsel efektler gösterir                         ║
║  ✅ Ses efektleri ve konuşma çalar                           ║
║  ✅ Masaüstü arka planını geçici olarak değiştirebilir       ║
║  ✅ Fare imlecini geçici olarak etkileyebilir                ║
║                                                              ║
║  Bu uygulama ASLA:                                           ║
║  ❌ Dosyalarınızı silmez veya değiştirmez                    ║
║  ❌ Kişisel verilerinizi internete göndermez                  ║
║  ❌ Kameranıza veya mikrofonunuza erişmez                    ║
║  ❌ Sisteminize kalıcı zarar vermez                          ║
║                                                              ║
║  Acil Çıkış: Ctrl + Shift + Q (her zaman çalışır)           ║
║                                                              ║
║  ⚠️ EPİLEPSİ UYARISI: Yanıp sönen ışıklar ve hızlı         ║
║  renk değişimleri içerir.                                    ║
║                                                              ║
║  [ ] Bu bilgileri okudum ve kabul ediyorum.                   ║
║                                                              ║
║              [DEVAM ET]           [ÇIKIŞ]                    ║
╚══════════════════════════════════════════════════════════════╝
```

### Onay Gereksinimleri

1. Checkbox işaretlenmeden "DEVAM ET" butonu aktif olmaz.
2. Onay durumu SQLite'a kaydedilir — her açılışta tekrar sorulmaz.
3. Onay sırasında kill switch zaten aktiftir.
4. "ÇIKIŞ" butonu uygulamayı tamamen kapatır.

---

## 8. Streamer Koruması

### Algılama

```python
STREAMER_APPS = [
    "obs64.exe", "obs32.exe",    # OBS Studio
    "streamlabs.exe",             # Streamlabs
    "xsplit.exe",                  # XSplit
    "discord.exe",                 # Discord (ekran paylaşımı)
]

async def check_streamer_mode():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() in STREAMER_APPS:
            return True
    return False
```

### Streamer Mode Etkileri

Streamer mode aktifken:
- Dosya isimleri AI context'ten **tamamen çıkarılır**
- Kullanıcı profili AI'ya gönderilmez
- AI sadece genel bağlamla çalışır
- Log dosyalarında kişisel bilgi yazılmaz

---

## 9. Güvenlik Kontrol Listesi (Her Faz Sonu)

Her geliştirme fazının sonunda kontrol edilecek maddeler:

- [ ] Kill switch çalışıyor mu? (Ctrl+Shift+Q)
- [ ] Resource guard aktif mi? (CPU/RAM limitleri)
- [ ] Privacy filter doğru çalışıyor mu? (Blacklist test)
- [ ] Tüm efektler geri alınabiliyor mu? (Restore test)
- [ ] Panic detection çalışıyor mu? (ESC spam, Alt+F4 spam)
- [ ] Crash recovery çalışıyor mu? (Process kill testi)
- [ ] Streamer mode algılanıyor mu? (OBS açıkken test)
- [ ] Gerçek dosya sistemi değiştirilmiyor mu? (readonly test)
- [ ] AI context'te tam yol yok mu? (Log inceleme)
- [ ] Temp dosyalar temizleniyor mu? (Oturum sonu kontrol)
