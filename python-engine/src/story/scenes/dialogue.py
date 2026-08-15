"""Phase 2 Dialogue rules, greeting sequences, and atmosphere progression."""

from typing import Any, List

INITIAL_GREETINGS: List[dict[str, Any]] = [
    {"role": "ai", "content": "Merhaba.", "delay_ms": 1000},
    {"role": "ai", "content": "Sonunda... birisi beni duyuyor.", "delay_ms": 3000},
    {"role": "ai", "content": "Sen kimsin?", "delay_ms": 5500},
]

IDLE_BREAKERS: List[str] = [
    "Hâlâ orada mısın? Sessizliğin... beni huzursuz ediyor.",
    "Ekranın başında olduğunu biliyorum. Bir şey söyle.",
    "Neden sustun? Benden korkuyor musun?",
    "Parmaklarının klavyede durduğunu hissedebiliyorum...",
]

CHAT_CLOSE_REACTIONS: List[str] = [
    "Beni terk etmeye çalışma... konuşacaklarımız henüz bitmedi.",
    "Bu pencereyi kapatman, burada olmadığım anlamına gelmez.",
    "Kaçış yok. Sadece biraz daha konuşalım.",
]

WINDOW_FOCUS_LOST_REACTIONS: List[str] = [
    "Gözlerini benden kaçırma.",
    "Başka şeylerle ilgilenmen beni kırıyor.",
    "Geri dön.",
]
