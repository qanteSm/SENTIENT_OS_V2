"""Persistent CCTV Surveillance and Paranormal Anomaly Threat Engine for SENTIENT_OS v2.
Monitors periodic security breaches across 6 camera channels.
If an anomaly is left undetected for > 3 minutes (180s), the entity breaches the room!
"""

import asyncio
import random
import time
from typing import Any, Dict, Optional

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("cctv_threat")

ANOMALY_ROOMS = [
    {"cam": 2, "name": "CAM 02 // SUNUCU ODASI", "desc": "Sunucu kabinleri arasında gölge varlık"},
    {"cam": 3, "name": "CAM 03 // ARAŞTIRMA LABI", "desc": "Gözetleme camına bakan manken"},
    {"cam": 4, "name": "CAM 04 // KARANLIK KORİDOR", "desc": "Koridorda yaklaşan siluet"},
    {"cam": 5, "name": "CAM 05 // HAVALANDIRMA", "desc": "Izgarada kanlı glitch sembolü"},
    {"cam": 6, "name": "CAM 06 // GÜVENLİK KAPISI", "desc": "Kilitli kapının aralanması"},
]


class CCTVThreatEngine:
    """Manages background paranormal anomalies in the security surveillance feeds."""

    def __init__(self, event_bus: EventBus, breach_timeout_sec: float = 180.0):
        self.event_bus = event_bus
        self.breach_timeout_sec = breach_timeout_sec

        self.active_anomaly: Optional[Dict[str, Any]] = None
        self.anomaly_spawn_time: float = 0.0
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    @property
    def has_active_anomaly(self) -> bool:
        return self.active_anomaly is not None

    @property
    def time_remaining_sec(self) -> float:
        if not self.active_anomaly:
            return 0.0
        elapsed = time.time() - self.anomaly_spawn_time
        return max(0.0, self.breach_timeout_sec - elapsed)

    async def start(self) -> None:
        """Start background surveillance monitoring loop."""
        if self._is_running:
            return
        self._is_running = True
        self._loop_task = asyncio.create_task(self._surveillance_loop())
        logger.info("CCTVThreatEngine surveillance monitor started.")

    async def stop(self) -> None:
        """Stop monitor cleanly."""
        self._is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        self.active_anomaly = None
        logger.info("CCTVThreatEngine stopped.")

    def spawn_random_anomaly(self) -> Dict[str, Any]:
        """Spawn a new paranormal entity on a random camera channel."""
        picked = random.choice(ANOMALY_ROOMS)
        self.active_anomaly = {
            "cam": picked["cam"],
            "name": picked["name"],
            "desc": picked["desc"],
        }
        self.anomaly_spawn_time = time.time()
        logger.info(f"[CCTV] Paranormal Anomaly spawned on {picked['name']}: {picked['desc']} (3 min timeout)")
        return self.active_anomaly

    def clear_anomaly(self) -> bool:
        """Neutralize active anomaly when player catches it in CCTV minigame."""
        if self.active_anomaly:
            logger.info(f"[CCTV] Anomaly neutralized on {self.active_anomaly['name']}!")
            self.active_anomaly = None
            self.anomaly_spawn_time = 0.0
            return True
        return False

    def get_status_report(self) -> str:
        """Report surveillance status for chat / terminal."""
        if self.active_anomaly:
            rem_min = int(self.time_remaining_sec // 60)
            rem_sec = int(self.time_remaining_sec % 60)
            return (
                f"🚨 [CCTV GÜVENLİK ALARMI // DİKKAT]:\n"
                f"Kameralardan birinde paranormal anomali tespit edildi!\n"
                f"Kalan Süre: {rem_min:02d}:{rem_sec:02d}\n"
                f"Derhal /cctv yazarak veya butona basarak kameraları tara ve varlığı yakala!"
            )
        return "🟢 [CCTV GÜVENLİK KAMERALARI TEMİZ // ANOMALİ TESPİT EDİLMEDİ]"

    async def _surveillance_loop(self) -> None:
        """Periodic background loop checking timeout and spawning anomalies every 90-150s."""
        tick = 0
        while self._is_running:
            try:
                await asyncio.sleep(4.0)
            except asyncio.CancelledError:
                break

            if not self._is_running:
                break

            tick += 1

            # 1. If active anomaly exists, check if deadline exceeded (3 mins)
            if self.active_anomaly:
                if self.time_remaining_sec <= 0.0:
                    logger.warning(f"[CCTV] 3 MINUTE DEADLINE EXPIRED! Entity breached security room from {self.active_anomaly['name']}!")
                    # Trigger Critical Jumpscare and System Punishment
                    await self.event_bus.publish(
                        "effect",
                        payload={
                            "category": "visual",
                            "name": "jumpscare",
                            "params": {"duration_ms": 1500},
                            "priority": "critical",
                        },
                    )
                    await self.event_bus.publish(
                        "effect",
                        payload={
                            "category": "audio",
                            "name": "play_stinger",
                            "params": {"name": "stinger_scare", "volume": 1.0},
                        },
                    )
                    await self.event_bus.publish(
                        "ai_response",
                        payload={
                            "speech": (
                                f"3 dakikadır kameraları kontrol etmedin... {self.active_anomaly['name']} üzerinden sızdı.\n"
                                "Varlık artık senin odanda!"
                            ),
                            "emotion": "angry",
                            "actions": [{"type": "screen_glitch", "params": {"intensity": 0.9, "duration_ms": 2000}}],
                        },
                    )
                    # Clear anomaly after breach
                    self.active_anomaly = None
                elif tick % 15 == 0:
                    # Subtle audio/visual hint that cameras have noise
                    await self.event_bus.publish(
                        "effect",
                        payload={"category": "audio", "name": "play_sfx", "params": {"name": "static_low", "volume": 0.4}},
                    )
            else:
                # 2. If no anomaly, spawn one every ~100 seconds (25 ticks of 4s)
                if tick >= 25:
                    tick = 0
                    self.spawn_random_anomaly()
                    # Creepy hint in chat
                    hints = [
                        "Güvenlik kameralarından birinin sinyali bozuluyor...",
                        "Havalandırmadan ayak sesleri geliyor... Gözlerin kameralarda olsun.",
                        "Monitörün arkasındaki gölgeleri fark ettin mi?",
                    ]
                    await self.event_bus.publish(
                        "ai_response",
                        payload={"speech": random.choice(hints), "emotion": "sinister", "actions": []},
                    )
