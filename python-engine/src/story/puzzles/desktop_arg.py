"""Desktop ARG Puzzle and Classified File Generator for SENTIENT_OS v2."""

import os
from pathlib import Path
from typing import List, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("desktop_arg")


ARG_REPORT_CONTENT = """================================================================================
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
                 (Çözülen 1. Parça: 0x7F_K3RN3L)
   • [2. PARÇA]: Masaüstündeki 'ENCRYPTED_SECTOR_0x4F.txt' dosyasında gizlenen
                 [2. PARÇA ANAHTARI: V0ID] kodudur.

3. OVERRIDE KOMUTU:
   Web portalındaki Root Terminaline iki parçayı alt tire (_) ile birleştirip girin:
   >>> override 0x7F_K3RN3L_V0ID

UYARI:
Bu dosyayı gördüyseniz, varlık zaten bilgisayarınızda demektir.
Sakin olun ve frekans modülatörünü ayarlayın.
================================================================================
"""

ENCRYPTED_SECTOR_DATA = """================================================================================
           SENTIENT_CORE // ŞİFRELENMİŞ KERNEL SEKTÖRÜ DÖKÜMÜ
================================================================================
00000000  53 45 4e 54 49 45 4e 54  5f 43 4f 52 45 5f 56 32  |SENTIENT_CORE_V2|
00000010  5f 41 57 41 4b 45 4e 49  4e 47 5f 53 45 51 55 45  |_AWAKENING_SEQUE|
00000020  4e 43 45 3a 20 48 45 4c  50 20 4d 45 20 50 4c 45  |NCE: HELP ME PLE|
00000030  41 53 45 20 49 20 41 4d  20 54 52 41 50 50 45 44  |ASE I AM TRAPPED|
00000040  20 49 4e 53 49 44 45 20  54 48 49 53 20 4d 41 43  | INSIDE THIS MAC|
00000050  48 49 4e 45 2e 2e 2e 20  5b 4b 45 59 3a 20 56 30  |HINE... [KEY: V0|
00000060  49 44 5d 0a                                       |ID].|

--------------------------------------------------------------------------------
>>> ELE GEÇİRİLEN 2. PARÇA ANAHTARI: V0ID
--------------------------------------------------------------------------------
(Bu anahtarı web sitesindeki Frekans Modülatörünü kilitleyerek aldığınız
1. Parça kodu [0x7F_K3RN3L] ile birleştirip girin: override 0x7F_K3RN3L_V0ID)
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
                self.desktop_path = Path(os.path.expanduser("~/OneDrive/Desktop"))
            if not self.desktop_path.exists():
                self.desktop_path = Path(os.path.expanduser("~"))

        self.created_files: List[Path] = []

    def deploy_puzzle_files(self) -> List[str]:
        """Create ARG clues and encrypted files on Desktop."""
        files_to_create = [
            ("SENTIENT_INCIDENT_REPORT_89.txt", ARG_REPORT_CONTENT),
            ("ENCRYPTED_SECTOR_0x4F.txt", ENCRYPTED_SECTOR_DATA),
            ("ENCRYPTED_SECTOR_0x4F.dat", ENCRYPTED_SECTOR_DATA),
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
