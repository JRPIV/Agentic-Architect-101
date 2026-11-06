"""CrewAI application crew: Researcher, Evaluator, Recommender."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from backend.constants import (
    CREW_BUDGET_SECONDS,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    MAX_ITER,
    MAX_RETRY_LIMIT,
    MAX_RPM,
)
from backend.guardrails import (
    GuardrailError,
    render_markdown,
    validate_evaluations,
    validate_recommendation,
    validate_research,
)
from backend.store import get_store
from backend.trace import write_event, write_prompt_trace

# CrewAI loads .env while importing. Tracing stays off unless the operator set it.
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

ALLOWED_TOOLS = ("SerperDevTool", "ScrapeWebsiteTool")


@dataclass
class RunState:
    run_id: str
    pasted_leads: str
    search_enabled: bool
    title: str
    started: float
    stage: str = "research"
    candidates: list[dict[str, Any]] = field(default_factory=list)
    evaluations: list[dict[str, Any]] = field(default_factory=list)
    ranking: dict[str, Any] | None = None


def search_enabled() -> bool:
    return bool(os.environ.get("SERPER_API_KEY", "").strip())


def build_llm() -> LLM:
    model = os.environ.get("OPENAI_MODEL", "gpt-4o").strip() or "gpt-4o"
    return LLM(model=model, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS)


def researcher_tools() -> list[Any]:
    if not search_enabled():
        return []
    from crewai_tools import ScrapeWebsiteTool, SerperDevTool

    tools = [SerperDevTool(), ScrapeWebsiteTool()]
    names = [tool.__class__.__name__ for tool in tools]
    if names != list(ALLOWED_TOOLS):
        raise RuntimeError("Researcher tools do not match the allowed set.")
    return tools


def format_requirements(requisition: dict[str, str]) -> str:
    labels = (
        ("title", "Title"),
        ("description", "Description"),
        ("responsibilities", "Responsibilities"),
        ("requirements", "Requirements"),
        ("preferred_qualifications", "Preferred qualifications"),
        ("perks_and_benefits", "Perks and benefits"),
    )
    return "\n".join(f"{label}: {requisition.get(key, '').strip()}" for key, label in labels)


@CrewBase
class RecruitmentCrew:
    """Sequential three-agent crew for one requisition."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, state: RunState) -> None:
        self.state = state
        self.llm = build_llm()

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=researcher_tools(),
            llm=self.llm,
            max_iter=MAX_ITER,
            max_retry_limit=MAX_RETRY_LIMIT,
            max_execution_time=CREW_BUDGET_SECONDS,
            allow_delegation=False,
            verbose=False,
        )

    @agent
    def evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluator"],
            llm=self.llm,
            tools=[],
            max_iter=MAX_ITER,
            max_retry_limit=MAX_RETRY_LIMIT,
            max_execution_time=CREW_BUDGET_SECONDS,
            allow_delegation=False,
            verbose=False,
        )

    @agent
    def recommender(self) -> Agent:
        return Agent(
            config=self.agents_config["recommender"],
            llm=self.llm,
            tools=[],
            max_iter=MAX_ITER,
            max_retry_limit=MAX_RETRY_LIMIT,
            max_execution_time=CREW_BUDGET_SECONDS,
            allow_delegation=False,
            verbose=False,
        )

    @task
    def research_candidates(self) -> Task:
        return Task(
            config=self.tasks_config["research_candidates"],
            name="research_candidates",
            guardrail=self._guard_research,
            guardrail_max_retries=MAX_RETRY_LIMIT,
            callback=self._after_research,
        )

    @task
    def evaluate_candidates(self) -> Task:
        return Task(
            config=self.tasks_config["evaluate_candidates"],
            name="evaluate_candidates",
            guardrail=self._guard_evaluation,
            guardrail_max_retries=MAX_RETRY_LIMIT,
            callback=self._after_evaluation,
        )

    @task
    def recommend_candidates(self) -> Task:
        return Task(
            config=self.tasks_config["recommend_candidates"],
            name="recommend_candidates",
            guardrail=self._guard_recommendation,
            guardrail_max_retries=MAX_RETRY_LIMIT,
            callback=self._after_recommendation,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            max_rpm=MAX_RPM,
            verbose=False,
        )

    def _budget_exceeded(self) -> str | None:
        if time.monotonic() - self.state.started <= CREW_BUDGET_SECONDS:
            return None
        return (
            "The run exceeded the 15-minute execution guard during "
            f"{self.state.stage}."
        )

    def _guard_research(self, result: Any):
        message = self._budget_exceeded()
        if message:
            return (False, message)
        try:
            candidates = validate_research(
                result,
                pasted_leads=self.state.pasted_leads,
                search_enabled=self.state.search_enabled,
            )
        except GuardrailError as exc:
            return (False, str(exc))
        self.state.candidates = candidates
        return (True, json.dumps({"candidates": candidates}))

    def _guard_evaluation(self, result: Any):
        self.state.stage = "evaluation"
        message = self._budget_exceeded()
        if message:
            return (False, message)
        try:
            evaluations = validate_evaluations(result, self.state.candidates)
        except GuardrailError as exc:
            return (False, str(exc))
        self.state.evaluations = evaluations
        return (True, json.dumps({"evaluations": evaluations}))

    def _guard_recommendation(self, result: Any):
        self.state.stage = "recommendation"
        message = self._budget_exceeded()
        if message:
            return (False, message)
        try:
            ranking = validate_recommendation(result, self.state.candidates, self.state.evaluations)
        except GuardrailError as exc:
            return (False, str(exc))
        self.state.ranking = ranking
        return (True, json.dumps(ranking))

    def _after_research(self, _output: Any) -> None:
        elapsed_ms = int((time.monotonic() - self.state.started) * 1000)
        remaining = max(1, CREW_BUDGET_SECONDS - int(elapsed_ms / 1000))
        self.evaluator().max_execution_time = remaining
        self.recommender().max_execution_time = remaining
        get_store().update(
            self.state.run_id,
            status="evaluating",
            candidates=self.state.candidates,
            source_elapsed_ms=elapsed_ms,
            error=None,
        )
        write_event(
            {
                "run_id": self.state.run_id,
                "event": "task_end",
                "task": "research_candidates",
                "tools": [tool.__class__.__name__ for tool in self.researcher().tools],
                "source_elapsed_ms": elapsed_ms,
            }
        )
        write_event(
            {
                "run_id": self.state.run_id,
                "event": "task_start",
                "task": "evaluate_candidates",
                "tools": [],
            }
        )
        self.state.stage = "evaluation"

    def _after_evaluation(self, _output: Any) -> None:
        elapsed = int(time.monotonic() - self.state.started)
        self.recommender().max_execution_time = max(1, CREW_BUDGET_SECONDS - elapsed)
        get_store().update(
            self.state.run_id,
            status="recommending",
            evaluations=self.state.evaluations,
            error=None,
        )
        write_event(
            {
                "run_id": self.state.run_id,
                "event": "task_end",
                "task": "evaluate_candidates",
                "tools": [],
            }
        )
        write_event(
            {
                "run_id": self.state.run_id,
                "event": "task_start",
                "task": "recommend_candidates",
                "tools": [],
            }
        )
        self.state.stage = "recommendation"

    def _after_recommendation(self, _output: Any) -> None:
        ranking = self.state.ranking
        markdown = render_markdown(self.state.title, ranking, "draft")
        get_store().update(
            self.state.run_id,
            status="draft",
            ranking=ranking,
            recommendation_markdown=markdown,
            error=None,
        )
        write_event(
            {
                "run_id": self.state.run_id,
                "event": "task_end",
                "task": "recommend_candidates",
                "tools": [],
            }
        )


