from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from .agents import AgentRole, AgentTask

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class DynamicTask:
    id: str
    task: AgentTask
    status: TaskStatus = TaskStatus.PENDING
    evidence_count: int = 0
    notes: list[str] = field(default_factory=list)

@dataclass
class ResearchState:
    question: str
    tasks: dict[str, DynamicTask] = field(default_factory=dict)
    completed_roles: set[AgentRole] = field(default_factory=set)
    evidence_count: int = 0
    coverage_score: float = 0.0
    disagreements: int = 0

class DynamicOrchestrator:
    """Deterministic MVP orchestrator with evidence-driven task spawning."""

    def start(self, question: str) -> ResearchState:
        state = ResearchState(question=question)
        for task in (
            AgentTask(AgentRole.SCOUT, f"Find literature relevant to: {question}"),
            AgentTask(AgentRole.SCREENING, "Screen and deduplicate retrieved literature."),
            AgentTask(AgentRole.EXTRACTION, "Extract atomic claims and experimental conditions."),
        ):
            self._add(state, task)
        return state

    def update(self, state: ResearchState, *, evidence_count: int,
               coverage_score: float, disagreements: int = 0) -> ResearchState:
        state.evidence_count = evidence_count
        state.coverage_score = max(0.0, min(1.0, coverage_score))
        state.disagreements = disagreements
        self._spawn_if_needed(state)
        return state

    def complete(self, state: ResearchState, task_id: str) -> ResearchState:
        task = state.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        state.completed_roles.add(task.task.role)
        self._spawn_if_needed(state)
        return state

    def _spawn_if_needed(self, state: ResearchState) -> None:
        roles = {item.task.role for item in state.tasks.values()}
        if AgentRole.VERIFIER not in roles and state.evidence_count > 0:
            self._add(state, AgentTask(AgentRole.VERIFIER,
                "Verify source identity, passages, interpretation, and provenance."))
        if AgentRole.GAP not in roles and state.coverage_score >= 0.35:
            self._add(state, AgentTask(AgentRole.GAP,
                "Investigate candidate limitations and search for counterevidence."))
        if AgentRole.REVIEWER not in roles and (
            state.disagreements > 0 or state.coverage_score >= 0.70
        ):
            self._add(state, AgentTask(AgentRole.REVIEWER,
                "Adversarially challenge candidate findings and search for prior work."))
        if AgentRole.SYNTHESIS not in roles and (
            state.coverage_score >= 0.80 and AgentRole.VERIFIER in state.completed_roles
        ):
            self._add(state, AgentTask(AgentRole.SYNTHESIS,
                "Synthesize only evidence that passed the verification gate."))

    @staticmethod
    def _add(state: ResearchState, task: AgentTask) -> None:
        task_id = str(uuid4())
        state.tasks[task_id] = DynamicTask(id=task_id, task=task)
