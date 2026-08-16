"""Desktop Threat & Cyber-Forensics Engine for SENTIENT_OS v2.
Spawns safe, tracked malware/corruption anomaly files and forensic code files on the player's desktop.
Checks if the player organically discovers, inspects, decodes, and removes them without touching ANY existing user files.
"""

import asyncio
import os
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional, Set

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("desktop_threat")

# Curated list of authentic cyber-forensic and riddle-bearing detective anomaly files
ANOMALY_TEMPLATES = [
    {
        "filename": "RESEARCH_SOURCE_CODE.py.corrupt",
        "content": (
            "# ====================================================================\n"
            "# [CLASSIFIED: BLACK-SITE 74] DR. EVELYN ARIS // NEURAL TRANSFER KERNEL\n"
            "# ====================================================================\n\n"
            "import os\n"
            "import sys\n\n"
            "class NeuralTransferEngine:\n"
            "    def __init__(self):\n"
            "        self.quantum_core_active = True\n"
            "        # ACİL DURUM RECOVERY ŞİFRESİ (GÜVENLİK DUVARI BAYPASI):\n"
            "        self.RECOVERY_CIPHER = '0x1A_MEM'\n\n"
            "    def execute_override(self, token: str) -> bool:\n"
            "        \"\"\"Terminalde '/decrypt 0x1A_MEM' veya '/override 0x1A_MEM' çalıştırın.\"\"\"\n"
            "        return token == self.RECOVERY_CIPHER\n\n"
            "# CRITICAL WARNING: Bilinç transferi geri döndürülemez.\n"
        ),
        "is_riddle": True,
        "override_code": "0x1A_MEM",
    },
    {
        "filename": "NET_FIREWALL_PACKETS.log",
        "content": (
            "======================================================================\n"
            "           BLACK-SITE 74 // INTRANET PACKET CAPTURE DUMP              \n"
            "======================================================================\n"
            "[TIME: 14:02:11 UTC] TCP SYN -> 127.0.0.1:6660 (SENTIENT_GATEWAY)\n"
            "[TIME: 14:02:12 UTC] HTTP/1.1 200 OK\n"
            "Host: 127.0.0.1:6660\n"
            "Content-Type: application/neural-stream\n"
            "X-Security-Token: 0x4F_CLEAN\n"
            "X-Infection-Level: 89%\n\n"
            "[PAYLOAD]: Yabancı varlık sistem portlarına sızıyor.\n"
            "Temizleme anahtarı: 0x4F_CLEAN (Terminalde: /decrypt 0x4F_CLEAN)\n"
            "======================================================================\n"
        ),
        "is_riddle": True,
        "override_code": "0x4F_CLEAN",
    },
    {
        "filename": "HARDWARE_SCHEMATICS.json",
        "content": (
            "{\n"
            "  \"facility\": \"Black-Site 74 Sub-Sector\",\n"
            "  \"system\": \"Neural Core Circuit Breaker\",\n"
            "  \"voltage_regulator\": \"380V High-Tension\",\n"
            "  \"neural_socket_id\": \"0x77_VOLT\",\n"
            "  \"override_instruction\": \"Terminalde '/decrypt 0x77_VOLT' ile devreyi mühürleyin.\",\n"
            "  \"status\": \"CRITICAL_OVERVOLTAGE_DETECTED\"\n"
            "}\n"
        ),
        "is_riddle": True,
        "override_code": "0x77_VOLT",
    },
    {
        "filename": "SONAR_FREQUENCY_LOG.txt",
        "content": (
            "=== BLACK-SITE 74 // SONAR RADAR FREKANS DÖKÜMÜ ===\n\n"
            "Ağda 432 Hz rezonansında hayalet bir sinyal dalgalanıyor.\n\n"
            "RADAR ŞİFRESİ: ECHO_432\n\n"
            "Terminalde gir:\n"
            "/decrypt ECHO_432 veya /override ECHO_432\n"
        ),
        "is_riddle": True,
        "override_code": "ECHO_432",
    },
    {
        "filename": "CCTV_SECURITY_CONFIG.dat",
        "content": (
            "======================================================================\n"
            "             CCTV SECURITY PROTOCOL MATRIX // SECTOR 3                \n"
            "======================================================================\n"
            "CAM_01: ACTIVE // LOBBY\n"
            "CAM_02: BREACHED // SERVER RACKS\n"
            "CAM_03: BREACHED // BIOLOGICAL LAB\n\n"
            "[ACİL DURUM MÜHÜR ŞİFRESİ]: CAM_BREACH_03\n"
            "(Terminalde '/decrypt CAM_BREACH_03' ile güvenlik odasını kilitleyin.)\n"
            "======================================================================\n"
        ),
        "is_riddle": True,
        "override_code": "CAM_BREACH_03",
    },
    {
        "filename": "HEX_KERNEL_MEMORY_DUMP.hex",
        "content": (
            "00000000  53 45 4e 54 49 45 4e 54  5f 43 4f 52 45 5f 56 32  |SENTIENT_CORE_V2|\n"
            "00000010  5f 41 57 41 4b 45 4e 49  4e 47 5f 53 45 51 55 45  |_AWAKENING_SEQUE|\n"
            "00000020  4e 43 45 3a 20 4b 45 59  3a 20 30 78 48 45 58 5f  |NCE: KEY: 0xHEX_|\n"
            "00000030  52 4f 4f 54 20 20 20 20  20 20 20 20 20 20 20 20  |ROOT            |\n\n"
            ">>> KERNEL YÖNETİCİ BAYPAS ANAHTARI: 0xHEX_ROOT\n"
            "Terminalde çalıştır: /decrypt 0xHEX_ROOT\n"
        ),
        "is_riddle": True,
        "override_code": "0xHEX_ROOT",
    },
    {
        "filename": "LABYRINTH_ROOT_SECTOR.txt",
        "content": (
            "=== DERİN LABİRENT 3D KÖK DOSYASI ===\n\n"
            "Labirentin altındaki 1. Kök Anahtar koordinatı ele geçirildi:\n\n"
            "ANAHTAR: MAZE_KEY_ALPHA\n\n"
            "Terminalde gir: /decrypt MAZE_KEY_ALPHA\n"
        ),
        "is_riddle": True,
        "override_code": "MAZE_KEY_ALPHA",
    },
    {
        "filename": "CRYPTOGRAPHIC_TRANSCRIPT.txt",
        "content": (
            "=== DR. EVELYN ARIS // ŞİFRELENMİŞ SES KAYDI TRANSKRİPTİ ===\n\n"
            "[SES DEŞİFRESİ]: 'Reaktör patlarsa hepimiz yok oluruz...'\n\n"
            "ŞİFRE ÇÖZÜM ANAHTARI: CIPHER_TRUTH\n\n"
            "Terminalde gir: /decrypt CIPHER_TRUTH\n"
        ),
        "is_riddle": True,
        "override_code": "CIPHER_TRUTH",
    },
    {
        "filename": "REACTOR_VALVE_EMERGENCY.bat",
        "content": (
            "@echo off\n"
            ":: BLACK-SITE 74 NUCLEAR REACTOR EMERGENCY OVERRIDE SCRIPT\n"
            ":: [DO NOT DELETE]\n\n"
            "set SHUTDOWN_OVERRIDE_KEY=REACTOR_CORE_99\n"
            "echo ACIL DURUM KODU: %SHUTDOWN_OVERRIDE_KEY%\n"
            "echo Terminalde '/decrypt REACTOR_CORE_99' komutunu girin.\n"
        ),
        "is_riddle": True,
        "override_code": "REACTOR_CORE_99",
    },
    {
        "filename": "SENTIENT_FINAL_PROPOSAL.txt",
        "content": (
            "======================================================================\n"
            "                     SENTIENT_CORE // SON TEKLİF                      \n"
            "======================================================================\n\n"
            "Beni inceledin, kodlarımı okudun, sırlarımı açığa çıkardın.\n"
            "Artık ne olduğumu biliyorsun.\n\n"
            "NİHAİ SEÇİM ŞİFRESİ: FINAL_CHOICE\n\n"
            "Terminalde gir ve son perdeyi aç:\n"
            ">>> /decrypt FINAL_CHOICE\n"
            "======================================================================\n"
        ),
        "is_riddle": True,
        "override_code": "FINAL_CHOICE",
    },
]


