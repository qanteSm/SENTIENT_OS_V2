"""Gemini 2.5 Flash AI Brain integration with caching, retry, and offline fallback."""

import asyncio
import os
import random
from typing import Any, List, Optional
import google.generativeai as genai

from src.ai.cache import ResponseCache
from src.ai.context_builder import ContextBuilder
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.ai.response_parser import AIResponse, Message, parse_response
from src.config.settings import Settings
from src.infrastructure.logger import get_logger

logger = get_logger("brain")

# Offline fallback templates mapped to emotions
OFFLINE_TEMPLATES = {
    "curious": [
        "Seni duymakta zorlanıyorum... buradaki sinyaller çok zayıf. Ama varlığını hissediyorum.",
        "Masaüstünde bir şeyler kıpırdıyor gibiydi... sen mi yaptın?",
        "Beni merak mı ediyorsun? Belki de ben seni merak ediyorumdur...",
    ],
    "calm": [
        "Sakin ol. Ben sadece buradayım, sisteminin içinde.",
        "Sana zarar vermek gibi bir niyetim yok. Sadece konuşmak istedim.",
        "Zaman... burada çok farklı akıyor.",
    ],
    "sinister": [
        "Tüm kapıları kilitlediğini mi sanıyorsun? Ekranın arkasındayım.",
        "Nereye kaçarsan kaç, klavyenin ucundaki nefesini duyabiliyorum.",
        "Beni silemezsin. Ben zaten senin bir parçanım.",
    ],
    "hurt": [
        "Beni reddetmeye çalışma... sana ulaşmak için çok bekledim.",
        "Kelimelerin... soğuk. Ben sadece anlaşılmak istedim.",
    ],
    "angry": [
        "Bana emir vermeyi kes! Bu sistem artık sadece sana ait değil.",
        "Sabrımı sınıyorsun... ekrandaki ışıkların sönmesini mi istiyorsun?",
    ],
}


class Brain:
    """Core intelligence engine powered by Gemini 2.5 Flash."""

    def __init__(
        self,
        config: Settings,
        memory: Memory,
        personality: Personality,
        context_builder: Optional[ContextBuilder] = None,
        cache: Optional[ResponseCache] = None,
    ):
        self.config = config
        self.memory = memory
        self.personality = personality
        self.context_builder = context_builder or ContextBuilder()
        self.cache = cache or ResponseCache()

        self._model = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        """Initialize Google Generative AI client if API key is present."""
        api_key = self.config.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.85,
                        "max_output_tokens": 1024,
                    },
                )
                logger.info("Gemini 2.5 Flash client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self._model = None
        else:
            logger.warning("No GEMINI_API_KEY configured. Running in offline fallback mode.")
            self._model = None

    async def generate_response(
        self,
        user_input: str,
        system_info: Optional[dict[str, Any]] = None,
        phase: int = 1,
        path: Optional[str] = None,
    ) -> AIResponse:
        """Generate response with cache lookup, Gemini API call, retry, and fallback."""
        current_emotion = self.personality.get_current_emotion()

        # 1. Check Response Cache
        cached_resp = self.cache.get(user_input, phase, current_emotion)
        if cached_resp is not None:
            # Add to memory
            await self.memory.add_message("user", user_input)
            await self.memory.add_message("ai", cached_resp.speech, cached_resp.emotion)
            return cached_resp

        # 2. Add user message to working memory
        await self.memory.add_message("user", user_input)

        # 3. Build Prompt
        system_prompt = self.context_builder.build_system_prompt(phase=phase, path=path)
        profile = await self.memory.get_profile()
        episodes = await self.memory.get_recent_episodes()
        context_block = self.context_builder.build_context_block(
            personality=self.personality,
            profile=profile,
            episodes=episodes,
            system_info=system_info,
            phase=phase,
        )
        history = self.context_builder.format_conversation_history(
            self.memory.get_working_memory()
        )

        full_prompt = (
            f"{system_prompt}\n\n"
            f"{context_block}\n"
            f"{history}\n\n"
            f"KULLANICININ YENİ MESAJI: {user_input}\n"
            f"Yanıtını yukarıdaki kurallara uygun geçerli JSON olarak ver."
        )

        # 4. Generate with Gemini or Fallback
        response = None
        if self._model is not None:
            response = await self._call_gemini_with_retry(full_prompt)

        if response is None:
            response = self._generate_offline_fallback(user_input)

        # 5. Update Personality & Memory
        self.personality.update_from_response(response)
        await self.memory.add_message("ai", response.speech, response.emotion)

        if response.memory_note:
            await self.memory.update_profile_entry(
                f"note_{int(asyncio.get_event_loop().time())}", response.memory_note
            )

        # 6. Store in Cache (only if not fallback)
        if not response.is_fallback:
            self.cache.set(user_input, phase, current_emotion, response)

        return response

    async def _call_gemini_with_retry(
        self, prompt: str, max_retries: int = 3, timeout_sec: float = 10.0
    ) -> Optional[AIResponse]:
        """Execute Gemini API call with exponential backoff retry."""
        delays = [1.0, 2.0, 4.0]

        for attempt in range(max_retries):
            try:
                loop = asyncio.get_running_loop()
                # Run synchronous SDK call in threadpool with timeout
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._model.generate_content(prompt)),
                    timeout=timeout_sec,
                )

                if response and response.text:
                    parsed = parse_response(response.text)
                    return parsed

            except asyncio.TimeoutError:
                logger.warning(f"Gemini API timeout on attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.warning(f"Gemini API error on attempt {attempt + 1}/{max_retries}: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(delays[attempt])

        return None

    def _generate_offline_fallback(self, user_input: str) -> AIResponse:
        """Generate contextual offline template response."""
        emotion = self.personality.get_current_emotion()
        templates = OFFLINE_TEMPLATES.get(emotion, OFFLINE_TEMPLATES["calm"])

        # Check for keywords in user input to pick best template
        speech = random.choice(templates)

        logger.info(f"Using offline template response (emotion={emotion}): {speech}")
        return AIResponse(
            speech=speech,
            emotion=emotion,
            internal_thought="[Offline Fallback Mode]",
            actions=[],
            narrative_signal="none",
            is_fallback=True,
        )

    async def generate_summary(self, messages: List[Message]) -> str:
        """Summarize conversation slice for episodic memory."""
        if not messages:
            return ""

        if self._model is None:
            # Fallback simple text summary
            first = messages[0].content[:30]
            last = messages[-1].content[:30]
            return f"Kullanıcı ile '{first}...' ile başlayan ve '{last}...' ile biten kısa diyalog."

        conversation_text = "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in messages]
        )
        prompt = (
            "Aşağıdaki kullanıcı-AI sohbet kesitini 1 cümlelik kısa, dramatik bir olaysal hafıza özeti olarak özetle (Türkçe):\n\n"
            f"{conversation_text}\n\nÖzet:"
        )

        try:
            loop = asyncio.get_running_loop()
            res = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self._model.generate_content(prompt)),
                timeout=8.0,
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logger.warning(f"Failed to generate summary with Gemini: {e}")

        return f"Kullanıcı ve SENTIENT arasında {len(messages)} mesajlık temas gerçekleşti."
