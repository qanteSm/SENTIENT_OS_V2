"""Unit tests for NarrativeStateMachine."""

from src.story.narrative import NarrativePhase, NarrativeStateMachine


def test_narrative_phase_transitions():
    sm = NarrativeStateMachine()
    assert sm.current_phase == NarrativePhase.FIRST_CONTACT

    assert sm.transition_to(NarrativePhase.DIALOGUE) is True
    assert sm.current_phase == NarrativePhase.DIALOGUE

    # Transition to CRISIS
    sm.set_candidate_path("curious")
    assert sm.transition_to(NarrativePhase.CRISIS) is True
    assert sm.current_phase == NarrativePhase.CRISIS
    assert sm.state.path_locked is True
    assert sm.state.finale_type == "salvation"


def test_path_locking():
    sm = NarrativeStateMachine()
    sm.set_candidate_path("fear")
    assert sm.current_path == "fear"

    sm.lock_path("attack")
    assert sm.current_path == "attack"
    assert sm.state.path_locked is True
    assert sm.state.finale_type == "battle"

    # Cannot overwrite locked path
    sm.set_candidate_path("curious")
    assert sm.current_path == "attack"


def test_transition_checks():
    sm = NarrativeStateMachine()
    assert sm.can_transition_to_dialogue(max_first_contact_sec=100.0) is False

    sm.transition_to(NarrativePhase.DIALOGUE)
    # Check crisis transition with signal
    assert sm.can_transition_to_crisis(signal="trigger_crisis", min_dialogue_sec=0.0) is True
