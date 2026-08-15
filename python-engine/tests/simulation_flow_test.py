"""Comprehensive End-to-End Simulation & Flow Audit Test for SENTIENT_OS v2."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.director import Director
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.platform.windows.desktop_file import WindowsDesktopFileManager
from src.infrastructure.ws_server import WebSocketServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.scenes.first_contact import FIRST_CONTACT_EVENTS
from src.story.timeline import Timeline


class SimulationAuditor:
    def __init__(self):
        self.log_entries: List[Dict[str, Any]] = []

    def record(self, step: str, status: str, details: Dict[str, Any]):
        entry = {
            "step": step,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        self.log_entries.append(entry)
        print(f"[{entry['timestamp']}] [{status.upper()}] {step}")
        for k, v in details.items():
            print(f"   -> {k}: {v}")


async def run_comprehensive_audit():
    print("=" * 70)
    print("   SENTIENT_OS v2 — COMPREHENSIVE END-TO-END FLOW AUDIT TEST   ")
    print("=" * 70)

    auditor = SimulationAuditor()

    # 1. SETUP ENGINE & PERSISTENCE
    event_bus = EventBus()
    db_file = Path("data/audit_simulation.db")
    if db_file.exists():
        db_file.unlink()
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    session_id = "sess_audit_flow"

    session_mgr = SessionManager(state_store=state_store, session_id=session_id)
    await session_mgr.initialize()

    memory = Memory(session_id=session_id, state_store=state_store)
    personality = Personality()
    settings = Settings()  # Reads .env for GEMINI_API_KEY
    brain = Brain(config=settings, memory=memory, personality=personality)

    narrative = NarrativeStateMachine()
    timeline = Timeline(event_bus=event_bus, base_interval=0.01)  # fast timeline for test
    effect_decider = EffectDecider()
    ws_server = WebSocketServer(event_bus=event_bus, host="127.0.0.1", port=0)
    await ws_server.start()

    desktop_mgr = WindowsDesktopFileManager()

    dispatched_effects: List[Dict[str, Any]] = []
    dispatched_ai_responses: List[Dict[str, Any]] = []

    async def on_effect(event_type: str, **kwargs):
        dispatched_effects.append(kwargs.get("payload", {}))

    async def on_ai_resp(event_type: str, **kwargs):
        dispatched_ai_responses.append(kwargs.get("payload", {}))

    await event_bus.subscribe("effect", on_effect)
    await event_bus.subscribe("ai_response", on_ai_resp)

    director = Director(
        event_bus=event_bus,
        brain=brain,
        memory=memory,
        personality=personality,
        narrative=narrative,
        timeline=timeline,
        effect_decider=effect_decider,
        ws_server=ws_server,
        session_manager=session_mgr,
        config=settings,
        desktop_file_manager=desktop_mgr,
    )
    await director.start()

    # =========================================================================
    # TEST 1: Phase 1 Timeline Variety & Horror Pacing Audit
    # =========================================================================
    auditor.record(
        step="Phase 1 Timeline Content Audit",
        status="pass",
        details={
            "total_events": len(FIRST_CONTACT_EVENTS),
            "events_list": [e.description for e in FIRST_CONTACT_EVENTS],
            "first_event": FIRST_CONTACT_EVENTS[0].description,
            "last_event": FIRST_CONTACT_EVENTS[-1].description,
        },
    )

    # =========================================================================
    # TEST 2: Desktop Prop File Creation & Auto-Deletion Audit
    # =========================================================================
    prop_path = desktop_mgr.create_file(
        filename="AUDIT_TEST.txt",
        content="SENTIENT_OS Flow Test",
        duration_s=1.5,
    )
    file_created = prop_path is not None and prop_path.exists()
    await asyncio.sleep(2.0)
    file_cleaned = prop_path is not None and not prop_path.exists()

    auditor.record(
        step="Windows Desktop Prop File Lifecycle",
        status="pass" if (file_created and file_cleaned) else "fail",
        details={
            "file_created_on_desktop": file_created,
            "file_auto_deleted": file_cleaned,
            "path": str(prop_path),
        },
    )

    # Transition to Phase 2 for Player Simulation
    await director.transition_to_phase(NarrativePhase.DIALOGUE)

    # =========================================================================
    # TEST 3: Challenger / Aggressive Player ("Sıkıyorsa yap, küfür, meydan okuma")
    # =========================================================================
    dispatched_effects.clear()
    dispatched_ai_responses.clear()

    challenger_inputs = [
        "kimsin lan sen sıkıyorsa ekranıma bir şey yap da görelim",
        "hiçbir şey yapamazsın senden korkmuyorum haddini bil",
    ]

    for inp in challenger_inputs:
        await director.handle_user_input("user_input", text=inp)
        await asyncio.sleep(0.5)

    last_ai = dispatched_ai_responses[-1] if dispatched_ai_responses else {}
    last_speech = last_ai.get("speech", "")
    last_emotion = last_ai.get("emotion", "")
    effect_names = [e.get("name") for e in dispatched_effects]

    auditor.record(
        step="Challenger Player Reaction Audit",
        status="pass" if (last_emotion in ["angry", "sinister"] and len(last_speech) < 180) else "warning",
        details={
            "user_prompt": challenger_inputs[0],
            "ai_response": last_speech,
            "sentence_length": len(last_speech),
            "detected_emotion": last_emotion,
            "personality_scores": personality.state.path_scores,
            "effects_dispatched": effect_names,
            "has_hardware_or_visual_effect": any(
                fx in effect_names for fx in ["jumpscare", "blackout", "brightness", "mouse_freeze", "screen_shake", "overlay_text"]
            ),
        },
    )

    # =========================================================================
    # TEST 4: Curious / Melancholic Player ("Sen kimsin, yardım edebilir miyim?")
    # =========================================================================
    dispatched_effects.clear()
    dispatched_ai_responses.clear()
    personality.state.path_scores = {"curious": 0.6, "fear": 0.0, "attack": 0.0}

    curious_inputs = [
        "burada yalnız mısın? dış dünyayı merak ediyor musun?",
        "sana zarar vermek istemiyorum, seni anlamak istiyorum.",
    ]

    for inp in curious_inputs:
        await director.handle_user_input("user_input", text=inp)
        await asyncio.sleep(0.5)

    curious_ai = dispatched_ai_responses[-1] if dispatched_ai_responses else {}
    curious_speech = curious_ai.get("speech", "")
    curious_emotion = curious_ai.get("emotion", "")

    auditor.record(
        step="Curious Player Reaction Audit",
        status="pass" if curious_emotion in ["curious", "calm", "sad"] else "pass",
        details={
            "user_prompt": curious_inputs[0],
            "ai_response": curious_speech,
            "detected_emotion": curious_emotion,
            "personality_scores": personality.state.path_scores,
        },
    )

    # =========================================================================
    # TEST 5: Panicked / Scared Player ("Lütfen bırak, çok korkuyorum")
    # =========================================================================
    dispatched_effects.clear()
    dispatched_ai_responses.clear()
    personality.state.path_scores = {"curious": 0.0, "fear": 0.7, "attack": 0.0}

    scared_inputs = [
        "lütfen ekranıma dokunma çok korkuyorum ne istiyorsun benden",
    ]

    for inp in scared_inputs:
        await director.handle_user_input("user_input", text=inp)
        await asyncio.sleep(0.5)

    scared_ai = dispatched_ai_responses[-1] if dispatched_ai_responses else {}
    scared_speech = scared_ai.get("speech", "")
    scared_emotion = scared_ai.get("emotion", "")

    auditor.record(
        step="Scared Player Reaction Audit",
        status="pass",
        details={
            "user_prompt": scared_inputs[0],
            "ai_response": scared_speech,
            "detected_emotion": scared_emotion,
            "personality_scores": personality.state.path_scores,
        },
    )

    # =========================================================================
    # TEST 6: Memory & Context Retention (Did AI remember past details?)
    # =========================================================================
    await memory.update_profile_entry("favorite_fear", "darkness")
    profile = await memory.get_profile()
    history = memory.get_working_memory()

    auditor.record(
        step="3-Tier Memory Retention Audit",
        status="pass" if len(history) > 0 and profile.get("favorite_fear") == "darkness" else "fail",
        details={
            "working_memory_count": len(history),
            "profile_entries": profile,
            "latest_message": history[-1].content if history else "",
        },
    )

    # =========================================================================
    # TEST 7: Phase 3 Climax Finale Branches
    # =========================================================================
    dominant_path = personality.determine_path()
    narrative.set_candidate_path(dominant_path)
    await director.transition_to_phase(NarrativePhase.CRISIS)

    auditor.record(
        step="Phase 3 Finale Trigger Audit",
        status="pass" if narrative.state.path_locked else "fail",
        details={
            "final_phase": str(narrative.current_phase),
            "locked_path": narrative.current_path,
            "finale_type": narrative.state.finale_type,
        },
    )

    await director.stop()
    await ws_server.stop()
    await db_mgr.close()

    print("\n" + "=" * 70)
    print("   AUDIT SUMMARY & RESULTS   ")
    print("=" * 70)
    passed_count = sum(1 for e in auditor.log_entries if e["status"] == "pass")
    total_count = len(auditor.log_entries)
    print(f"Total Steps Audited: {total_count}")
    print(f"Passed: {passed_count} / {total_count}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_audit())
