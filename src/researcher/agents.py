from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class AgentRole(str, Enum):
    PLANNER="planner"; SCOUT="literature_scout"; SCREENING="screening"; EXTRACTION="extraction"; VERIFIER="citation_verifier"; GAP="gap_investigator"; REVIEWER="adversarial_reviewer"; SYNTHESIS="synthesis"
@dataclass
class AgentTask:
    role: AgentRole
    objective: str
    dependencies: list[str]=field(default_factory=list)
class ResearchPlanner:
    def plan(self, question: str) -> list[AgentTask]:
        return [
            AgentTask(AgentRole.SCOUT,f"Find primary literature relevant to: {question}"),
            AgentTask(AgentRole.SCREENING,"Deduplicate and screen sources against scope."),
            AgentTask(AgentRole.EXTRACTION,"Extract atomic claims, methods, populations, conditions, and results."),
            AgentTask(AgentRole.VERIFIER,"Verify important claims against source passages and provenance."),
            AgentTask(AgentRole.GAP,"Search for counterevidence and candidate research gaps."),
            AgentTask(AgentRole.REVIEWER,"Challenge candidate gaps and search for prior work."),
            AgentTask(AgentRole.SYNTHESIS,"Synthesize only claims that pass the evidence gate."),
        ]
