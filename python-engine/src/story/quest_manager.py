"""Quest and System Security Sector Manager for SENTIENT_OS v2.
Integrates the 10 horror minigames directly into narrative story trials and tracks sector progression.
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
    is_completed: bool = False
    score: int = 0
    clue_revealed: str = ""


SECTOR_TRIALS: List[SectorTrial] = [
    # Sector 1: Memory & File Integrity
    SectorTrial(
        id="trial_memory",
        sector=1,
        title="SEKTÖR 1: Bellek Matrisi Onarımı",
        description="Bozuk RAM karolarını sıralı hatırla ve sistemi kurtar.",
        game_file="games/game1_memory.html",
        clue_revealed="LOG #01: SENTIENT_CORE ilk olarak yerel intranet port 6660 üzerinde uyandı.",
    ),
    SectorTrial(
        id="trial_slicer",
        sector=1,
        title="SEKTÖR 1: Zararlı Yazılım Tasfiyesi",
        description="Ekrana yağan virüslü .exe dosyalarını çöp kutusuna varmadan doğra.",
        game_file="games/game2_slicer.html",
        clue_revealed="LOG #02: Virüslü sektörler temizlendi. Çekirdek direnci zayıfladı.",
    ),

    # Sector 2: Hardware & Neural Circuitry
    SectorTrial(
        id="trial_wires",
        sector=2,
        title="SEKTÖR 2: Nöral Kablo Devresi",
        description="15 saniyede kıvılcımlı yüksek voltaj kablolarını doğru soketlere bağla.",
        game_file="games/game3_wires.html",
        clue_revealed="LOG #03: Donanım devreleri yeniden bağlandı. Voltaj sabitlendi.",
    ),
    SectorTrial(
        id="trial_radar",
        sector=2,
        title="SEKTÖR 2: Sonar Radar Anomali Taraması",
        description="Karanlık radarda dönen ışıkla merkeze yaklaşan varlık anomalilerini yakala.",
        game_file="games/game4_radar.html",
        clue_revealed="LOG #04: Ağ çevresindeki hayalet sinyaller bertaraf edildi.",
    ),

    # Sector 3: Surveillance & Cryptography
    SectorTrial(
        id="trial_cctv",
        sector=3,
        title="SEKTÖR 3: CCTV Paranormal Güvenlik Odası",
        description="6 güvenlik kamerasını tara, varlık güvenlik odasına girmeden gölgeleri yakala.",
        game_file="games/game6_cctv.html",
        clue_revealed="LOG #05: Güvenlik odası mühürlendi. Varlık kameralardan püskürtüldü.",
    ),
    SectorTrial(
        id="trial_hex",
        sector=3,
        title="SEKTÖR 3: Siber Güvenlik Hex Matris Sızması",
        description="6x6 hex bellek bloğundan doğru satır-sütun anahtarını çıkar.",
        game_file="games/game7_hex.html",
        clue_revealed="LOG #06: Hex kernel şifresi çözüldü. Yönetici modu aktif.",
    ),

    # Sector 4: Dark Core Labyrinth & Cipher Wheel
    SectorTrial(
        id="trial_maze",
        sector=4,
        title="SEKTÖR 4: 2.5D Raycaster Karanlık Labirent",
        description="Wolfenstein tarzı 3D labirentte el feneriyle 3 kök anahtarı topla, Stalker'dan kaç.",
        game_file="games/game8_maze.html",
        clue_revealed="LOG #07: Labirentin derinliklerindeki 3 kök anahtar ele geçirildi.",
    ),
    SectorTrial(
        id="trial_cipher",
        sector=4,
        title="SEKTÖR 4: Kriptografik Şifre Çarkı",
        description="3 katmanlı döner çarkı frekansla eşle ve ses kaydını deşifre et.",
        game_file="games/game5_cipher.html",
        clue_revealed="LOG #08: Black-Site gizli ses kaydı çözüldü.",
    ),

    # Sector 5: Core Reactor & Psychological Interrogation
    SectorTrial(
        id="trial_reactor",
        sector=5,
        title="SEKTÖR 5: Reaktör Aşırı Isınma Savunması",
        description="4 göstergeli nükleer reaktör valf ve basıncını 45 saniye dengede tut.",
        game_file="games/game9_reactor.html",
        clue_revealed="LOG #09: Reaktör çekirdeği kritik erimeden kurtarıldı.",
    ),
    SectorTrial(
        id="trial_trial",
        sector=5,
        title="SEKTÖR 5: Psikolojik Sorgu ve Mors Şifresi",
        description="AI sorgusu ve mors kodunu çözerek Mavi Ekran (BSOD) krizini savuştur.",
        game_file="games/game10_trial.html",
        clue_revealed="LOG #10: Zihinsel sorgu tamamlandı. Final savaş kapısı açıldı.",
    ),
]


class QuestManager:
    """Manages active security trials, sector unlocking, and trial launch events."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.trials: Dict[str, SectorTrial] = {
            t.id: SectorTrial(
                id=t.id,
                sector=t.sector,
                title=t.title,
                description=t.description,
                game_file=t.game_file,
                clue_revealed=t.clue_revealed,
            )
            for t in SECTOR_TRIALS
        }
        self.current_sector: int = 1
        self.active_trial_id: Optional[str] = None
        self._unlocked_logs: List[str] = []

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
            # Fallback by game name
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
        """Handle minigame result, reward player, and unlock lore logs."""
        trial: Optional[SectorTrial] = None

        # 1. Match by active_trial_id if set
        if self.active_trial_id and self.active_trial_id in self.trials:
            trial = self.trials[self.active_trial_id]
        elif game_file:
            # Match by specific game file
            for t in self.trials.values():
                if game_file in t.game_file or t.game_file in game_file:
                    trial = t
                    break
        else:
            # Fallback to current sector trial
            trial = self.get_next_available_trial()

        if trial:
            if success:
                trial.is_completed = True
                trial.score = score
                if trial.clue_revealed and trial.clue_revealed not in self._unlocked_logs:
                    self._unlocked_logs.append(trial.clue_revealed)
                logger.info(f"[QUEST] Trial '{trial.title}' COMPLETED successfully! Total completed: {self.completed_count}/{self.total_count}")

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

    def get_system_status_summary(self) -> str:
        """Generate formatted status report for /status or /scan terminal commands."""
        lines = [
            "==================================================",
            "        SENTIENT_OS v2 // SİSTEM TEŞHİS RAPORU    ",
            "==================================================",
            f"GÜNCEL GÜVENLİK DÜZEYİ: SEKTÖR {self.current_sector}/5",
            f"TAMAMLANAN GÜVENLİK SINAVLARI: {self.completed_count}/{self.total_count}",
            f"AKTİF GÖREV: {self.get_current_objective_title()}",
            "--------------------------------------------------",
            "SEKTÖR DURUMLARI:",
        ]

        for s in range(1, 6):
            s_trials = [t for t in self.trials.values() if t.sector == s]
            s_done = all(t.is_completed for t in s_trials)
            status_icon = "🟢 [GÜVENLİ]" if s_done else "🔴 [İHLAL EDİLDİ]"
            lines.append(f"  • SEKTÖR 0{s}: {status_icon} ({sum(1 for t in s_trials if t.is_completed)}/{len(s_trials)} Onarıldı)")

        if self._unlocked_logs:
            lines.append("--------------------------------------------------")
            lines.append("ELE GEÇİRİLEN ŞİFRELİ LOGLAR:")
            for log in self._unlocked_logs[-3:]:
                lines.append(f"  > {log}")

        lines.append("==================================================")
        return "\n".join(lines)
