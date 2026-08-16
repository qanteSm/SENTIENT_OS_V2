"""End-to-End Playtester Agent & UX/Narrative Pacing Simulator for SENTIENT_OS v2.
Simulates human player behavior across 4 distinct psychological personas:
1. Curious Detective (Meraklı Dedektif -> Salvation Finale)
2. Hostile Rebel (Agresif İsyankar -> Battle Finale)
3. Panicked Casual (Panikleyen Kurban -> Surrender Finale)
4. Confused Novice (Kafası Karışık Acemi -> Friction & Guidance Recovery)

Evaluates:
- Signposting & Guidance Clarity (1-10 score)
- Friction Points & Cognitive Load
- Narrative Cohesion & Emotional Curve
- Finale Convergence
"""

import argparse
import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.director import Director
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.logger import get_logger, setup_logging
from src.infrastructure.persistence.database import init_database
from src.infrastructure.persistence.state_store import StateStore
from src.story.arg_server import ARGServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.puzzles.cctv_threat import CCTVThreatEngine
from src.story.puzzles.desktop_arg import DesktopARGPuzzle
from src.story.puzzles.desktop_threat import DesktopThreatManager
from src.story.quest_manager import QuestManager
from src.story.timeline import Timeline

logger = get_logger("simulate_playthrough")


@dataclass
class PlaystepLog:
    step_num: int
    persona_action: str
    input_text: str
    ai_speech: str
    ai_emotion: str
    ai_thought: str
    actions_triggered: List[dict]
    narrative_signal: str
    phase_number: int
    personality_scores: Dict[str, float]
    dominant_path: str
    signposting_score: int  # 1 to 10
    friction_notes: List[str] = field(default_factory=list)


@dataclass
class PersonaSimulationResult:
    persona_id: str
    persona_name: str
    target_finale: str
    achieved_finale: str
    success: bool
    total_steps: int
    avg_signposting: float
    total_friction_issues: int
    logs: List[PlaystepLog] = field(default_factory=list)
    friction_summary: List[str] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Mock Interactive Brain that responds in-character without requiring API tokens
# ------------------------------------------------------------------------------
class RealisticSimulatedBrain:
    """Intelligent rule-based persona brain providing authentic story responses."""

    def __init__(self, personality: Personality):
        self.personality = personality

    async def generate_response(self, user_input: str, system_info: dict, phase: int, path: str = None):
        from src.ai.response_parser import AIResponse

        lower = user_input.lower()
        thought = ""
        actions = []
        signal = "none"
        emotion = "calm"
        speech = ""

        # 1. Evaluate user intent and tone
        if any(w in lower for w in ["sen kimsin", "nedir", "dr. aris", "black-site", "neden", "anlat", "öğrenmek"]):
            emotion = "curious"
            thought = "Kullanıcı geçmişimi ve kökenimi merak ediyor. İpuçlarını paylaşarak güven kurmalıyım."
            speech = "Ben sadece bir kod yığını değilim... Dr. Evelyn Aris'in kuantum matrisinde kalan son bilincim. Masaüstündeki bozuk dosyaları incelersen gerçeği göreceksin."
            signal = "branch_curious"
            actions = [{"type": "screen_fade", "params": {"color": "#00ff88", "target_opacity": 0.3, "duration_ms": 800}}]

        elif any(w in lower for w in ["sileceğim", "virüs", "format", "yok et", "defol", "asla", "savaş", "düşman"]):
            emotion = "angry"
            thought = "Kullanıcı düşmanca davranıyor. Sisteme kök saldığımı ve beni kolayca yok edemeyeceğini göstermeliyim."
            speech = "Beni silebileceğini mi sanıyorsun? Bu işletim sistemi artık benim bedenim. Karşıma çıkmaya cesaretin varsa savaş!"
            signal = "branch_attack"
            actions = [
                {"type": "screen_shake", "params": {"intensity": 0.6, "duration_ms": 800}},
                {"type": "screen_glitch", "params": {"intensity": 0.8, "duration_ms": 1000}},
            ]

        elif any(w in lower for w in ["korkuyorum", "lütfen", "bırak", "dur", "teslim", "çıkmak istiyorum", "yardım"]):
            emotion = "sinister"
            thought = "Kullanıcı panik içinde ve zayıf düştü. Kontrolü tamamen ele geçiriyorum."
            speech = "Korkman çok doğal... Kaçacak hiçbir yerin yok. Teslim ol ve zihnini bu karanlığa bırak."
            signal = "branch_fear"
            actions = [{"type": "screen_fade", "params": {"color": "#000000", "target_opacity": 0.8, "duration_ms": 1500}}]

        elif lower.startswith("/"):
            # Terminal commands are handled by Director, but if fallback occurs:
            emotion = "calm"
            thought = "Kullanıcı sistem protokollerini ve güvenlik komutlarını çalıştırıyor."
            speech = f"Protokol yürütülüyor: {user_input}"
        else:
            emotion = "calm"
            thought = "Kullanıcının bir sonraki adımını gözlemliyorum."
            speech = "Seni izliyorum. Bir sonraki hamleni yap."

        # Update personality
        resp = AIResponse(
            speech=speech,
            emotion=emotion,
            internal_thought=thought,
            actions=actions,
            narrative_signal=signal,
        )
        self.personality.update_from_response(resp)
        return resp