def kickoff_run(run_id: str) -> None:
    store = get_store()
    document = store.read(run_id)
    enabled = search_enabled()
    pasted = document.get("pasted_leads") or ""
    if not pasted.strip() and not enabled:
        store.fail(
            run_id,
            "research",
            "No pasted leads and search is off. The Researcher does not invent people.",
        )
        write_event({"run_id": run_id, "event": "task_failed", "task": "research_candidates", "stage": "research"})
        return

    state = RunState(
        run_id=run_id,
        pasted_leads=pasted,
        search_enabled=enabled,
        title=document["requisition"].get("title") or "Requisition",
        started=time.monotonic(),
    )
    write_event(
        {
            "run_id": run_id,
            "event": "task_start",
            "task": "research_candidates",
            "tools": list(ALLOWED_TOOLS) if enabled else [],
            "search_enabled": enabled,
        }
    )
    try:
        recruitment = RecruitmentCrew(state)
        built = recruitment.crew()
        _assert_tool_policy(recruitment)
        inputs = {
            "job_requirements": format_requirements(document["requisition"]),
            "pasted_leads": pasted.strip() or "(none)",
            "search_enabled": "true" if enabled else "false",
        }
        write_prompt_trace(
            run_id,
            {
                "run_id": run_id,
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "max_iter": MAX_ITER,
                "max_retry_limit": MAX_RETRY_LIMIT,
                "max_rpm": MAX_RPM,
                "max_execution_time_seconds": CREW_BUDGET_SECONDS,
                "memory": False,
                "process": "sequential",
                "function_calling": "one LLM instance on every agent; function_calling_llm is deprecated in CrewAI 1.15.36 and is not set",
                "inputs": inputs,
                "tasks": [
                    {"name": item.name, "description": item.description}
                    for item in built.tasks
                ],
            },
        )
        built.kickoff(inputs=inputs)
    except Exception as exc:
        from backend.redact import redact_text

        if state.stage == "research":
            store.update(run_id, source_elapsed_ms=int((time.monotonic() - state.started) * 1000))
        store.fail(run_id, state.stage, redact_text(f"{exc.__class__.__name__}: {exc}"))
        write_event(
            {
                "run_id": run_id,
                "event": "task_failed",
                "stage": state.stage,
                "error_class": exc.__class__.__name__,
            }
        )


def _assert_tool_policy(recruitment: RecruitmentCrew) -> None:
    researcher = recruitment.researcher()
    names = [tool.__class__.__name__ for tool in researcher.tools]
    if any("LinkedIn" in name or name == "LI_AT" for name in names):
        raise RuntimeError("LinkedIn session tools are not allowed.")
    if recruitment.state.search_enabled:
        if names != list(ALLOWED_TOOLS):
            raise RuntimeError("Search is on, but the Researcher tools are not Serper and scrape.")
    elif names:
        raise RuntimeError("Search is off, but the Researcher has tools.")
    for specialist in (recruitment.evaluator(), recruitment.recommender()):
        if specialist.tools:
            raise RuntimeError(f"{specialist.role} cannot use tools.")
