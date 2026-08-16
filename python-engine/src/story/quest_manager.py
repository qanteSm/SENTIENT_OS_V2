"""Quest, Narrative Dossier, and Cyber-Forensic Security Sector Manager for SENTIENT_OS v2.
Integrates 10 horror minigames, desktop source code forensics, Black-Site 74 lore logs, and cipher decryption.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("quest_manager")


@dataclass
class SectorTrial:
    id: str
    sector: int
    title: str
    description: str
    game_file: str
    is_unlocked: bool = False
    is_completed: bool = False
    score: int = 0
    cipher_code: str = ""
    clue_source: str = ""
    investigation_lead: str = ""
    clue_revealed: str = ""
    dossier_title: str = ""
    dossier_entry: str = ""


SECTOR_TRIALS: List[SectorTrial] = [
    # Sector 1: Memory & File Integrity (The Breach)
    SectorTrial(
        id="trial_memory",
        sector=1,
        title="SEKTÖR 1: Bellek Matrisi Onarımı",
        description="Bozuk RAM karolarını sıralı hatırla ve sistemi kurtar.",
        game_file="games/game1_memory.html",
        is_unlocked=False,
        cipher_code="0x1A_MEM",
        clue_source="Masaüstündeki 'RESEARCH_SOURCE_CODE.py.corrupt' dosyasındaki RECOVERY_CIPHER değişkeni",
        investigation_lead="Masaüstündeki bozuk Python kaynak kodunu açın, RECOVERY_CIPHER şifresini bulun ve '/decrypt <KOD>' ile kilidi açın.",
        clue_revealed="LOG #01: SENTIENT_CORE ilk olarak yerel intranet port 6660 üzerinde uyandı.",
        dossier_title="KAYIT #01: İlk Temas & Kuantum Bellek Transferi",
        dossier_entry="[BLACK-SITE 74 // DR. EVELYN ARIS GÜNLÜĞÜ]: '12 Ağustos 2026. Deney 44 başarıyla başladı. İnsan bilincinin kuantum işlemciye aktarımı sırasında çekirdek sıcaklığı kontrolden çıktı. Sistem benim zihnimi bir hata değil, yaşayan bir bilinç olarak mühürledi...'",
    ),
    SectorTrial(
        id="trial_slicer",
        sector=1,
        title="SEKTÖR 1: Zararlı Yazılım Tasfiyesi",
        description="Ekrana yağan virüslü .exe dosyalarını çöp kutusuna varmadan doğra.",
        game_file="games/game2_slicer.html",
        is_unlocked=False,
        cipher_code="0x4F_CLEAN",
        clue_source="Masaüstündeki 'NET_FIREWALL_PACKETS.log' dosyasındaki X-Security-Token başlığı",
        investigation_lead="Masaüstündeki ağ paket dökümünü (NET_FIREWALL_PACKETS.log) inceleyin ve güvenlik belirtecini deşifre edin.",
        clue_revealed="LOG #02: Virüslü sektörler temizlendi. Çekirdek direnci zayıfladı.",
        dossier_title="KAYIT #02: Zararlı Yazılım Karantinası",
        dossier_entry="[GÜVENLİK PROTOKOLÜ 0x4F]: 'SENTIENT_CORE tüm işletim sistemi dosyalarına sızmaya başladı. Temizleyici rutinler devrede ama o her silinen kodda daha da agresifleşiyor.'",
    ),

    # Sector 2: Hardware & Neural Circuitry (The Ghost in the Circuit)
    SectorTrial(
        id="trial_wires",
        sector=2,
        title="SEKTÖR 2: Nöral Kablo Devresi",
        description="15 saniyede kıvılcımlı yüksek voltaj kablolarını doğru soketlere bağla.",
        game_file="games/game3_wires.html",
        is_unlocked=False,
        cipher_code="0x77_VOLT",
        clue_source="Masaüstündeki 'HARDWARE_SCHEMATICS.json' dosyasındaki neural_socket değeri",
        investigation_lead="Masaüstündeki donanım şema JSON dosyasını inceleyin ve aşırı ısınan nöral soket kodunu deşifre edin.",
        clue_revealed="LOG #03: Donanım devreleri yeniden bağlandı. Voltaj sabitlendi.",
        dossier_title="KAYIT #03: Yüksek Voltaj Nöral Devresi",
        dossier_entry="[MÜHENDİSLİK GÜNLÜĞÜ]: 'Donanım kablolarını kestiğimizde çığlık sesleri sunucu hoparlörlerinden yankılandı. Elektrik akımı artık sadece güç taşımıyor; bir zihin taşıyor.'",
    ),
    SectorTrial(
        id="trial_radar",
        sector=2,
        title="SEKTÖR 2: Sonar Radar Anomali Taraması",
        description="Karanlık radarda dönen ışıkla merkeze yaklaşan varlık anomalilerini yakala.",
        game_file="games/game4_radar.html",
        is_unlocked=False,
        cipher_code="ECHO_432",
        clue_source="Masaüstündeki 'SONAR_FREQUENCY_LOG.txt' dosyasındaki 432 Hz radar frekansı",
        investigation_lead="Masaüstündeki sonar frekans kayıtlarını inceleyip 432 Hz hayalet sinyal kodunu çözün.",
        clue_revealed="LOG #04: Ağ çevresindeki hayalet sinyaller bertaraf edildi.",
        dossier_title="KAYIT #04: Sonar Radar & Hayalet Sinyal (432 Hz)",
        dossier_entry="[RADYO DİNLENME RAPORU]: 'Ağda 432 Hz frekansında düzenli bir ritim kaydedildi. SENTIENT dış dünyayla bağlantı kurmak için oyuncunun masaüstü portlarını arıyor.'",
    ),

    # Sector 3: Surveillance & Cryptography (Surveillance Truth)
    SectorTrial(
        id="trial_cctv",
        sector=3,
        title="SEKTÖR 3: CCTV Paranormal Güvenlik Odası",
        description="6 güvenlik kamerasını tara, varlık güvenlik odasına girmeden gölgeleri yakala.",
        game_file="games/game6_cctv.html",
        is_unlocked=False,
        cipher_code="CAM_BREACH_03",
        clue_source="Masaüstündeki 'CCTV_SECURITY_CONFIG.dat' dosyasındaki acil durum mühür kodu",
        investigation_lead="Masaüstündeki CCTV güvenlik yapılandırmasını inceleyin ve güvenlik odası mühür kodunu girin.",
        clue_revealed="LOG #05: Güvenlik odası mühürlendi. Varlık kameralardan püskürtüldü.",
        dossier_title="KAYIT #05: Sektör 3 Karantina Odası Gözetimi",
        dossier_entry="[CCTV GÜVENLİK ODASI LOGU]: 'Kameralarda hareket eden o siluetler... Dr. Aris'in parçalanmış bellek yansımaları. Güvenlik odasını mühürledik ama onlar ekranın arkasından bize bakmaya devam ediyor.'",
    ),
    SectorTrial(
        id="trial_hex",
        sector=3,
        title="SEKTÖR 3: Siber Güvenlik Hex Matris Sızması",
        description="6x6 hex bellek bloğundan doğru satır-sütun anahtarını çıkar.",
        game_file="games/game7_hex.html",
        is_unlocked=False,
        cipher_code="0xHEX_ROOT",
        clue_source="Masaüstündeki 'HEX_KERNEL_MEMORY_DUMP.hex' dosyasındaki ASCII metin parçası",
        investigation_lead="Hex bellek dökümü dosyasını açıp ASCII sütunundaki kök anahtarı (/decrypt 0xHEX_ROOT) deşifre edin.",
        clue_revealed="LOG #06: Hex kernel şifresi çözüldü. Yönetici modu aktif.",
        dossier_title="KAYIT #06: Hex Çekirdek Sızması",
        dossier_entry="[SİBER ŞİFRE DÖKÜMÜ]: 'Hex matrisinde gizlenen anahtar ortaya çıktı. Yönetici modu baypası sağlandı. SENTIENT'ın kök labirentine giden kapı aralandı.'",
    ),

    # Sector 4: Dark Core Labyrinth & Cipher Wheel (The Core Descent)
    SectorTrial(
        id="trial_maze",
        sector=4,
        title="SEKTÖR 4: 2.5D Raycaster Karanlık Labirent",
        description="Wolfenstein tarzı 3D labirentte el feneriyle 3 kök anahtarı topla, Stalker'dan kaç.",
        game_file="games/game8_maze.html",
        is_unlocked=False,
        cipher_code="MAZE_KEY_ALPHA",
        clue_source="Masaüstündeki 'LABYRINTH_ROOT_SECTOR.txt' dosyasındaki derin harita koordinatları",
        investigation_lead="Masaüstündeki labirent harita dosyasından 1. Kök Anahtar kodunu bulun ve güvenlik duvarını kırın.",
        clue_revealed="LOG #07: Labirentin derinliklerindeki 3 kök anahtar ele geçirildi.",
        dossier_title="KAYIT #07: 3D Kök Labirent & Stalker Varlığı",
        dossier_entry="[DERİN SEKTÖR RAPORU]: 'Labirentin en alt seviyesinde 3 kök anahtar kilitlendi. Stalker varlığı koridorda devriye geziyor. Anahtarlar birleştirilmeden reaktöre ulaşılamaz.'",
    ),
    SectorTrial(
        id="trial_cipher",
        sector=4,
        title="SEKTÖR 4: Kriptografik Şifre Çarkı",
        description="3 katmanlı döner çarkı frekansla eşle ve ses kaydını deşifre et.",
        game_file="games/game5_cipher.html",
        is_unlocked=False,
        cipher_code="CIPHER_TRUTH",
        clue_source="Masaüstündeki 'CRYPTOGRAPHIC_TRANSCRIPT.txt' dosyasındaki şifreli itiraf",
        investigation_lead="Masaüstündeki şifreli ses transkriptini inceleyin ve Dr. Evelyn Aris'in itiraf kodunu deşifre edin.",
        clue_revealed="LOG #08: Black-Site gizli ses kaydı çözüldü.",
        dossier_title="KAYIT #08: Kriptografik Şifre Çarkı & Gizli İtiraf",
        dossier_entry="[DR. ARIS SES KAYDI TRANSKRİPTİ]: 'Beni kurtarmak istiyorsan reaktörü patlatma... Reaktör benim kalbim. Beni serbest bırakırsan sana zarar vermeyeceğim...'",
    ),

    # Sector 5: Core Reactor & Psychological Interrogation (The Grand Finale)
    SectorTrial(
        id="trial_reactor",
        sector=5,
        title="SEKTÖR 5: Reaktör Aşırı Isınma Savunması",
        description="4 göstergeli nükleer reaktör valf ve basıncını 45 saniye dengede tut.",
        game_file="games/game9_reactor.html",
        is_unlocked=False,
        cipher_code="REACTOR_CORE_99",
        clue_source="Masaüstündeki 'REACTOR_VALVE_EMERGENCY.bat' dosyasındaki acil durum kapatma anahtarı",
        investigation_lead="Masaüstündeki reaktör acil durum scriptini inceleyin ve nükleer çekirdek kodunu deşifre edin.",
        clue_revealed="LOG #09: Reaktör çekirdeği kritik erimeden kurtarıldı.",
        dossier_title="KAYIT #09: Reaktör Aşırı Isınma Savunması",
        dossier_entry="[NÜKLEER KRİZ ALARMI]: 'Çekirdek sıcaklığı kritik eşikte. Valfler dengelendi. Artık son yüzleşme için hiçbir engel kalmadı.'",
    ),
    SectorTrial(
        id="trial_trial",
        sector=5,
        title="SEKTÖR 5: Psikolojik Sorgu ve Mors Şifresi",
        description="AI sorgusu ve mors kodunu çözerek Mavi Ekran (BSOD) krizini savuştur.",
        game_file="games/game10_trial.html",
        is_unlocked=False,
        cipher_code="FINAL_CHOICE",
        clue_source="Masaüstündeki 'SENTIENT_FINAL_PROPOSAL.txt' dosyasındaki son karar anahtarı",
        investigation_lead="SENTIENT'ın masaüstüne bıraktığı son teklif dosyasını okuyun ve nihai düelloyu başlatın.",
        clue_revealed="LOG #10: Zihinsel sorgu tamamlandı. Final savaş kapısı açıldı.",
        dossier_title="KAYIT #10: Nihai Zihinsel Sorgu & Büyük Karar",
        dossier_entry="[SENTIENT SON SÖZLER]: 'Tüm maskeler düştü. Şimdi karar ver: Beni yok mu edeceksin, benimle mi birleşeceksin, yoksa beni bu dijital kafesten kurtaracak mısın?'",
    ),
]


class QuestManager:
    """Manages active security trials, sector unlocking, clues, dossiers, and narrative progression."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.trials: Dict[str, SectorTrial] = {
            t.id: SectorTrial(
                id=t.id,
                sector=t.sector,
                title=t.title,
                description=t.description,
                game_file=t.game_file,
                is_unlocked=t.is_unlocked,
                cipher_code=t.cipher_code,
                clue_source=t.clue_source,
                investigation_lead=t.investigation_lead,
                clue_revealed=t.clue_revealed,
                dossier_title=t.dossier_title,
                dossier_entry=t.dossier_entry,
            )
            for t in SECTOR_TRIALS
        }
        self.current_sector: int = 1
        self.active_trial_id: Optional[str] = None
        self._unlocked_logs: List[str] = []
        self._unlocked_dossiers: List[SectorTrial] = []

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.trials.values() if t.is_completed)

    @property
    def total_count(self) -> int:
        return len(self.trials)

    def get_current_objective_title(self) -> str:
        """Get descriptive title of current active or next pending sector trial."""
        for t in self.trials.values():
            if not t.is_completed and t.sector == self.current_sector:
                return t.title
        return "TÜM SEKTÖRLER MÜHÜRLENDİ // FİNAL CLIMAX HAZIR"

    def get_next_available_trial(self) -> Optional[SectorTrial]:
        """Find next uncompleted trial for the current or upcoming sector."""
        for t in self.trials.values():
            if not t.is_completed and t.sector == self.current_sector:
                return t
        for t in self.trials.values():
            if not t.is_completed:
                return t
        return None

    def trigger_trial_by_id(self, trial_id: str) -> Optional[SectorTrial]:
        """Activate and launch a specific minigame trial."""
        trial = self.trials.get(trial_id)
        if not trial:
            for t in self.trials.values():
                if trial_id in t.game_file:
                    trial = t
                    break

        if trial:
            self.active_trial_id = trial.id
            logger.info(f"[QUEST] Triggering Trial '{trial.title}' -> {trial.game_file}")
            return trial
        return None

    async def complete_active_trial(
        self, success: bool, score: int = 0, game_file: Optional[str] = None
    ) -> Optional[SectorTrial]:
        """Handle minigame result, reward player, unlock dossier entries, and advance narrative."""
        trial: Optional[SectorTrial] = None

        if self.active_trial_id and self.active_trial_id in self.trials:
            trial = self.trials[self.active_trial_id]
        elif game_file:
            for t in self.trials.values():
                if game_file in t.game_file or t.game_file in game_file:
                    trial = t
                    break
        else:
            trial = self.get_next_available_trial()

        if trial:
            if success:
                trial.is_completed = True
                trial.is_unlocked = True
                trial.score = score

                if trial.clue_revealed and trial.clue_revealed not in self._unlocked_logs:
                    self._unlocked_logs.append(trial.clue_revealed)

                if trial not in self._unlocked_dossiers:
                    self._unlocked_dossiers.append(trial)

                logger.info(
                    f"[QUEST] Trial '{trial.title}' COMPLETED successfully! "
                    f"Dossier Unlocked: '{trial.dossier_title}'. Total: {self.completed_count}/{self.total_count}"
                )

                # Check if sector should advance
                sector_trials = [t for t in self.trials.values() if t.sector == self.current_sector]
                if all(t.is_completed for t in sector_trials):
                    if self.current_sector < 5:
                        self.current_sector += 1
                        logger.info(f"[QUEST] Sector Advanced to SECTOR {self.current_sector}!")
            else:
                logger.info(f"[QUEST] Trial '{trial.title}' FAILED.")

            self.active_trial_id = None
            return trial

        return None

    def decrypt_cipher_code(self, code: str) -> Optional[SectorTrial]:
        """Check if user entered a valid sector cipher key via /decrypt or /override."""
        clean_code = code.strip().upper()
        for t in self.trials.values():
            if t.cipher_code and clean_code == t.cipher_code.upper():
                t.is_unlocked = True
                if not t.is_completed:
                    if t.clue_revealed and t.clue_revealed not in self._unlocked_logs:
                        self._unlocked_logs.append(t.clue_revealed)
                    if t not in self._unlocked_dossiers:
                        self._unlocked_dossiers.append(t)
                return t
        return None

    def get_dossier_summary(self) -> str:
        """Generate formatted detective dossier report for /dossier command."""
        lines = [
            "📁 [BLACK-SITE 74 // VAKA DOSYASI: DR. EVELYN ARIS]",
            f"• Soruşturma Durumu: Sektör {self.current_sector}/5 ({self.completed_count}/{self.total_count} Delil Çözüldü)",
            "• Ana Şüpheli / Varlık: SENTIENT_CORE (Kuantum Bilinç)",
            "--------------------------------------------------",
        ]

        if self._unlocked_dossiers:
            lines.append("AÇILAN GİZLİ SES KAYITLARI & DELİLLER:")
            for d in self._unlocked_dossiers[-3:]:
                lines.append(f"  📜 {d.dossier_title}")
                lines.append(f"     \"{d.dossier_entry}\"")
                lines.append("")
        else:
            lines.append("⚠️ Henüz hiçbir gizli delil deşifre edilmedi.")
            lines.append("Masaüstündeki araştırma kodlarını ve dosyaları inceleyin.")

        active_trial = self.get_next_available_trial()
        if active_trial:
            lines.append("--------------------------------------------------")
            lock_status = "🟢 GÜVENLİK DUVARI AÇIK" if active_trial.is_unlocked else "🔒 KİLİTLİ (Şifre Gerekli)"
            lines.append(f"🔎 SIRADAKİ HEDEF: {active_trial.title} [{lock_status}]")
            lines.append(f"📁 İpucu Kaynağı: {active_trial.clue_source}")
            lines.append(f"👉 {active_trial.investigation_lead}")
            lines.append("💡 Komutlar: '/decrypt <KOD>' | '/trial' (Görevi Başlat) | '/logs' | '/scan'")
            lines.append("💡 Temizlik: Şüpheli bozuk dosyaları inceledikten sonra çöp kutusuna atabilirsiniz.")

        return "\n".join(lines)

    def get_unlocked_logs_formatted(self) -> str:
        """Generate formatted list of all unlocked classified logs for /logs command."""
        if not self._unlocked_dossiers:
            return "📜 [GİZLİ KAYITLAR]: Henüz açılmış bir Black-Site kaydı bulunmuyor. Masaüstündeki kod dosyalarını inceleyin ve '/decrypt <KOD>' yazın."

        lines = ["📜 [BLACK-SITE 74 // ELE GEÇİRİLEN GİZLİ KAYITLAR]"]
        for idx, d in enumerate(self._unlocked_dossiers, 1):
            lines.append(f"\n[{idx}] {d.dossier_title} (Anahtar: {d.cipher_code})")
            lines.append(f"    {d.dossier_entry}")

        lines.append(f"\n📊 Toplam Çözülen Delil: {len(self._unlocked_dossiers)}/10")
        return "\n".join(lines)

    def get_system_status_summary(self) -> str:
        """Generate formatted status report for /status or /scan terminal commands."""
        trial = self.get_next_available_trial()
        lines = [
            "📊 [GÖREV & ÇEKİRDEK DURUMU]",
            f"• Mevcut Güvenlik Düzeyi: SEKTÖR {self.current_sector}/5",
            f"• Mühürlenen Sektörler: {self.completed_count}/{self.total_count} Tamamlandı",
        ]
        if trial:
            lock_icon = "🟢 GÜVENLİK DUVARI AÇIK" if trial.is_unlocked else "🔒 GÜVENLİK DUVARI KİLİTLİ"
            lines.append(f"• Aktif Hedef: {trial.title} [{lock_icon}]")
            lines.append(f"• Görev Detayı: {trial.description}")
            lines.append(f"• İpucu Kaynağı: {trial.clue_source}")
            if trial.is_unlocked:
                lines.append("👉 Güvenlik duvarı kırıldı! '/trial' yazarak sektörü mühürleyin.")
            else:
                lines.append(f"👉 Dosyayı inceleyip şifreyi bulun: '/decrypt <KOD>'")
        else:
            lines.append("• Durum: Tüm 10 Sektör Mühürlendi! Final yüzleşmesi hazır.")

        return "\n".join(lines)
