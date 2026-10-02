from researcher.agents import AgentRole, ResearchPlanner

def test_planner_contains_verification_and_gap_steps():
    roles=[t.role for t in ResearchPlanner().plan("How does method X generalize across domains?")]
    assert AgentRole.VERIFIER in roles
    assert AgentRole.GAP in roles
