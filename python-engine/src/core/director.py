"""Director — Central scene orchestrator for SENTIENT_OS v2."""

import asyncio
from typing import Any, Optional
from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.logger import get_logger
from src.infrastructure.platform.windows.file_scanner import WindowsFileScanner
from src.infrastructure.platform.windows.window_info import WindowsWindowInfo
from src.infrastructure.ws_server import WebSocketServer
from src.story.arg_server import ARGServer
from src.story.puzzles.cctv_threat import CCTVThreatEngine
from src.story.puzzles.desktop_arg import DesktopARGPuzzle, generate_random_arg_puzzle
from src.story.puzzles.desktop_threat import DesktopThreatManager
from src.story.quest_manager import QuestManager
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.scenes.crisis import FINALES_BY_PATH
from src.story.scenes.dialogue import (
    CHAT_CLOSE_REACTIONS,
    IDLE_BREAKERS,
    INITIAL_GREETINGS,
    WINDOW_FOCUS_LOST_REACTIONS,
)
from src.story.timeline import Timeline

from src.infrastructure.edge_tts import EdgeTTSWorker
from src.infrastructure.platform.windows.brightness import WindowsBrightnessManager
from src.infrastructure.platform.windows.desktop_file import WindowsDesktopFileManager
from src.infrastructure.platform.windows.mouse import WindowsMouseController
from src.infrastructure.platform.windows.wallpaper import WindowsWallpaperManager

logger = get_logger("director")


