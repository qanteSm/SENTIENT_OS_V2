"""Phase 1 First Contact scripted timeline events."""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class SceneEvent:
    time_offset_s: float
    effects: List[dict[str, Any]]
    description: str
    audio: Optional[dict[str, Any]] = None


FIRST_CONTACT_EVENTS: List[SceneEvent] = [
    SceneEvent(
        time_offset_s=30.0,
        effects=[{"type": "mouse_drift", "params": {"intensity": 0.1, "duration_ms": 200}}],
        description="Fare imleci hafifçe kayar",
    ),
    SceneEvent(
        time_offset_s=60.0,
        effects=[{"type": "fake_file_appear", "params": {"filename": "readme.txt", "duration_ms": 3000}}],
        audio={"type": "play_sfx", "params": {"name": "click_soft", "volume": 0.3}},
        description="Masaüstünde geçici dosya belirir",
    ),
    SceneEvent(
        time_offset_s=90.0,
        effects=[{"type": "overlay_text", "params": {"text": "merhaba", "style": "ghostly", "duration_ms": 2000}}],
        description="Soluk 'merhaba' yazısı belirir",
    ),
    SceneEvent(
        time_offset_s=120.0,
        effects=[{"type": "system_clock_shift", "params": {"offset_seconds": -60}}],
        description="Sistem saati görsel olarak 1 dakika geri gider",
    ),
    SceneEvent(
        time_offset_s=150.0,
        effects=[{"type": "screen_shake", "params": {"intensity": 0.05, "duration_ms": 500}}],
        audio={"type": "play_sfx", "params": {"name": "static_low", "volume": 0.2}},
        description="Hafif ekran titremesi",
    ),
    SceneEvent(
        time_offset_s=180.0,
        effects=[{"type": "log_message", "params": {"text": "Bağlantı kuruldu. Hedef bulundu."}}],
        description="Sahte log mesajı",
    ),
    SceneEvent(
        time_offset_s=210.0,
        effects=[{"type": "screen_glitch", "params": {"intensity": 0.1, "duration_ms": 1000, "type": "desaturate"}}],
        description="Ekran renkleri anlık desatüre olur",
    ),
    SceneEvent(
        time_offset_s=240.0,
        effects=[{
            "type": "fake_notification",
            "params": {"title": "Güvenlik Uyarısı", "body": "Bilinmeyen uygulama ağ erişimi istiyor", "duration_ms": 3000}
        }],
        description="Sahte sistem güvenlik bildirimi",
    ),
    SceneEvent(
        time_offset_s=270.0,
        effects=[
            {"type": "overlay_text", "params": {"text": "SENİ GÖRÜYORUM", "style": "glitched", "duration_ms": 1500}},
            {"type": "screen_glitch", "params": {"intensity": 0.4, "duration_ms": 800}},
        ],
        audio={"type": "play_stinger", "params": {"name": "stinger_scare", "volume": 0.7}},
        description="'SENİ GÖRÜYORUM' yazısı ve glitch efekti",
    ),
    SceneEvent(
        time_offset_s=300.0,
        effects=[
            {"type": "open_chat", "params": {"theme": "terminal"}},
            {"type": "ambient_shift", "params": {"mood": "calm", "fade_ms": 3000}},
        ],
        description="Katman 2 geçişi: Chat penceresi açılır ve ambient ses başlar",
    ),
]
