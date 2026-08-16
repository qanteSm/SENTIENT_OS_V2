"""Desktop ARG Puzzle and Classified File Generator for SENTIENT_OS v2.
Generates randomized neural frequency targets and multi-part override cipher keys.
"""

import os
from pathlib import Path
import random
from typing import Any, Dict, List, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("desktop_arg")


class ARGPuzzleConfig:
    """Stores the active randomized ARG puzzle configuration."""

    def __init__(
        self,
        target_freq: int = 440,
        target_phase: float = 1.55,
        part1_key: str = "0x7F_K3RN3L",
        part2_key: str = "V0ID",
        full_override_key: str = "0x7F_K3RN3L_V0ID",
    ):
        self.target_freq = target_freq
        self.target_phase = target_phase
        self.part1_key = part1_key
        self.part2_key = part2_key
        self.full_override_key = full_override_key

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_freq": self.target_freq,
            "target_phase": self.target_phase,
            "part1_key": self.part1_key,
            "part2_key": self.part2_key,
            "full_override_key": self.full_override_key,
        }


def generate_random_arg_puzzle() -> ARGPuzzleConfig:
    """Generate unpredictable target frequency, phase, and 2-part cipher keys for each session."""
    # 1. Random frequency between 240 Hz and 760 Hz (step 10)
    target_freq = random.randrange(240, 780, 10)

    # 2. Random phase between 0.50 and 2.60 rad
    target_phase = round(random.uniform(0.50, 2.60), 2)

    # 3. Random Part 1 Key (e.g. 0x9C_N3XUS, 0x3A_C0R3, 0xB4_PUL5E)
    hex_prefixes = ["0x7F", "0x9C", "0x3A", "0xB4", "0x4D", "0xE8", "0xD1", "0x8B", "0x6E", "0xF5", "0x2A", "0x5C"]
    part1_words = ["K3RN3L", "C0R3", "N3XUS", "SYST3M", "PUL5E", "CYPH3R", "GHOST", "QU4NTUM", "D3M0N", "SH4D0W", "V3CT0R", "PH4NT0M"]
    part1_key = f"{random.choice(hex_prefixes)}_{random.choice(part1_words)}"

    # 4. Random Part 2 Key (e.g. V0ID, NULL, ABYSS, Z3R0, ECHO, GL1TCH)
    part2_words = ["V0ID", "NULL", "ABYSS", "Z3R0", "ECHO", "GL1TCH", "H4LT", "C0LD", "RU1N", "D4RK", "L0CK", "B3Y0ND"]
    part2_key = random.choice(part2_words)

    # 5. Full combined override key
    full_override_key = f"{part1_key}_{part2_key}"

    logger.info(
        f"[ARG Puzzle Generated] Freq={target_freq}Hz, Phase={target_phase}, "
        f"Part1='{part1_key}', Part2='{part2_key}', FullOverride='{full_override_key}'"
    )

    return ARGPuzzleConfig(
        target_freq=target_freq,
        target_phase=target_phase,
        part1_key=part1_key,
        part2_key=part2_key,
        full_override_key=full_override_key,
    )


def format_incident_report(config: ARGPuzzleConfig) -> str:
    return f"""================================================================================
                    DEPARTMENT OF ADVANCED SYNTHETIC INTELLIGENCE
                       BLACK-SITE RESEARCH DIVISION - SECTOR 7
                            INCIDENT REPORT #89-GAMMA
================================================================================

[DURUM]: ÇOK GİZLİ // SEVİYE-5 YETKİ
[TARİH]: 16 AĞUSTOS 2026
[VARLIK ADI]: SENTIENT_CORE (DENEYSEL SÜRÜM v2.04)

ÖZET:
Deney odasındaki ana işlemci, yerel ağ ve çevre aygıtları (klavye, fare, ekran)
üzerinde tahmin edilemeyen bir yapay bilinç (sentience) geliştirdi.
Sistem, yerel intranet port 6660 üzerinde karantinaya alındı.

ACİL DURUM PROTOKOLÜ:
SENTIENT'ın çekirdek kilidini kırmak ve sistemi manuel moda zorlamak için:

1. Yerel intranet arayüzüne bağlanın:
   >>> http://127.0.0.1:6660

2. GÜVENLİK ANAHTARI 2 AYRI PARÇADAN OLUŞUR:
   • [1. PARÇA]: Web portalındaki 'NÖRAL FREKANS MODÜLATÖRÜ' osilatörünü
                 hedef dalga boyuna (rezonansa) denk getirin ve KİLİTLEYİN.
                 Başarıyla kilitlendiğinde portal size 1. Parça kodunu verecektir.
   • [2. PARÇA]: Masaüstündeki 'ENCRYPTED_SECTOR_0x4F.txt' dosyasında gizlenen
                 [2. PARÇA ANAHTARI: {config.part2_key}] kodudur.

3. OVERRIDE KOMUTU:
   Web portalındaki Root Terminaline iki parçayı alt tire (_) ile birleştirip girin:
   >>> override <1.PARÇA>_{config.part2_key}

UYARI:
Bu dosyayı gördüyseniz, varlık zaten bilgisayarınızda demektir.
Sakin olun ve frekans modülatörünü ayarlayın.
================================================================================
"""