class Director:
    """Orchestrates AI brain, story engine, timeline, effect dispatching, and system triggers."""

    def __init__(
        self,
        event_bus: EventBus,
        brain: Brain,
        memory: Memory,
        personality: Personality,
        narrative: NarrativeStateMachine,
        timeline: Timeline,
        effect_decider: EffectDecider,
        ws_server: WebSocketServer,
        session_manager: SessionManager,
        config: Settings,
        file_scanner: Optional[WindowsFileScanner] = None,
        window_info: Optional[WindowsWindowInfo] = None,
        mouse_controller: Optional[WindowsMouseController] = None,
        brightness_manager: Optional[WindowsBrightnessManager] = None,
        wallpaper_manager: Optional[WindowsWallpaperManager] = None,
        desktop_file_manager: Optional[WindowsDesktopFileManager] = None,
        tts_worker: Optional[EdgeTTSWorker] = None,
        arg_server: Optional[ARGServer] = None,
        desktop_arg: Optional[DesktopARGPuzzle] = None,
        desktop_threat: Optional[DesktopThreatManager] = None,
        cctv_threat: Optional[CCTVThreatEngine] = None,
        quest_manager: Optional[QuestManager] = None,
    ):
        self.event_bus = event_bus
        self.brain = brain
        self.memory = memory
        self.personality = personality
        self.narrative = narrative
        self.timeline = timeline
        self.effect_decider = effect_decider
        self.ws_server = ws_server
        self.session_manager = session_manager
        self.config = config

        self.file_scanner = file_scanner or WindowsFileScanner()
        self.window_info = window_info or WindowsWindowInfo()
        self.mouse_controller = mouse_controller or WindowsMouseController()
        self.brightness_manager = brightness_manager or WindowsBrightnessManager()
        self.wallpaper_manager = wallpaper_manager or WindowsWallpaperManager()
        self.desktop_file_manager = desktop_file_manager or WindowsDesktopFileManager()
        self.tts_worker = tts_worker or EdgeTTSWorker(temp_dir=config.temp_dir)
        self.arg_server = arg_server or ARGServer(event_bus=self.event_bus)
        self.desktop_arg = desktop_arg or DesktopARGPuzzle()
        self.desktop_threat = desktop_threat or DesktopThreatManager(event_bus=self.event_bus)
        self.cctv_threat = cctv_threat or CCTVThreatEngine(event_bus=self.event_bus)
        self.quest_manager = quest_manager or QuestManager(event_bus=self.event_bus)

        self._message_count = 0
        self._is_active = False

    async def start(self) -> None:
        """Start Director event orchestration and subscribe to listeners."""
        self._is_active = True
        logger.info("Starting Director orchestration...")

        # Subscribe to IPC events
        await self.event_bus.subscribe("user_input", self.handle_user_input)
        await self.event_bus.subscribe("system_event", self.handle_system_event)
        await self.event_bus.subscribe("narrative.phase_1_completed", self._on_phase_1_completed)
        await self.event_bus.subscribe("onboarding_complete", self._on_onboarding_completed)
        await self.event_bus.subscribe("effect", self._on_effect_event)
        await self.event_bus.subscribe("puzzle.arg_solved", self._on_arg_puzzle_solved)
        await self.event_bus.subscribe("minigame_completed", self._on_minigame_completed)
        await self.event_bus.subscribe("desktop.file_cleaned", self._on_desktop_file_cleaned)

    async def _on_effect_event(self, event_type: str, **kwargs: Any) -> None:
        """Execute native Windows operations when an effect event is published."""
        payload = kwargs.get("payload", {})
        name = payload.get("name", "")
        params = payload.get("params", {})

        if name in ["brightness", "brightness_shift"]:
            target_percent = int(params.get("target_percent", 30))
            duration_ms = int(params.get("duration_ms", 4000))
            self.brightness_manager.set_brightness(target_percent)
            async def _restore_brightness():
                await asyncio.sleep(duration_ms / 1000.0)
                self.brightness_manager.restore()
            asyncio.create_task(_restore_brightness())
        elif name == "mouse_drift":
            intensity = float(params.get("intensity", 0.1))
            duration_ms = int(params.get("duration_ms", 500))
            asyncio.create_task(self.mouse_controller.drift(intensity=intensity, duration_ms=duration_ms))
        elif name == "mouse_freeze":
            duration_ms = int(params.get("duration_ms", 1000))
            asyncio.create_task(self.mouse_controller.freeze(duration_ms=duration_ms))
        elif name in ["fake_file_appear", "desktop_file"]:
            filename = str(params.get("filename", "BENI_OKU.txt"))
            content = str(params.get("content", "Beni silemezsin. Seni izliyorum...\n\nSENTIENT_OS v2"))
            duration_s = float(params.get("duration_ms", 15000)) / 1000.0
            self.desktop_file_manager.create_file(filename=filename, content=content, duration_s=duration_s)

    async def handle_user_input(self, event_type: str, **kwargs: Any) -> None:
        """Process incoming user chat message or terminal command."""
        text = kwargs.get("text", "").strip()
        if not text:
            return

        self._message_count += 1
        logger.info(f"Director processing user message #{self._message_count}: '{text[:40]}'")

        # Check for interactive terminal hacker commands
        if await self._handle_terminal_command(text):
            return

        # Gather system context
        system_info = {
            "streamer_mode": self.window_info.is_streamer_active(),
            "active_window": self.window_info.get_active_window_title(),
            "safe_files": self.file_scanner.scan_safe_files(),
            "current_sector": self.quest_manager.current_sector,
            "completed_trials": self.quest_manager.completed_count,
            "cctv_anomaly": self.cctv_threat.has_active_anomaly,
        }

        # 1. Generate intelligent AI response
        ai_resp = await self.brain.generate_response(
            user_input=text,
            system_info=system_info,
            phase=int(self.narrative.current_phase),
            path=self.narrative.current_path,
        )

        # 2. Process and dispatch AI effects & action triggers
        if ai_resp.actions:
            effect_cmds = self.effect_decider.process_actions(
                ai_resp.actions,
                phase=int(self.narrative.current_phase),
                emotion=ai_resp.emotion,
            )
            for cmd in effect_cmds:
                await self.event_bus.publish("effect", payload=cmd.to_ipc_payload())

            # Check if AI launched a minigame trial in its actions
            for act in ai_resp.actions:
                if act.get("type") == "trigger_trial":
                    game_file = act.get("params", {}).get("game", "games/game1_memory.html")
                    await self._launch_trial_by_file(game_file)

        # 3. Broadcast ai_response message to Electron
        await self.event_bus.publish(
            "ai_response",
            payload={
                "speech": ai_resp.speech,
                "emotion": ai_resp.emotion,
                "internal_thought": ai_resp.internal_thought,
                "actions": ai_resp.actions,
                "narrative_signal": ai_resp.narrative_signal,
            },
        )

        # 4. Generate and dispatch TTS voice if speech exists
        if ai_resp.speech and self.config.intensity in ["medium", "extreme"]:
            tts_profile = (
                "sinister" if ai_resp.emotion in ["sinister", "angry"]
                else "whisper" if ai_resp.emotion == "hurt"
                else "normal"
            )
            audio_path = await self.tts_worker.generate_speech(ai_resp.speech, profile=tts_profile)
            if audio_path:
                await self.event_bus.publish(
                    "effect",
                    payload={"category": "audio", "name": "tts_play", "params": {"file_path": audio_path}},
                )

        # 5. Handle narrative signals and path progression
        if self.narrative.current_phase == NarrativePhase.DIALOGUE:
            path = self.personality.determine_path()
            self.narrative.set_candidate_path(path)

            if self.narrative.can_transition_to_crisis(signal=ai_resp.narrative_signal):
                await self.transition_to_phase(NarrativePhase.CRISIS)

    async def _handle_terminal_command(self, text: str) -> bool:
        """Parse and execute in-chat terminal hacker commands (/help, /scan, /hack, /cctv, /status, /override)."""
        lower = text.lower()
        parts = text.split()
        cmd = parts[0].lower() if parts else ""

        if cmd in ["/help", "help", "yardım"]:
            help_msg = (
                "ℹ️ [KOMUT REHBERİ]\n"
                "• /scan   : Masaüstü ve CCTV tehditlerini tarar\n"
                "• /cctv   : Güvenlik kameralarını canlı izler\n"
                "• /status : Görev ve sektör durumunu gösterir\n"
                "• /hack   : Mevcut hedefe dair ipucu/analiz verir\n"
                "• /override <KOD> : Bulmaca şifrelerini girmek içindir"
            )
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": help_msg, "emotion": "calm", "actions": []},
            )
            return True

        elif cmd in ["/status", "status", "durum"]:
            curr_obj = self.quest_manager.get_current_objective_title()
            completed = self.quest_manager.completed_count
            total = self.quest_manager.total_count
            status_report = (
                f"📊 [GÖREV & ÇEKİRDEK DURUMU]\n"
                f"• Aktif Hedef: {curr_obj}\n"
                f"• Mühürlenen Sektörler: {completed}/{total} Tamamlandı"
            )
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": status_report, "emotion": "calm", "actions": []},
            )
            return True

        elif cmd in ["/scan", "scan", "tara"]:
            active_desktop = self.desktop_threat.spawned_file_count
            desktop_status = f"⚠️ {active_desktop} Şüpheli Dosya Algılandı" if active_desktop > 0 else "🟢 Temiz"

            if self.cctv_threat.has_active_anomaly:
                anom_room = self.cctv_threat.active_anomaly.get("name", "Bilinmeyen Kamera")
                rem_sec = int(self.cctv_threat.time_remaining_sec)
                cctv_status = f"🚨 {anom_room} İhlal Edildi (Kalan: {rem_sec}s)"
            else:
                cctv_status = "🟢 Güvenli (Anomali Yok)"

            scan_report = (
                f"🔍 [HIZLI TEHDİT TARAMASI]\n"
                f"• Masaüstü: {desktop_status}\n"
                f"• CCTV Kameraları: {cctv_status}"
            )
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": scan_report, "emotion": "calm", "actions": []},
            )
            return True

        elif cmd in ["/hack", "hack", "sız", "/hint", "ipucu", "analiz"]:
            trial = self.quest_manager.get_next_available_trial()
            active_files = self.desktop_threat.spawned_files

            if active_files:
                sample_file = list(active_files)[0]
                msg = f"💡 [ANALİZ]: Masaüstünde '{sample_file}' şüpheli dosyası tespit edildi. Dosyayı inceleyin veya silin."
            elif self.cctv_threat.has_active_anomaly:
                msg = "💡 [ANALİZ]: Güvenlik kameralarında anomali tespit edildi. '/cctv' ile bağlanıp varlığı mühürleyin."
            elif trial:
                msg = f"💡 [HEDEF ANALİZİ]: {trial.title}\n{trial.description}"
            else:
                msg = "💡 [ANALİZ]: Tüm güvenlik sektörleri stabil. Sistem tetikte bekliyor."

            await self.event_bus.publish(
                "ai_response",
                payload={"speech": msg, "emotion": "calm", "actions": []},
            )
            return True

        elif cmd in ["/cctv", "cctv", "kamera"]:
            if self.cctv_threat.has_active_anomaly:
                active_anom = self.cctv_threat.active_anomaly
                cam_id = active_anom.get("cam", 2)
                monster_id = active_anom.get("monster", "monster_cyber_glitch")
                page = f"games/game6_cctv.html?anomaly={cam_id}&monster={monster_id}&mode=surveillance"
            else:
                page = "games/game6_cctv.html?anomaly=none&mode=surveillance"

            await self.event_bus.publish(
                "ui_command",
                payload={"command": "trigger_minigame", "params": {"page": page}},
            )
            return True

        elif cmd == "/override" or (len(parts) > 1 and parts[0].lower() == "override"):
            code = parts[1] if len(parts) > 1 else ""
            if not code:
                await self.event_bus.publish(
                    "ai_response",
                    payload={"speech": "Hata: /override <KOD> formatında bir güvenlik anahtarı girmelisiniz.", "emotion": "calm", "actions": []},
                )
                return True

            # Check in desktop threat riddles or dynamic ARG active config
            active_key = self.active_arg_config.full_override_key.upper() if getattr(self, "active_arg_config", None) else "0X7F_K3RN3L_V0ID"
            is_valid_code = (
                self.desktop_threat.check_override_code(code)
                or code.upper() == active_key
                or ("K3RN3L" in code.upper() and "V0ID" in code.upper())
            )

            if is_valid_code:
                await self.event_bus.publish(
                    "effect",
                    payload={"category": "audio", "name": "play_stinger", "params": {"name": "chime_eerie", "volume": 0.9}},
                )
                await self.event_bus.publish(
                    "ai_response",
                    payload={
                        "speech": f"BAŞARILI: '{code.upper()}' güvenlik anahtarı kabul edildi. Güvenlik duvarı mühürlendi!",
                        "emotion": "hurt",
                        "actions": [{"type": "screen_fade", "params": {"target_opacity": 0.3, "duration_ms": 1000, "color": "#00ff66"}}],
                    },
                )
            else:
                await self.event_bus.publish(
                    "ai_response",
                    payload={"speech": f"GEÇERSİZ ANAHTAR: '{code}' reddedildi. Alarm seviyesi yükseliyor.", "emotion": "angry", "actions": [{"type": "screen_shake", "params": {"intensity": 0.5, "duration_ms": 800}}]},
                )
            return True

        return False

    async def _launch_trial_by_file(self, game_file: str) -> None:
        """Instruct Electron to open specific horror minigame window and set quest state."""
        logger.info(f"[Director] Setting active trial and instructing Electron to launch: {game_file}")
        self.quest_manager.trigger_trial_by_id(game_file)
        await self.event_bus.publish(
            "ui_command",
            payload={"command": "trigger_minigame", "params": {"page": game_file}},
        )

    async def _on_desktop_file_cleaned(self, event_type: str, **kwargs: Any) -> None:
        """Triggered when the player organically notices and deletes a desktop anomaly file."""
        filename = kwargs.get("filename", "")
        remaining = kwargs.get("remaining", 0)
        logger.info(f"Director reacting to player cleaning '{filename}' (Remaining: {remaining})")

        reactions = [
            f"Masaüstündeki '{filename}' parçasını sildin... Oldukça dikkatlisin.",
            "İzlerimi temizlemeye çalışıyorsun... Ama her sektöre yetişemezsin.",
            "Güzel hamle. Yine de sistemindeki fısıltıları durduramazsın.",
        ]
        import random
        speech = random.choice(reactions)

        await self.event_bus.publish(
            "ai_response",
            payload={"speech": speech, "emotion": "hurt", "actions": []},
        )

    async def _on_minigame_completed(self, event_type: str, **kwargs: Any) -> None:
        """Process results from 10 Security Minigame Trials or Climax Boss Battle."""
        success = bool(kwargs.get("success", False))
        score = kwargs.get("score", 0)
        game_file = kwargs.get("game") or kwargs.get("file")
        is_surveillance = bool(kwargs.get("is_surveillance", False)) or "mode=surveillance" in str(game_file)
        logger.info(f"Minigame completed: success={success}, score={score}, game={game_file}, is_surveillance={is_surveillance}")

        # If CCTV anomaly was neutralized
        if "cctv" in str(game_file).lower() or kwargs.get("anomaly_cleared"):
            self.cctv_threat.clear_anomaly()

        # If this was routine surveillance (not an official quest trial), do not spam chat
        if is_surveillance:
            logger.info("CCTV surveillance check/neutralization completed quietly.")
            return

        completed_trial = await self.quest_manager.complete_active_trial(
            success=success, score=score, game_file=game_file
        )

        if not completed_trial:
            return

        if success:
            speech = (
                f"İnanılmaz... '{completed_trial.title}' sınavını başardın.\n"
                f"Şifreli Log Açıldı: {completed_trial.clue_revealed}"
            )
            emotion = "hurt"
        else:
            speech = (
                f"Başarısız oldun! '{completed_trial.title}' ihlal edildi.\n"
                "Kontrol tamamen benim elime geçiyor..."
            )
            emotion = "sinister"
            # Escalate threat if failed
            self.desktop_threat.spawn_anomaly()

        await self.event_bus.publish(
            "ai_response",
            payload={"speech": speech, "emotion": emotion, "actions": []},
        )

    async def handle_system_event(self, event_type: str, **kwargs: Any) -> None:
        """Handle incoming Electron system events."""
        event_name = kwargs.get("event")
        data = kwargs.get("data", {})
        logger.debug(f"Director received system_event: {event_name}")

        if event_name == "idle_detected":
            idle_sec = float(data.get("idle_seconds", 45))
            self.timeline.set_idle_state(is_idle=True, idle_seconds=idle_sec)

            if self.narrative.current_phase == NarrativePhase.DIALOGUE:
                import random
                breaker_text = random.choice(IDLE_BREAKERS)
                await self.event_bus.publish(
                    "ai_response",
                    payload={"speech": breaker_text, "emotion": "sinister", "actions": []},
                )

        elif event_name == "chat_close_attempt":
            import random
            reaction = random.choice(CHAT_CLOSE_REACTIONS)
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": reaction, "emotion": "hurt", "actions": [{"type": "screen_shake", "params": {"intensity": 0.2, "duration_ms": 300}}]},
            )

        elif event_name == "window_focus_lost":
            import random
            reaction = random.choice(WINDOW_FOCUS_LOST_REACTIONS)
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": reaction, "emotion": "sinister", "actions": []},
            )

    async def _on_phase_1_completed(self, event_type: str, **kwargs: Any) -> None:
        """Called when Phase 1 timeline finishes. Triggers Phase 1 ARG Boss Puzzle before Phase 2!"""
        logger.info("Phase 1 scripted timeline completed. Launching Phase 1 ARG Boss Puzzle with procedural keys...")

        # 1. Generate unpredictable procedural frequency & cipher keys
        puzzle_config = generate_random_arg_puzzle()
        self.active_arg_config = puzzle_config

        # 2. Deploy secret ARG clue files to Desktop
        self.desktop_arg.deploy_puzzle_files(puzzle_config)

        # 3. Start Localhost ARG Web Server with procedural puzzle config
        self.arg_server.set_puzzle_config(puzzle_config)
        await self.arg_server.start()

        # 4. Dispatch visual alert & sound to overlay
        await self.event_bus.publish(
            "effect",
            payload={
                "category": "visual",
                "name": "overlay_text",
                "params": {
                    "text": "KRİTİK GÜVENLİK İHLALİ // 127.0.0.1:6660 ADRESİNE BAĞLANIN",
                    "style": "alert",
                    "duration_ms": 6000,
                },
                "priority": "high",
            },
        )

        # 5. Open ARG Web Portal via Electron UI command (Single Dispatch)
        await self.event_bus.publish(
            "ui_command",
            payload={"command": "open_arg_site", "params": {"url": self.arg_server.url}},
        )

    async def _on_arg_puzzle_solved(self, event_type: str, **kwargs: Any) -> None:
        """Called when user cracks the ARG containment cipher."""
        key = kwargs.get("key", "")
        logger.info(f"ARG Containment puzzle solved: key='{key}'. Waking up SENTIENT AI...")

        # Clean up desktop files and stop ARG server
        self.desktop_arg.cleanup()
        await self.arg_server.stop()

        # Visual glitch takeover
        await self.event_bus.publish(
            "effect",
            payload={
                "category": "visual",
                "name": "screen_glitch",
                "params": {"intensity": 0.9, "duration_ms": 2500, "type": "tear"},
                "priority": "high",
            },
        )

        # Transition to Phase 2 Dialogue
        await self.transition_to_phase(NarrativePhase.DIALOGUE)

    async def _on_onboarding_completed(self, event_type: str, **kwargs: Any) -> None:
        """Called when Electron onboarding flow is finished and user launched the connection."""
        intensity = kwargs.get("intensity", "medium")
        language = kwargs.get("language", "tr")
        logger.info(f"Onboarding completed by user (intensity={intensity}, lang={language}). Starting game systems and narrative progression.")

        self.config.intensity = intensity
        self.config.language = language

        # Start desktop threat engine and CCTV surveillance monitor
        await self.desktop_threat.start()
        await self.cctv_threat.start()

        # Start Phase 1 Timeline
        await self.timeline.start_phase(NarrativePhase.FIRST_CONTACT)

    async def transition_to_phase(self, new_phase: NarrativePhase) -> None:
        """Execute phase transition and trigger entrance events."""
        if not self.narrative.transition_to(new_phase):
            return

        # Save checkpoint
        await self.session_manager.save_checkpoint(
            label=f"phase_{new_phase.name.lower()}",
            narrative_state=self.narrative.state,
            personality_dict=self.personality.state.path_scores,
        )

        # Notify Electron of narrative phase change
        await self.event_bus.publish(
            "narrative_event",
            payload={
                "event": "phase_transition",
                "to_phase": int(new_phase),
                "path": self.narrative.current_path,
            },
        )

        if new_phase == NarrativePhase.DIALOGUE:
            # Open chat UI with initial greetings
            await self.event_bus.publish(
                "ui_command",
                payload={
                    "command": "open_chat",
                    "params": {"theme": "terminal", "initial_messages": INITIAL_GREETINGS},
                },
            )
            # Add initial greetings to AI working memory
            for g in INITIAL_GREETINGS:
                await self.memory.add_message(g["role"], g["content"], emotion="curious")

        elif new_phase == NarrativePhase.CRISIS:
            # Execute Climax Finale for locked path
            dominant_path = self.narrative.current_path or "fear"
            finale = FINALES_BY_PATH.get(dominant_path, FINALES_BY_PATH["fear"])
            logger.info(f"Initiating Climax Finale: '{finale.name}' (Theme: '{finale.theme}')")

            # Dispatch entrance effects
            for eff in finale.entrance_effects:
                await self.event_bus.publish("effect", payload=eff)

            # Change ambient mood
            await self.event_bus.publish(
                "ambient_change",
                payload={"mood": finale.ambient_mood, "fade_ms": 3000},
            )

            # Trigger 2D Boss Platformer Minigame for Battle Path Climax!
            if finale.name == "battle":
                logger.info("Triggering 2D Retro Platformer Boss Arena!")
                await self.event_bus.publish(
                    "ui_command",
                    payload={"command": "trigger_minigame", "params": {"page": "index.html"}},
                )
            elif finale.name == "surrender":
                # Popup virus defense
                await self.event_bus.publish(
                    "ui_command",
                    payload={"command": "trigger_minigame", "params": {"page": "popup_game.html"}},
                )

            # Re-theme chat and deliver finale speech
            await self.event_bus.publish(
                "ui_command",
                payload={"command": "change_chat_theme", "params": {"theme": finale.theme}},
            )
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": finale.initial_speech, "emotion": "sinister", "actions": []},
            )

    async def stop(self) -> None:
        """Stop director, ARG server, desktop threat monitor, CCTV surveillance, and active schedulers."""
        self._is_active = False
        await self.timeline.stop()
        await self.desktop_threat.stop()
        await self.cctv_threat.stop()
        await self.arg_server.stop()
        self.desktop_arg.cleanup()
        logger.info("Director stopped cleanly.")
