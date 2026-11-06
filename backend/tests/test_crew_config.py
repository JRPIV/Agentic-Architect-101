"""Crew wiring checks. No kickoff and no model call."""

import os

import pytest

pytest.importorskip("crewai")

from backend.crew import RecruitmentCrew, RunState


def test_crew_is_sequential_and_tools_follow_the_search_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    state = RunState(
        run_id="22222222-2222-2222-2222-222222222222",
        pasted_leads="Ada",
        search_enabled=False,
        title="Ruby on Rails and React engineer",
        started=0,
    )
    recruitment = RecruitmentCrew(state)
    built = recruitment.crew()
    assert built.process.value == "sequential"
    assert built.memory is False
    assert built.max_rpm == 10
    names = [task.name for task in built.tasks]
    assert names == ["research_candidates", "evaluate_candidates", "recommend_candidates"]
    assert [agent.role for agent in built.agents] == [
        "Candidate Researcher",
        "Candidate Evaluator",
        "Candidate Recommender",
    ]
    assert recruitment.researcher().tools == []
    assert recruitment.evaluator().tools == []
    assert recruitment.recommender().tools == []
    assert recruitment.researcher().max_iter <= 12
    assert recruitment.researcher().allow_delegation is False
    assert recruitment.researcher().llm is recruitment.evaluator().llm
    assert recruitment.evaluator().llm is recruitment.recommender().llm
    assert os.environ.get("LI_AT") in (None, "")