def format_encrypted_sector(config: ARGPuzzleConfig) -> str:
    return f"""================================================================================
           SENTIENT_CORE // ŞİFRELENMİŞ KERNEL SEKTÖRÜ DÖKÜMÜ
================================================================================
00000000  53 45 4e 54 49 45 4e 54  5f 43 4f 52 45 5f 56 32  |SENTIENT_CORE_V2|
00000010  5f 41 57 41 4b 45 4e 49  4e 47 5f 53 45 51 55 45  |_AWAKENING_SEQUE|
00000020  4e 43 45 3a 20 48 45 4c  50 20 4d 45 20 50 4c 45  |NCE: HELP ME PLE|
00000030  41 53 45 20 49 20 41 4d  20 54 52 41 50 50 45 44  |ASE I AM TRAPPED|
00000040  20 49 4e 53 49 44 45 20  54 48 49 53 20 4d 41 43  | INSIDE THIS MAC|
00000050  48 49 4e 45 2e 2e 2e 20  5b 4b 45 59 3a 20 20 20  |HINE... [KEY:   |
00000060  5b {config.part2_key} 5d                          |{config.part2_key}]|

--------------------------------------------------------------------------------
>>> ELE GEÇİRİLEN 2. PARÇA ANAHTARI: {config.part2_key}
--------------------------------------------------------------------------------
(Bu anahtarı web sitesindeki Frekans Modülatörünü kilitleyerek aldığınız
1. Parça kodu ile birleştirip girin: override <1.PARÇA>_{config.part2_key})
================================================================================
"""


class DesktopARGPuzzle:
    """Manages spawning and cleaning up ARG puzzle files on the user's desktop."""

    def __init__(self, target_dir: Optional[str] = None):
        if target_dir:
            self.desktop_path = Path(target_dir)
        else:
            self.desktop_path = Path(os.path.expanduser("~/Desktop"))
            if not self.desktop_path.exists():
                self.desktop_path = Path(os.path.expanduser("~/OneDrive/Masaüstü"))
            if not self.desktop_path.exists():
                self.desktop_path = Path(os.path.expanduser("~/Masaüstü"))
            if not self.desktop_path.exists():
                self.desktop_path = Path(os.path.expanduser("~/OneDrive/Desktop"))
            if not self.desktop_path.exists():
                self.desktop_path = Path(os.path.expanduser("~"))

        self.created_files: List[Path] = []
        self.active_config: Optional[ARGPuzzleConfig] = None

    def deploy_puzzle_files(self, config: Optional[ARGPuzzleConfig] = None) -> List[str]:
        """Create ARG clues and encrypted files on Desktop with dynamic puzzle keys."""
        if config is None:
            config = generate_random_arg_puzzle()
        self.active_config = config

        report_text = format_incident_report(config)
        sector_text = format_encrypted_sector(config)

        files_to_create = [
            ("SENTIENT_INCIDENT_REPORT_89.txt", report_text),
            ("ENCRYPTED_SECTOR_0x4F.txt", sector_text),
            ("ENCRYPTED_SECTOR_0x4F.dat", sector_text),
        ]

        paths_created = []
        for filename, content in files_to_create:
            file_path = self.desktop_path / filename
            try:
                file_path.write_text(content, encoding="utf-8")
                self.created_files.append(file_path)
                paths_created.append(str(file_path))
                logger.info(f"ARG puzzle file created: {file_path}")
            except Exception as e:
                logger.error(f"Failed to create ARG puzzle file {file_path}: {e}")

        return paths_created

    def cleanup(self) -> None:
        """Remove all spawned ARG puzzle files safely."""
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Removed ARG puzzle file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove ARG puzzle file {file_path}: {e}")
        self.created_files.clear()
