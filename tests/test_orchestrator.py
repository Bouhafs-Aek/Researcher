from researcher.agents import AgentRole
from researcher.orchestrator import DynamicOrchestrator

def test_orchestrator_spawns_verifier_after_evidence():
    state = DynamicOrchestrator().start("test question")
    state = DynamicOrchestrator().update(state, evidence_count=10, coverage_score=0.2)
    assert any(t.task.role == AgentRole.VERIFIER for t in state.tasks.values())

def test_orchestrator_waits_for_coverage_before_synthesis():
    orchestrator = DynamicOrchestrator()
    state = orchestrator.start("test question")
    state = orchestrator.update(state, evidence_count=10, coverage_score=0.9)
    verifier = next(t for t in state.tasks.values() if t.task.role == AgentRole.VERIFIER)
    orchestrator.complete(state, verifier.id)
    assert any(t.task.role == AgentRole.SYNTHESIS for t in state.tasks.values())
