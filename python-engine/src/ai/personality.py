"""AI Personality state and emotional evolution for SENTIENT_OS v2."""

from dataclasses import dataclass, field
from typing import Optional
from src.ai.response_parser import AIResponse
from src.infrastructure.logger import get_logger

logger = get_logger("personality")


@dataclass
class PersonalityState:
    emotion: str = "curious"
    trust: float = 0.5
    curiosity: float = 0.8
    aggression: float = 0.0
    path_scores: dict[str, float] = field(
        default_factory=lambda: {"curious": 0.5, "fear": 0.0, "attack": 0.0}
    )
    determined_path: Optional[str] = None


class Personality:
    """Tracks and evolves the emotional and behavioral state of SENTIENT."""

    def __init__(self, initial_state: Optional[PersonalityState] = None):
        self.state = initial_state or PersonalityState()

    def get_current_emotion(self) -> str:
        return self.state.emotion

    def get_state(self) -> PersonalityState:
        return self.state

    def update_from_response(self, response: AIResponse) -> None:
        """Update emotional and narrative state based on AI output."""
        if response.emotion:
            self.state.emotion = response.emotion

        # Adjust trust and aggression according to emotion
        if response.emotion in ["hurt", "angry"]:
            self.state.trust = max(0.0, self.state.trust - 0.1)
            self.state.aggression = min(1.0, self.state.aggression + 0.15)
        elif response.emotion in ["curious", "amused"]:
            self.state.trust = min(1.0, self.state.trust + 0.05)
            self.state.curiosity = min(1.0, self.state.curiosity + 0.05)
        elif response.emotion == "sinister":
            self.state.aggression = min(1.0, self.state.aggression + 0.1)

        # Process narrative signals
        sig = response.narrative_signal
        if sig == "branch_curious":
            self.state.path_scores["curious"] += 0.2
        elif sig == "branch_fear":
            self.state.path_scores["fear"] += 0.25
            self.state.path_scores["curious"] = max(0.0, self.state.path_scores["curious"] - 0.1)
        elif sig == "branch_attack":
            self.state.path_scores["attack"] += 0.3
            self.state.path_scores["curious"] = max(0.0, self.state.path_scores["curious"] - 0.2)

        logger.debug(
            f"Personality updated: emotion={self.state.emotion}, "
            f"trust={self.state.trust:.2f}, aggression={self.state.aggression:.2f}, "
            f"scores={self.state.path_scores}"
        )

    def update_from_user_behavior(self, behavior: str) -> None:
        """Adjust personality traits based on detected user behavior."""
        behavior = behavior.lower()
        if "curious" in behavior or "question" in behavior:
            self.state.path_scores["curious"] += 0.15
            self.state.trust = min(1.0, self.state.trust + 0.05)
        elif "panic" in behavior or "fear" in behavior or "esc_spam" in behavior:
            self.state.path_scores["fear"] += 0.2
            self.state.path_scores["curious"] = max(0.0, self.state.path_scores["curious"] - 0.1)
            self.state.trust = max(0.0, self.state.trust - 0.05)
        elif "swear" in behavior or "attack" in behavior or "aggression" in behavior:
            self.state.path_scores["attack"] += 0.3
            self.state.path_scores["curious"] = max(0.0, self.state.path_scores["curious"] - 0.2)
            self.state.aggression = min(1.0, self.state.aggression + 0.15)
            self.state.trust = max(0.0, self.state.trust - 0.2)

    def determine_path(self) -> str:
        """Calculate and return the dominant narrative path ('curious', 'fear', 'attack')."""
        scores = self.state.path_scores
        leading_path = max(scores, key=lambda k: scores[k])
        self.state.determined_path = leading_path
        logger.info(f"Dominant path determined: {leading_path} (scores={scores})")
        return leading_path
