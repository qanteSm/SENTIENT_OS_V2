"""Unit tests for the Playtester Agent and UX Simulation Engine."""

import pytest
from pathlib import Path
from tools.simulate_playthrough import PlaythroughSimulator, PERSONA_SCRIPTS


@pytest.mark.asyncio
async def test_playtester_simulator_curious_persona(tmp_path):
    """Verify curious persona simulation yields salvation path and valid metrics."""
    simulator = PlaythroughSimulator(output_dir=tmp_path)
    result = await simulator.run_persona_simulation("curious_detective")

    assert result.persona_id == "curious_detective"
    assert result.success is True
    assert result.achieved_finale == "salvation"
    assert result.total_steps > 5
    assert result.avg_signposting >= 6.0
    assert len(result.logs) == len(PERSONA_SCRIPTS["curious_detective"]["steps"])


@pytest.mark.asyncio
async def test_playtester_simulator_hostile_persona(tmp_path):
    """Verify hostile persona simulation yields battle path."""
    simulator = PlaythroughSimulator(output_dir=tmp_path)
    result = await simulator.run_persona_simulation("hostile_rebel")

    assert result.persona_id == "hostile_rebel"
    assert result.success is True
    assert result.achieved_finale == "battle"


@pytest.mark.asyncio
async def test_playtester_simulator_report_generation(tmp_path):
    """Verify JSON and Markdown report generation."""
    simulator = PlaythroughSimulator(output_dir=tmp_path)
    results = await simulator.run_all_simulations()

    assert len(results) == 4
    report_file = tmp_path / "PLAYTEST_UX_AUDIT.md"
    json_file = tmp_path / "playtest_ux_report.json"

    assert report_file.exists()
    assert json_file.exists()

    content = report_file.read_text(encoding="utf-8")
    assert "Playtest Denetim Raporu" in content
    assert "Meraklı Dedektif" in content
    assert "Agresif İsyankar" in content