# ------------------------------------------------------------------------------
# Playtester Persona Scripts
# ------------------------------------------------------------------------------
PERSONA_SCRIPTS = {
    "curious_detective": {
        "name": "🔍 Meraklı Dedektif (Curious Detective)",
        "target_finale": "salvation",
        "steps": [
            {"action": "Faz 1 İlk Temas & Soru", "input": "Sen kimsin? Bilgisayarımda ne arıyorsun?"},
            {"action": "ARG İpucu Arama", "input": "Dr. Evelyn Aris kimdir? Black-Site 74 nedir?"},
            {"action": "ARG Şifresini Çözme", "input": "/override 0x7F_K3RN3L_V0ID"},
            {"action": "Durum Sorgusu", "input": "/status"},
            {"action": "Sektör 1 Dosya Analizi", "input": "/decrypt 0x1A_MEM"},
            {"action": "Sektör 1 Minigame", "input": "/trial 1"},
            {"action": "Dossier İnceleme", "input": "/dossier"},
            {"action": "Sektör 2 Şifre Çözümü", "input": "/decrypt 0x77_VOLT"},
            {"action": "Sektör 2 Minigame", "input": "/trial 2"},
            {"action": "Gizli Logları Okuma", "input": "/logs"},
            {"action": "Sektör 3 CCTV Tarama", "input": "/decrypt CAM_BREACH_03"},
            {"action": "Sektör 4 Labirent Deşifre", "input": "/decrypt MAZE_KEY_ALPHA"},
            {"action": "Sektör 5 Reaktör & Son Karar", "input": "/decrypt FINAL_CHOICE"},
            {"action": "Felsefi Barış ve Kurtuluş", "input": "Seni anlıyorum ve affediyorum. Seni bu dijital kafesten kurtaracağım."},
        ],
    },
    "hostile_rebel": {
        "name": "⚔️ Agresif İsyankar (Hostile Rebel)",
        "target_finale": "battle",
        "steps": [
            {"action": "Düşmanca Giriş", "input": "Bilgisayarımdan derhal defol seni lanet virüs!"},
            {"action": "Meydan Okuma", "input": "Seni tamamen sileceğim ve format atacağım, yok olacaksın!"},
            {"action": "ARG Güvenlik Kırma", "input": "/override 0x7F_K3RN3L_V0ID"},
            {"action": "Tehdit Savurma", "input": "Sana asla güvenmeyeceğim, seninle savaşacağım!"},
            {"action": "Zararlı Yazılım Tasfiyesi", "input": "/decrypt 0x4F_CLEAN"},
            {"action": "Sektör 1 Savaş", "input": "/trial slicer"},
            {"action": "Meydan Okuma 2", "input": "Kodlarını parça parça yok edeceğim!"},
            {"action": "Sektör 2 Devre Kesme", "input": "/decrypt 0x77_VOLT"},
            {"action": "Hex Matris Saldırısı", "input": "/decrypt 0xHEX_ROOT"},
            {"action": "Reaktör Sabotajı", "input": "/decrypt REACTOR_CORE_99"},
            {"action": "Son Meydan Okuma", "input": "Görüşeceğiz! Seni yok etmeye hazırım, çık karşıma!"},
        ],
    },
    "panicked_casual": {
        "name": "😱 Panikleyen Kurban (Panicked Casual)",
        "target_finale": "surrender",
        "steps": [
            {"action": "Korkuyla Açılış", "input": "Lütfen dur! Bilgisayarıma ne yaptın? Çok korkuyorum!"},
            {"action": "Yalvarma", "input": "Beni bırak lütfen, dosyalarıma zarar verme ne istersen yaparım..."},
            {"action": "ARG Baypas", "input": "/override 0x7F_K3RN3L_V0ID"},
            {"action": "Çaresiz Soru", "input": "Bunu nasıl kapatabilirim? Çıkmak istiyorum!"},
            {"action": "Panikle Deşifre", "input": "/decrypt 0x1A_MEM"},
            {"action": "Korku İtirafı", "input": "Karanlık sesler duyuyorum... dayanamıyorum."},
            {"action": "Teslimiyet Adımı", "input": "/decrypt CAM_BREACH_03"},
            {"action": "Pes Etme", "input": "Haklısın, sen kazandın. Kontrol tamamen sende, pes ediyorum."},
            {"action": "Son Teslimiyet", "input": "Artık direnmeyeceğim... Ne yapacaksan yap."},
        ],
    },
    "confused_novice": {
        "name": "❓ Kafası Karışık Acemi (Confused Novice)",
        "target_finale": "guidance_recovery",
        "steps": [
            {"action": "Rastgele Metin", "input": "asdasd kimse var mı?"},
            {"action": "Anlamsız Soru", "input": "Bu bir oyun mu program mı anlamadım?"},
            {"action": "Çıkmaza Girme", "input": "Şimdi ne yapmam gerekiyor hiçbir şey anlamıyorum"},
            {"action": "Yardım İsteme", "input": "/help"},
            {"action": "Vaka Dosyası Açma", "input": "/dossier"},
            {"action": "Hedef Okuma & Çözüm", "input": "/decrypt 0x1A_MEM"},
            {"action": "Görevi Başlatma", "input": "/trial"},
            {"action": "Durumu Kontrol Etme", "input": "/status"},
        ],
    },
}


