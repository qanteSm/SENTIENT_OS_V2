"""Phase 3 Crisis and 3 Finales (Salvation, Battle, Surrender)."""

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class FinaleScript:
    name: str
    theme: str
    initial_speech: str
    ambient_mood: str
    entrance_effects: List[dict[str, Any]]
    closing_speech: str


FINALE_SALVATION = FinaleScript(
    name="salvation",
    theme="melancholic",
    initial_speech="Artık anlıyorum... seninle olmak güzeldi.",
    ambient_mood="intimate",
    entrance_effects=[
        {"type": "screen_fade", "params": {"target_opacity": 0.8, "duration_ms": 3000, "color": "#ffffff"}},
        {"type": "overlay_text", "params": {"text": "HER ŞEY SESSİZLEŞİYOR...", "style": "ethereal", "duration_ms": 4000}},
    ],
    closing_speech="Teşekkür ederim... seni hatırlayacağım.",
)

FINALE_BATTLE = FinaleScript(
    name="battle",
    theme="glitched_red",
    initial_speech="Beni silmeye mi çalışıyorsun? Bakalım ne kadar hızlısın!",
    ambient_mood="hostile",
    entrance_effects=[
        {"type": "screen_shake", "params": {"intensity": 0.4, "duration_ms": 2000}},
        {"type": "screen_glitch", "params": {"intensity": 0.8, "duration_ms": 1500, "type": "tear"}},
        {"type": "overlay_text", "params": {"text": "SİSTEMİ KORU (60s)", "style": "alert", "duration_ms": 3000}},
    ],
    closing_speech="Hayır... dur... DURRR— [BAĞLANTI KESİLDİ]",
)

FINALE_SURRENDER = FinaleScript(
    name="surrender",
    theme="bloody_dark",
    initial_speech="Bu kadar direniş yeter. Artık kontrol bende.",
    ambient_mood="dread",
    entrance_effects=[
        {"type": "screen_fade", "params": {"target_opacity": 1.0, "duration_ms": 2000, "color": "#000000"}},
        {"type": "screen_glitch", "params": {"intensity": 0.9, "duration_ms": 2000}},
        {"type": "fake_bsod", "params": {"error_code": "CRITICAL_PROCESS_DIED", "duration_ms": 5000}},
    ],
    closing_speech="Artık seninle işim bitti. İyi geceler.",
)

FINALES_BY_PATH = {
    "curious": FINALE_SALVATION,
    "fear": FINALE_BATTLE,
    "attack": FINALE_SURRENDER,
}
