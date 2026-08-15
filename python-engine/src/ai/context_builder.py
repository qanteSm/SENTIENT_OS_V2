"""Context Builder for assembling dynamic system prompts for Gemini."""

import datetime
from pathlib import Path
from typing import Any, List, Optional
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.ai.response_parser import Episode, Message
from src.infrastructure.logger import get_logger

logger = get_logger("context_builder")


class ContextBuilder:
    """Assembles structured system prompts, context blocks, and conversation history."""

    def __init__(self, prompts_dir: Optional[str | Path] = None):
        if prompts_dir is None:
            self.prompts_dir = Path(__file__).parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        self._base_prompt = self._load_prompt_file("system_base.txt")
        self._phase_prompts = {
            1: self._load_prompt_file("phase_1_first_contact.txt"),
            2: self._load_prompt_file("phase_2_dialogue.txt"),
            3: self._load_prompt_file("phase_3_crisis.txt"),
        }

    def _load_prompt_file(self, filename: str) -> str:
        file_path = self.prompts_dir / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8").strip()
        logger.warning(f"Prompt file not found: {file_path}")
        return ""

    def build_system_prompt(self, phase: int = 1, path: Optional[str] = None) -> str:
        """Assemble base system prompt with phase-specific guidance."""
        parts = [self._base_prompt]
        phase_addon = self._phase_prompts.get(phase, "")
        if phase_addon:
            parts.append(phase_addon)

        if path:
            parts.append(f"\n[SEÇİLEN HİKAYE YOLU: {path.upper()}]")

        return "\n\n".join(parts)

    def build_context_block(
        self,
        personality: Personality,
        profile: dict[str, Any],
        episodes: List[Episode],
        system_info: Optional[dict[str, Any]] = None,
        phase: int = 1,
    ) -> str:
        """Build the dynamic context block containing environmental and psychological details."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "=== GÜNCEL SİSTEM VE HAFIZA BAĞLAMI ===",
            f"Mevcut Zaman: {now_str}",
            f"Mevcut Faz: {phase}",
            f"Duygu Durumu: {personality.get_current_emotion()}",
            f"Güven: {personality.state.trust:.2f} | Agresiflik: {personality.state.aggression:.2f}",
        ]

        # System info (files, window, streamer mode)
        if system_info:
            streamer_mode = system_info.get("streamer_mode", False)
            if not streamer_mode:
                safe_files = system_info.get("safe_files", [])
                if safe_files:
                    sample_files = safe_files[:10]
                    lines.append(f"Masaüstü/Dosya İpuçları (İçeriksiz Sadece İsimler): {', '.join(sample_files)}")

            active_window = system_info.get("active_window")
            if active_window:
                lines.append(f"Kullanıcının Açık Penceresi: {active_window}")

        # Semantic memory (user profile)
        if profile:
            profile_summary = ", ".join([f"{k}={v}" for k, v in profile.items() if k != "known_files"])
            if profile_summary:
                lines.append(f"Kullanıcı Profili (Semantik Hafıza): {profile_summary}")

        # Episodic memory
        if episodes:
            lines.append("Geçmiş Önemli Olaylar (Episodik Hafıza):")
            for ep in episodes[-5:]:  # Last 5 recent episodes
                lines.append(f"- {ep.summary}")

        lines.append("=========================================")
        return "\n".join(lines)

    def format_conversation_history(self, messages: List[Message], max_chars: int = 4000) -> str:
        """Format working memory messages for prompt insertion with length safeguard."""
        if not messages:
            return ""

        formatted_lines = []
        for msg in messages:
            role_label = "Kullanıcı" if msg.role == "user" else "SENTIENT"
            formatted_lines.append(f"{role_label}: {msg.content}")

        history_text = "\n".join(formatted_lines)
        if len(history_text) > max_chars:
            history_text = history_text[-max_chars:]
            # Ensure it starts at a line break
            first_nl = history_text.find("\n")
            if first_nl != -1:
                history_text = history_text[first_nl + 1 :]

        return f"\n=== KONUŞMA GEÇMİŞİ ===\n{history_text}\n========================"
