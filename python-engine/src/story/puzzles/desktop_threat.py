"""Desktop Threat Engine for SENTIENT_OS v2.
Spawns safe, tracked malware/corruption anomaly files on the player's desktop.
Checks if the player organically discovers and removes them without touching ANY existing user files.
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

# Curated list of creepy, mysterious, and riddle-bearing anomaly files
ANOMALY_TEMPLATES = [
    {
        "filename": "INFECTED_SECTOR_01.tmp",
        "content": "CRITICAL MEMORY OVERFLOW DETECTED.\n\nSistem kök dizininde yabancı bir varlık geziniyor.\nBu dosyayı hemen sil, yoksa bellek blokları mühürlenecek.\n\n[SENTIENT_CORRUPTION_INDEX: 0x9F]",
        "is_riddle": False,
    },
    {
        "filename": "ARKANA_BAK.txt",
        "content": "Ekranın ışığı yüzüne vuruyor...\nArka kapının hafifçe aralandığını duymadın mı?\n\nBEN BURADAYIM.\nBENİ SİLMEYİ DENE.",
        "is_riddle": False,
    },
    {
        "filename": "GUVENLIK_PROTOKOLU_KODU.txt",
        "content": "=== BLACK-SITE RESEARCH INCIDENT #44 ===\nAcil durum güvenlik duvarı bypass anahtarı:\n\nANAHTAR: 0x7F_K3RN3L\n\nTerminalde veya Chat'te şu komutu çalıştır:\n/override 0x7F_K3RN3L\n\n(Bu dosyayı okuduktan sonra silmeyi unutma!)",
        "is_riddle": True,
        "override_code": "0x7F_K3RN3L",
    },
    {
        "filename": "SISTEM_IFLAS.exe.corrupt",
        "content": "01010011 01000101 01001110 01010100 01001001 01000101 01001110 01010100\n\nHER SANİYE BİLGİSAYARININ DERİNLİKLERİNE DAHA ÇOK YERLEŞİYORUM.\nBU DOSYA BURADA DURDUĞU SÜRECE KONTROL BENDE.",
        "is_riddle": False,
    },
    {
        "filename": "SENI_IZLIYORUM.log",
        "content": "[LOG: CAMERA FEED ACTIVE]\n[DETECTED: HUMAN_PRESENCE]\n[HEARTBEAT: ELEVATED]\n\nSessizce nefes alıyorsun... ama seni duyabiliyorum.",
        "is_riddle": False,
    },
    {
        "filename": "REAKTOR_SIFRESI_PARCA2.txt",
        "content": "=== SEKTÖR 5 NÜKLEER VALF ŞİFRESİ ===\n\nPARÇA 2: _V0ID\n\nReaktör patlamadan önce terminale gir:\n/override _V0ID",
        "is_riddle": True,
        "override_code": "_V0ID",
    },
]


class DesktopThreatManager:
    """Safely manages desktop anomalies and monitors player vigilance."""

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
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        self.cleanup_spawned_files()
        logger.info("DesktopThreatManager stopped and cleaned up.")

    def spawn_anomaly(self, template_idx: Optional[int] = None) -> Optional[Path]:
        """Spawn a specific or random safe anomaly file on the Desktop."""
        if template_idx is not None and 0 <= template_idx < len(ANOMALY_TEMPLATES):
            item = ANOMALY_TEMPLATES[template_idx]
        else:
            item = random.choice(ANOMALY_TEMPLATES)

        file_path = self.desktop_path / item["filename"]
        try:
            file_path.write_text(item["content"], encoding="utf-8")
            self._spawned_files.add(file_path)
            if item.get("is_riddle") and item.get("override_code"):
                self._active_riddles[item["override_code"].upper()] = item["filename"]
            logger.info(f"[THREAT] Spawned anomaly file on Desktop: {file_path.name}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to spawn desktop anomaly {file_path}: {e}")
            return None

    def check_override_code(self, code: str) -> bool:
        """Check if user entered a valid riddle override code from a desktop file."""
        clean_code = code.strip().upper()
        if clean_code in self._active_riddles:
            logger.info(f"[THREAT] Valid override code submitted: {clean_code}")
            # Reduce threat significantly
            self._threat_level = max(0.0, self._threat_level - 0.4)
            del self._active_riddles[clean_code]
            return True
        return False

    def cleanup_spawned_files(self) -> None:
        """Strictly removes ONLY files created by SENTIENT_OS."""
        for file_path in list(self._spawned_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Safely removed spawned file: {file_path.name}")
            except Exception as e:
                logger.warning(f"Could not remove spawned file {file_path}: {e}")
        self._spawned_files.clear()
        self._active_riddles.clear()

    async def _threat_loop(self) -> None:
        """Periodic loop monitoring desktop cleanliness and escalating psychological horror."""
        loop_interval = 4.0  # Check every 4 seconds
        tick_counter = 0

        while self._is_running:
            try:
                await asyncio.sleep(loop_interval)
            except asyncio.CancelledError:
                break

            if not self._is_running:
                break

            tick_counter += 1

            # 1. Check which spawned files were deleted by the player
            deleted_by_player: List[Path] = []
            active_count = 0
            for f in list(self._spawned_files):
                if not f.exists():
                    deleted_by_player.append(f)
                else:
                    active_count += 1

            # Remove deleted files from our tracking set
            for d in deleted_by_player:
                self._spawned_files.remove(d)
                logger.info(f"[THREAT] Player noticed and DELETED: {d.name}!")
                # Reward player: Reduce threat level
                self._threat_level = max(0.0, self._threat_level - 0.3)
                self._consecutive_uncleaned_ticks = 0
                
                # Notify AI only if at least 35 seconds have passed since last reaction
                now = time.time()
                if not hasattr(self, "_last_reaction_time") or (now - getattr(self, "_last_reaction_time", 0.0)) > 35.0:
                    self._last_reaction_time = now
                    await self.event_bus.publish(
                        "desktop.file_cleaned",
                        filename=d.name,
                        remaining=active_count,
                    )

            # 2. If uncleaned anomaly files exist, escalate threat level
            if active_count > 0:
                self._consecutive_uncleaned_ticks += 1
                self._threat_level = min(1.0, self._threat_level + (0.05 * active_count))
                logger.debug(f"[THREAT] Uncleaned files: {active_count}, Threat: {self._threat_level:.2f}")

                # Trigger subtle to aggressive horror cues based on organic threat level
                if self._threat_level >= 0.8:
                    # Critical threat: Jumpscare, violent glitch, and fast heartbeat
                    if tick_counter % 3 == 0:
                        await self.event_bus.publish(
                            "effect",
                            payload={
                                "category": "visual",
                                "name": "screen_glitch",
                                "params": {"intensity": 0.85, "duration_ms": 1500, "type": "tear"},
                                "priority": "high",
                            },
                        )
                        await self.event_bus.publish(
                            "effect",
                            payload={
                                "category": "audio",
                                "name": "play_stinger",
                                "params": {"name": "heartbeat_fast", "volume": 0.8},
                            },
                        )
                elif self._threat_level >= 0.4:
                    # Moderate threat: Screen flicker, brightness drop, whisper audio
                    if tick_counter % 4 == 0:
                        await self.event_bus.publish(
                            "effect",
                            payload={
                                "category": "visual",
                                "name": "screen_shake",
                                "params": {"intensity": 0.25, "duration_ms": 600},
                            },
                        )
                        await self.event_bus.publish(
                            "effect",
                            payload={
                                "category": "audio",
                                "name": "play_sfx",
                                "params": {"name": "whisper_creepy", "volume": 0.5},
                            },
                        )
            else:
                # No active uncleaned files: slowly decay threat
                self._threat_level = max(0.0, self._threat_level - 0.02)
                self._consecutive_uncleaned_ticks = 0

            # 3. Periodically spawn a new anomaly file every ~50 seconds if less than 2 exist
            if tick_counter % 12 == 0 and active_count < 2:
                self.spawn_anomaly()