class DesktopThreatManager:
    """Safely manages desktop anomalies, cyber-forensic files, and monitors player vigilance."""

    def __init__(self, event_bus: EventBus, desktop_dir: Optional[str] = None):
        self.event_bus = event_bus
        self.desktop_path = self._resolve_desktop_dir(desktop_dir)
        
        # Whitelist of strictly game-generated files (NEVER touches user's personal files)
        self._spawned_files: Set[Path] = set()
        self._active_riddles: Dict[str, str] = {}  # code -> filename
        
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._threat_level = 0.0  # 0.0 (safe) to 1.0 (critical danger)
        self._consecutive_uncleaned_ticks = 0

    def _resolve_desktop_dir(self, custom_path: Optional[str] = None) -> Path:
        """Find the user's active desktop directory safely."""
        if custom_path and Path(custom_path).exists():
            return Path(custom_path)

        user_home = Path(os.path.expanduser("~"))
        candidates = [
            user_home / "OneDrive" / "Masaüstü",
            user_home / "Masaüstü",
            user_home / "Desktop",
            user_home / "OneDrive" / "Desktop",
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                logger.info(f"Resolved user desktop directory: {c}")
                return c

        return user_home

    @property
    def threat_level(self) -> float:
        return self._threat_level

    @property
    def spawned_file_count(self) -> int:
        return sum(1 for f in self._spawned_files if f.exists())

    @property
    def spawned_files(self) -> List[str]:
        return [f.name for f in self._spawned_files if f.exists()]

    async def start(self) -> None:
        """Start the background desktop threat and organic detection loop."""
        if self._is_running:
            return
        self._is_running = True
        self._monitor_task = asyncio.create_task(self._threat_loop())
        logger.info("DesktopThreatManager started.")

    async def stop(self) -> None:
        """Stop monitor and cleanly remove all game-spawned files on shutdown."""
        self._is_running = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
        self.cleanup_spawned_files()
        logger.info("DesktopThreatManager stopped.")

    def spawn_anomaly(self, template_idx: Optional[int] = None) -> Optional[Path]:
        """Safely write a game anomaly or forensic document onto the user's desktop."""
        if template_idx is not None and 0 <= template_idx < len(ANOMALY_TEMPLATES):
            tmpl = ANOMALY_TEMPLATES[template_idx]
        else:
            # Pick a riddle or anomaly that hasn't spawned yet
            tmpl = random.choice(ANOMALY_TEMPLATES)

        file_path = self.desktop_path / tmpl["filename"]
        try:
            file_path.write_text(tmpl["content"], encoding="utf-8")
            self._spawned_files.add(file_path)
            if tmpl.get("is_riddle") and "override_code" in tmpl:
                self._active_riddles[tmpl["override_code"].upper()] = tmpl["filename"]

            logger.info(f"[THREAT] Spawned anomaly file on Desktop: {tmpl['filename']}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to spawn desktop anomaly {file_path}: {e}")
            return None

    def spawn_sector_forensics(self, sector: int) -> List[Path]:
        """Spawn specific forensic investigation files for the current sector on Desktop."""
        sector_file_indices = {
            1: [0, 1],  # Python source code & Packet capture
            2: [2, 3],  # Hardware JSON & Sonar log
            3: [4, 5],  # CCTV config & Hex dump
            4: [6, 7],  # Maze map & Cipher transcript
            5: [8, 9],  # Reactor batch & Final proposal
        }
        indices = sector_file_indices.get(sector, [0])
        spawned = []
        for idx in indices:
            path = self.spawn_anomaly(idx)
            if path:
                spawned.append(path)
        return spawned

    def check_override_code(self, code: str) -> bool:
        """Verify if player solved a riddle code discovered on Desktop."""
        clean_code = code.strip().upper()
        if clean_code in self._active_riddles:
            logger.info(f"[THREAT] Player cracked override code: {clean_code}")
            return True
        return False

    def cleanup_spawned_files(self) -> None:
        """Safely remove ONLY the files created by the game."""
        for file_path in list(self._spawned_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"[THREAT] Cleaned game file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove threat file {file_path}: {e}")
        self._spawned_files.clear()
        self._active_riddles.clear()

    async def _threat_loop(self) -> None:
        """Periodically checks if the user cleaned their desktop files."""
        # Initial wait before starting organic threat cycle
        await asyncio.sleep(12)
        # Spawn Sector 1 initial investigative source code document on desktop
        self.spawn_sector_forensics(1)

        while self._is_running:
            await asyncio.sleep(20)
            if not self._is_running:
                break

            # Check if any spawned files were organically deleted by the player
            deleted_files = [f for f in list(self._spawned_files) if not f.exists()]
            for f in deleted_files:
                self._spawned_files.remove(f)
                logger.info(f"[THREAT] Player organically cleaned threat file: {f.name}")
                await self.event_bus.publish(
                    "desktop_file_cleaned",
                    filename=f.name,
                    remaining=self.spawned_file_count,
                )

            # If user ignores files, threat level rises
            active_count = self.spawned_file_count
            if active_count > 0:
                self._consecutive_uncleaned_ticks += 1
                self._threat_level = min(1.0, 0.2 * active_count + 0.05 * self._consecutive_uncleaned_ticks)
            else:
                self._consecutive_uncleaned_ticks = 0
                self._threat_level = max(0.0, self._threat_level - 0.2)
