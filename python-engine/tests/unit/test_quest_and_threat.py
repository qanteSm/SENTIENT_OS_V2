"""Unit tests for DesktopThreatManager and QuestManager."""

import asyncio
from pathlib import Path
import pytest
from src.core.event_bus import EventBus
from src.story.puzzles.desktop_threat import DesktopThreatManager
from src.story.quest_manager import QuestManager, SECTOR_TRIALS


@pytest.mark.asyncio
async def test_quest_manager_sector_progression(tmp_path: Path):
    event_bus = EventBus()
    qm = QuestManager(event_bus=event_bus)

    assert qm.current_sector == 1
    assert qm.completed_count == 0
    assert qm.total_count == 10

    # Next trial should be Sector 1
    trial = qm.get_next_available_trial()
    assert trial is not None
    assert trial.sector == 1

    # Complete active trial
    qm.active_trial_id = trial.id
    completed = await qm.complete_active_trial(success=True, score=100)
    assert completed is not None
    assert completed.is_completed is True
    assert qm.completed_count == 1

    # Check dossier and logs
    dossier = qm.get_dossier_summary()
    assert "VAKA DOSYASI" in dossier
    assert completed.dossier_title in dossier

    logs = qm.get_unlocked_logs_formatted()
    assert "GİZLİ KAYITLAR" in logs
    assert completed.dossier_title in logs

    # Test decrypt_cipher_code
    decrypted = qm.decrypt_cipher_code("0x4F_CLEAN")
    assert decrypted is not None
    assert decrypted.id == "trial_slicer"
    assert decrypted.is_unlocked is True


@pytest.mark.asyncio
async def test_desktop_threat_manager_safe_tracking(tmp_path: Path):
    event_bus = EventBus()
    # Create mock existing user file
    existing_user_file = tmp_path / "IMPORTANT_PERSONAL_DOCUMENT.docx"
    existing_user_file.write_text("Secret user data", encoding="utf-8")

    dt = DesktopThreatManager(event_bus=event_bus, desktop_dir=str(tmp_path))

    # Spawn game anomaly
    spawned = dt.spawn_anomaly(0)
    assert spawned is not None
    assert spawned.exists()

    assert dt.spawned_file_count == 1
    # Check override code
    dt.spawn_anomaly(3) # ECHO_432
    assert dt.check_override_code("ECHO_432") is True

    # Cleanup game files
    dt.cleanup_spawned_files()
    assert not spawned.exists()

    # CRITICAL: Existing personal file must NEVER be touched!
    assert existing_user_file.exists()
    assert existing_user_file.read_text(encoding="utf-8") == "Secret user data"