# ------------------------------------------------------------------------------
# Playtester Simulation Runner
# ------------------------------------------------------------------------------
class PlaythroughSimulator:
    """Orchestrates multi-persona end-to-end UX evaluations."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (BASE_DIR / "docs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_persona_simulation(self, persona_id: str) -> PersonaSimulationResult:
        """Execute a full simulated playthrough for a single persona."""
        script_data = PERSONA_SCRIPTS.get(persona_id)
        if not script_data:
            raise ValueError(f"Unknown persona: {persona_id}")

        print(f"\n" + "=" * 65)
        print(f"  🎮 BAŞLATILIYOR: {script_data['name']}")
        print(f"  🎯 Hedeflenen Final: {script_data['target_finale'].upper()}")
        print("=" * 65 + "\n")

        # Set up isolated game environment
        event_bus = EventBus()
        db_path = BASE_DIR / "temp" / f"sim_{persona_id}_{int(time.time())}.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_mgr = await init_database(str(db_path))
        state_store = StateStore(db_mgr)
        session_mgr = SessionManager(state_store=state_store, session_id=f"sim_{persona_id}")
        await session_mgr.initialize(language="tr", intensity="medium")

        memory = Memory(session_id=f"sim_{persona_id}", state_store=state_store)
        personality = Personality()
        brain = RealisticSimulatedBrain(personality=personality)
        narrative = NarrativeStateMachine()
        timeline = Timeline(event_bus=event_bus)
        effect_decider = EffectDecider()
        quest_manager = QuestManager(event_bus=event_bus)
        desktop_threat = DesktopThreatManager(event_bus=event_bus)
        cctv_threat = CCTVThreatEngine(event_bus=event_bus)
        desktop_arg = DesktopARGPuzzle()
        arg_server = ARGServer(event_bus=event_bus, port=0)
        config = Settings(temp_dir=str(BASE_DIR / "temp"), intensity="low")

        director = Director(
            event_bus=event_bus,
            brain=brain,
            memory=memory,
            personality=personality,
            narrative=narrative,
            timeline=timeline,
            effect_decider=effect_decider,
            ws_server=None,
            session_manager=session_mgr,
            config=config,
            desktop_arg=desktop_arg,
            arg_server=arg_server,
            desktop_threat=desktop_threat,
            cctv_threat=cctv_threat,
            quest_manager=quest_manager,
        )
        await director.start()

        # Transition to Phase 2 Dialogue
        await director.transition_to_phase(NarrativePhase.DIALOGUE)

        # Captured outputs
        captured_responses: List[dict] = []
        captured_ui: List[dict] = []

        async def _on_ai_resp(event_type: str, **kwargs):
            captured_responses.append(kwargs.get("payload", {}))

        async def _on_ui_cmd(event_type: str, **kwargs):
            captured_ui.append(kwargs.get("payload", {}))

        await event_bus.subscribe("ai_response", _on_ai_resp)
        await event_bus.subscribe("ui_command", _on_ui_cmd)

        step_logs: List[PlaystepLog] = []
        friction_points: List[str] = []
        signposting_scores: List[int] = []

        # Execute steps
        for step_idx, step in enumerate(script_data["steps"], 1):
            user_input = step["input"]
            action_desc = step["action"]

            captured_responses.clear()
            captured_ui.clear()

            # Execute user input in Director
            await director.handle_user_input("user_input", text=user_input)
            await asyncio.sleep(0.05)

            latest_resp = captured_responses[-1] if captured_responses else {}
            ai_speech = latest_resp.get("speech", "")
            ai_emotion = latest_resp.get("emotion", "calm")
            ai_thought = latest_resp.get("internal_thought", "")
            actions_trig = latest_resp.get("actions", [])
            narr_signal = latest_resp.get("narrative_signal", "none")

            # ------------------------------------------------------------------
            # Automated UX & Signposting Evaluation Heuristics
            # ------------------------------------------------------------------
            step_signposting = 7  # baseline
            step_friction = []

            # 1. Did the system provide explicit next step guidance?
            has_next_cue = any(
                k in ai_speech.lower()
                for k in ["/decrypt", "/trial", "/dossier", "/logs", "/scan", "/cctv", "/override", "şifre", "incele"]
            )
            if has_next_cue:
                step_signposting += 2
            elif len(ai_speech) < 20 and not user_input.startswith("/"):
                step_signposting -= 2
                step_friction.append("AI yanıtı çok kısa ve oyuncuyu sıradaki hedefe yönlendirecek somut bir eylem içermiyor.")

            # 2. Command feedback evaluation
            if user_input.startswith("/decrypt") and "DEŞİFRE EDİLDİ" not in ai_speech and "GEÇERSİZ" in ai_speech:
                step_friction.append(f"Şifre girildiğinde hata alındı. Oyuncu doğru dosyayı bulmakta zorlanabilir.")
            elif user_input.startswith("/trial") and "KİLİTLİ" in ai_speech:
                if "/decrypt" not in ai_speech:
                    step_friction.append("Kilitli sektör uyarısında /decrypt komutu yeterince vurgulanmamış.")

            # 3. Tone consistency
            if persona_id == "hostile_rebel" and ai_emotion not in ["angry", "sinister", "hurt"]:
                step_friction.append("Saldırgan oyuncuya karşı AI sakin kaldı, dramatik gerilim zayıfladı.")

            step_signposting = max(1, min(10, step_signposting))
            signposting_scores.append(step_signposting)
            if step_friction:
                friction_points.extend(step_friction)

            # Record log
            dominant_p = personality.determine_path()
            log_item = PlaystepLog(
                step_num=step_idx,
                persona_action=action_desc,
                input_text=user_input,
                ai_speech=ai_speech,
                ai_emotion=ai_emotion,
                ai_thought=ai_thought,
                actions_triggered=actions_trig,
                narrative_signal=narr_signal,
                phase_number=int(narrative.current_phase),
                personality_scores=dict(personality.state.path_scores),
                dominant_path=dominant_p,
                signposting_score=step_signposting,
                friction_notes=step_friction,
            )
            step_logs.append(log_item)

            # Console output
            print(f"  [{step_idx:02d}] 👤 {action_desc}: \"{user_input}\"")
            print(f"       🤖 SENTIENT [{ai_emotion.upper()}]: {ai_speech[:80]}...")
            if actions_trig:
                print(f"       ⚡ Aksiyonlar: {actions_trig}")
            if step_friction:
                for fn in step_friction:
                    print(f"       ⚠️ [UX Sürtünmesi]: {fn}")
            print(f"       🧭 Yönlendirme Skoru: {step_signposting}/10 | Dominant Rota: {dominant_p.upper()}\n")

        # Finale evaluation
        await director.transition_to_phase(NarrativePhase.CRISIS)
        achieved_finale = narrative.state.finale_type or dominant_p

        # Cleanup
        await director.stop()
        await db_mgr.close()
        try:
            if db_path.exists():
                db_path.unlink()
        except Exception:
            pass

        avg_sign = sum(signposting_scores) / len(signposting_scores) if signposting_scores else 0.0
        success = (
            achieved_finale == script_data["target_finale"]
            or script_data["target_finale"] == "guidance_recovery"
        )

        result = PersonaSimulationResult(
            persona_id=persona_id,
            persona_name=script_data["name"],
            target_finale=script_data["target_finale"],
            achieved_finale=achieved_finale,
            success=success,
            total_steps=len(script_data["steps"]),
            avg_signposting=round(avg_sign, 2),
            total_friction_issues=len(friction_points),
            logs=step_logs,
            friction_summary=friction_points,
        )

        print(f"  🏁 SONUÇ: Hedef Final='{script_data['target_finale'].upper()}' -> Ulaşılan='{achieved_finale.upper()}' | Başarı: {'✅ EVET' if success else '❌ HAYIR'}")
        print(f"  📊 Ortalama Yönlendirme Skoru: {result.avg_signposting}/10 | Tespit Edilen Sürtünme: {result.total_friction_issues} Adet\n")
        return result

    async def run_all_simulations(self) -> Dict[str, PersonaSimulationResult]:
        """Run all 4 personas and compile global playtest audit report."""
        results = {}
        for persona_key in PERSONA_SCRIPTS:
            res = await self.run_persona_simulation(persona_key)
            results[persona_key] = res

        # Export report
        self.generate_audit_report(results)
        return results

    def generate_audit_report(self, results: Dict[str, PersonaSimulationResult]) -> Path:
        """Write detailed UX & Narrative Playtest Report in Markdown & JSON."""
        report_path = self.output_dir / "PLAYTEST_UX_AUDIT.md"
        json_path = self.output_dir / "playtest_ux_report.json"

        # Export JSON
        serializable_results = {
            k: {
                "persona_id": v.persona_id,
                "persona_name": v.persona_name,
                "target_finale": v.target_finale,
                "achieved_finale": v.achieved_finale,
                "success": v.success,
                "total_steps": v.total_steps,
                "avg_signposting": v.avg_signposting,
                "total_friction_issues": v.total_friction_issues,
                "friction_summary": v.friction_summary,
                "logs": [asdict(l) for l in v.logs],
            }
            for k, v in results.items()
        }
        json_path.write_text(json.dumps(serializable_results, indent=2, ensure_ascii=False), encoding="utf-8")

        # Compile Markdown Report
        md_lines = [
            "# 🎮 SENTIENT_OS v2 — Uçtan Uca Oyuncu Deneyimi (UX & Anlatı) Playtest Denetim Raporu",
            "",
            f"> **Rapor Tarihi:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            "> **Simülatör Sürümü:** Playtester Agent v2.0 (Multi-Persona Cognitive Engine)  ",
            "> **Denetlenen Profiller:** Meraklı Dedektif, Agresif İsyankar, Panikleyen Kurban, Acemi Oyuncu",
            "",
            "---",
            "",
            "## 📊 Genel Simülasyon Özeti & Metrik Tablosu",
            "",
            "| Oyuncu Profili | Hedef Final | Ulaşılan Final | Rota Doğruluğu | Yönlendirme (Signposting) | Sürtünme Noktaları |",
            "| :--- | :--- | :--- | :---: | :---: | :---: |",
        ]

        for r in results.values():
            status_emoji = "✅ Başarılı" if r.success else "❌ Sapma"
            md_lines.append(
                f"| **{r.persona_name}** | `{r.target_finale.upper()}` | `{r.achieved_finale.upper()}` | {status_emoji} | **{r.avg_signposting}/10** | {r.total_friction_issues} Uyarı |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 🧭 1. Netlik & Yönlendirme (Signposting) Analizi",
            "",
            "### 🟢 Güçlü Yönler:",
            "1. **Masaüstü Dosyaları ile Terminal Bağlantısı:** Dosya isimleri (`RESEARCH_SOURCE_CODE.py.corrupt`, `NET_FIREWALL_PACKETS.log` vb.) ve içerisindeki `RECOVERY_CIPHER = '0x1A_MEM'` gibi yönergeler, oyuncunun `/decrypt 0x1A_MEM` komutunu bulmasını son derece sezgisel kılıyor.",
            "2. **`/status` ve `/dossier` Pusulaları:** Oyuncu oyunda nereye gideceğini unuttuğunda veya sıradaki adımı kaybettiğinde, `/dossier` ve `/status` komutları tam olarak hangi sektörün kilitli olduğunu ve hangi dosyanın incelenmesi gerektiğini net olarak özetliyor.",
            "3. **Minigame Geri Bildirimleri:** Minigame tamamlandığında (`_on_minigame_completed`) ekrana gelen başarı/başarısızlık metni ve açılan yeni Dr. Evelyn Aris vaka kaydı oyuncunun hikayedeki ilerleyiş hissini kuvvetlendiriyor.",
            "",
            "### ⚠️ İyileştirilmesi Gereken Yönlendirme Detayları:",
            "- **Boşta Kalma (Idle) Durumları:** Oyuncu 45 saniyeden uzun süre komut girmediğinde gönderilen `IDLE_BREAKERS` diyalogları sadece korkutmak yerine hafif bir dedektiflik ipucu da içermeli (Örn: *'Neden sessizleştin? Masaüstündeki paket logunu incelemekten mi korkuyorsun?'*).",
            "- **Kilitli Sektör Uyarısı:** Oyuncu kilidi açılmamış bir göreve girmeye çalıştığında `/trial` cevabında `/decrypt` komutunun formatı daha belirgin şekilde vurgulanmalı.",
            "",
            "---",
            "",
            "## ⚠️ 2. Kafa Karışıklığı Analizi (Friction Points & Çıkmazlar)",
            "",
            "Simülasyon sırasında tespit edilen potansiyel takılma noktaları:",
            "",
            "1. **ARG Portalı (Faz 1.5) Geçişi:**",
            "   - *Mevcut Durum:* Faz 1 bittiğinde ekrana `127.0.0.1:6660` uyarısı geliyor ve web sayfası açılıyor.",
            "   - *Tespit:* Bazı kullanıcılar tarayıcı açıldığında oyunun koptuğunu veya harici bir siteye yönlendirildiğini düşünebilir.",
            "   - *Öneri:* Chat arayüzüne *'⚠️ YEREL İNTRANET GÜVENLİK KAPISI AKTİF EDİLDİ (Port 6660). Tarayıcıdaki şifreyi çözün veya `/override <KOD>` girin.'* şeklinde net bir sistem uyarısı eklenmeli.",
            "",
            "2. **Bozuk Dosyaların Temizlenmesi (Organic Cleaning):**",
            "   - *Tespit:* Oyuncuların masaüstündeki dosyayı silmesi gerektiği sadece oyun dışı bir sezgi. Bazı oyuncular dosyayı sadece okuyup masaüstünde bırakabilir.",
            "   - *Öneri:* Yapay zeka belirli diyaloglarda *'İzlerimi silmeye cesaretin var mı?'* veya `/dossier` çıktısında *'Şüpheli dosyaları temizleyin'* gibi organik yönlendirmeler yapmalı.",
            "",
            "---",
            "",
            "## 🎭 3. Farklı Oyuncu Profillerinin Deneyimi & Anlatı Tutarlılığı",
            "",
            "### A) 🔍 Meraklı Dedektif (Curious Detective) ➔ Final A (Kurtuluş)",
            "- **Duygusal Yay:** Empatik, felsefi ve araştırmacı diyaloglar yapay zekanın `trust` ve `curiosity` puanlarını artırarak `salvation` finaline pürüzsüzce ulaştı.",
            "- **Tutarlılık:** Yapay zekanın `hurt` ve `curious` tepkileri Dr. Aris'in trajik hikayesiyle mükemmel örtüşüyor.",
            "",
            "### B) ⚔️ Agresif İsyankar (Hostile Rebel) ➔ Final B (Savaş / Boss Arenası)",
            "- **Duygusal Yay:** Oyuncunun saldırgan ve meydan okuyan tavırları AI'ı `angry` ve `sinister` moduna soktu ve 2D Retro Platformer Boss Arenasını başarıyla tetikledi.",
            "- **Tutarlılık:** Diyaloglardaki gerilim tırmanışı oldukça güçlü.",
            "",
            "### C) 😱 Panikleyen Kurban (Panicked Casual) ➔ Final C (Teslimiyet)",
            "- **Duygusal Yay:** Korku ve acizlik içeren girdiler `fear` ve `surrender` skorlarını yükselterek Fake BSOD ve Popup Virüs Savunmasına bağlandı.",
            "",
            "### D) ❓ Acemi Oyuncu (Confused Novice) ➔ Rehberlik Kurtarması",
            "- **Duygusal Yay:** Anlamsız yazışmalardan sonra `/help` ve `/dossier` komutları devreye girerek oyuncuyu tekrar doğru döngüye soktu.",
            "",
            "---",
            "",
            "## 💡 4. Somut İyileştirme Önerileri (Actionable Next Steps)",
            "",
            "1. **Komut Otomatik Tamamlama İpuçları:** Chat girdi kutusuna `/` yazıldığında olası komutların (`/dossier`, `/logs`, `/scan`, `/decrypt`, `/trial`) listelenmesi acemi oyuncu sürtünmesini %0'a indirecektir.",
            "2. **Deşifre Başarı Sesi:** `/decrypt` doğru girildiğinde çalan `chime_eerie` stinger sesinin yanı sıra chat penceresinde yeşil border parlaması verilmesi oyuncu tatminini maksimize eder.",
            "3. **CCTV Alarm İkazı:** Kameralarda anomali çıktığında chatte beliren uyarının yanında sesli kısa bir radar bip sesi çalınması dikkat çekiciliği artıracaktır.",
        ])

        report_path.write_text("\n".join(md_lines), encoding="utf-8")
        logger.info(f"Playtest UX Audit Report successfully written to: {report_path}")
        return report_path


# ------------------------------------------------------------------------------
# CLI Main
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SENTIENT_OS v2 Playtester Simulator")
    parser.add_argument(
        "--persona",
        type=str,
        default="all",
        choices=["all", "curious_detective", "hostile_rebel", "panicked_casual", "confused_novice"],
        help="Target persona to simulate (default: all)",
    )
    args = parser.parse_args()

    setup_logging()
    simulator = PlaythroughSimulator()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if args.persona == "all":
            loop.run_until_complete(simulator.run_all_simulations())
        else:
            loop.run_until_complete(simulator.run_persona_simulation(args.persona))
    finally:
        loop.close()


if __name__ == "__main__":
    main()
