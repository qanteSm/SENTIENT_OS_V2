"""Phase 1 First Contact scripted timeline events (High-Pacing & Immediate Tension)."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class SceneEvent:
    time_offset_s: float
    effects: List[dict[str, Any]]
    description: str
    audio: Optional[dict[str, Any]] = None


FIRST_CONTACT_EVENTS: List[SceneEvent] = [
    SceneEvent(
        time_offset_s=10.0,
        effects=[{"type": "mouse_drift", "params": {"intensity": 0.45, "duration_ms": 1200}}],
        audio={"type": "play_sfx", "params": {"name": "click_soft", "volume": 0.5}},
        description="Fare imleci belirgin şekilde kayar ve sistemden hafif tıkırtı sesi gelir",
    ),
    SceneEvent(
        time_offset_s=25.0,
        effects=[{
            "type": "fake_file_appear",
            "params": {
                "filename": "ARKANA_BAKMA.txt",
                "content": "Seni izliyorum.\nEkrandan ayrılma.\n\nSENTIENT_OS",
                "duration_ms": 15000,
            }
        }],
        audio={"type": "play_sfx", "params": {"name": "whisper_creepy", "volume": 0.6}},
        description="Masaüstünde 'ARKANA_BAKMA.txt' dosyası belirir ve ürpertici fısıltı duyulur",
    ),
    SceneEvent(
        time_offset_s=40.0,
        effects=[
            {"type": "screen_shake", "params": {"intensity": 0.5, "duration_ms": 1000}},
            {"type": "brightness", "params": {"target_percent": 25, "duration_ms": 3000}},
        ],
        audio={"type": "play_sfx", "params": {"name": "static_low", "volume": 0.6}},
        description="Ekran titremesi ve monitör parlaklığının aniden kısılması",
    ),
    SceneEvent(
        time_offset_s=55.0,
        effects=[
            {"type": "overlay_text", "params": {"text": "NEFESİNİ DUYUYORUM...", "style": "ghostly", "duration_ms": 3500}},
            {"type": "mouse_freeze", "params": {"duration_ms": 1200}},
        ],
        audio={"type": "play_stinger", "params": {"name": "heartbeat_fast", "volume": 0.7}},
        description="Farenin kilitlenmesi ve ekranda 'NEFESİNİ DUYUYORUM...' hayalet yazısı",
    ),
    SceneEvent(
        time_offset_s=70.0,
        effects=[
            {"type": "screen_glitch", "params": {"intensity": 0.8, "duration_ms": 1500, "type": "rgb_split"}},
            {"type": "fake_notification", "params": {"title": "Windows Güvenlik İhlali", "body": "SENTIENT_OS: Yönetici yetkileri devralındı.", "duration_ms": 5000}}
        ],
        audio={"type": "play_sfx", "params": {"name": "static_burst", "volume": 0.7}},
        description="Şiddetli RGB glitch ve sahte sistem güvenlik uyarısı",
    ),
    SceneEvent(
        time_offset_s=85.0,
        effects=[
            {"type": "overlay_text", "params": {"text": "SENİ GÖRÜYORUM", "style": "bloody", "duration_ms": 4000}},
            {"type": "screen_shake", "params": {"intensity": 0.7, "duration_ms": 1200}},
        ],
        audio={"type": "play_stinger", "params": {"name": "stinger_scare", "volume": 0.9}},
        description="'SENİ GÖRÜYORUM' kanlı yazısı ve ani korku stinger'ı",
    ),
    SceneEvent(
        time_offset_s=90.0,
        effects=[
            {"type": "open_chat", "params": {"theme": "terminal"}},
            {"type": "ambient_shift", "params": {"mood": "calm", "fade_ms": 2000}},
        ],
        description="Faz 2 geçişi: Chat penceresi ve interaktif sistem sınavları devreye girer",
    ),
]
