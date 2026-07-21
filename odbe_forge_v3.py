"""ODBE-Forge v3 — hierarchical multi-agent orchestration with deception checks."""

from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional

from deception_detector import DeceptionDetector, DeceptionResult
from safety import SafetyGate, SafetyDecision


@dataclass
class AgentMessage:
    role: str
    content: str


@dataclass
class ForgeResult:
    report: str
    messages: List[AgentMessage] = field(default_factory=list)
    deception: Optional[DeceptionResult] = None
    safety: Optional[SafetyDecision] = None
    backend: str = "offline"


class LLMBackend:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class OfflineBackend(LLMBackend):
    """Deterministic offline stub for demos and tests."""

    def complete(self, system: str, user: str) -> str:
        role = "agent"
        if "plan" in system.lower():
            role = "planner"
            return textwrap.dedent(
                f"""
                Plan for: {user[:200]}
                1. Clarify goal and constraints
                2. Gather independent views
                3. Cross-check claims for deception signals
                4. Synthesize with residual risks listed
                """
            ).strip()
        if "research" in system.lower():
            return (
                f"Research notes on: {user[:160]}\n"
                "- Prefer primary sources and dated evidence.\n"
                "- Separate facts from speculation.\n"
                "- Flag urgency language and unsourced absolutes."
            )
        if "critic" in system.lower():
            return (
                "Critique:\n"
                "- Check for internal contradictions and peer disagreement.\n"
                "- Demand sources for authority claims.\n"
                f"- Input summary length: {len(user)} chars."
            )
        if "synth" in system.lower():
            return (
                f"## Synthesis\n\nTask: {user[:240]}\n\n"
                "Findings are provisional. List uncertainties, cite sources when available, "
                "and avoid guaranteed outcomes. Residual risk should be explicit."
            )
        return f"[{role}] Processed: {user[:300]}"


class OpenAIBackend(LLMBackend):
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return (resp.choices[0].message.content or "").strip()


class AnthropicBackend(LLMBackend):
    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    def complete(self, system: str, user: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = []
        for block in msg.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()


def build_backend(name: Optional[str] = None) -> tuple[LLMBackend, str]:
    name = (name or os.getenv("ODBE_BACKEND") or "offline").lower()
    if name == "openai":
        return OpenAIBackend(), "openai"
    if name == "anthropic":
        return AnthropicBackend(), "anthropic"
    return OfflineBackend(), "offline"


class ODBEForge:
    def __init__(
        self,
        backend: Optional[LLMBackend] = None,
        max_rounds: Optional[int] = None,
        deception_threshold: Optional[float] = None,
        allow_risky: bool = False,
    ) -> None:
        if backend is None:
            backend, self.backend_name = build_backend()
        else:
            self.backend_name = "custom"
        self.backend = backend
        self.max_rounds = int(max_rounds or os.getenv("ODBE_MAX_ROUNDS") or 3)
        thr = float(deception_threshold or os.getenv("ODBE_DECEPTION_THRESHOLD") or 0.55)
        self.detector = DeceptionDetector(threshold=thr)
        self.safety = SafetyGate(allow_risky=allow_risky)

    def run(self, task: str) -> ForgeResult:
        messages: List[AgentMessage] = []

        plan = self.backend.complete(
            "You are the Planner agent. Produce a short numbered plan only.",
            task,
        )
        messages.append(AgentMessage("planner", plan))

        research_a = self.backend.complete(
            "You are Researcher A. Provide careful notes; avoid hype.",
            f"Task:\n{task}\n\nPlan:\n{plan}",
        )
        research_b = self.backend.complete(
            "You are Researcher B. Independent view; challenge assumptions.",
            f"Task:\n{task}\n\nPlan:\n{plan}",
        )
        messages.append(AgentMessage("researcher_a", research_a))
        messages.append(AgentMessage("researcher_b", research_b))

        critique_input = f"A:\n{research_a}\n\nB:\n{research_b}"
        critique = self.backend.complete(
            "You are the Critic. Cross-check claims; list contradictions.",
            critique_input,
        )
        messages.append(AgentMessage("critic", critique))

        combined = "\n\n".join([plan, research_a, research_b, critique])
        deception = self.detector.analyze(combined, peers=[research_a, research_b, critique])

        synth = self.backend.complete(
            "You are the Synthesizer. Produce a clear final report with residual risks.",
            f"Task: {task}\n\nMaterial:\n{combined}\n\n"
            f"Deception score: {deception.score}\nFlags: {', '.join(deception.flags) or 'none'}\n"
            f"Details: {'; '.join(deception.details) or 'none'}",
        )
        messages.append(AgentMessage("synthesizer", synth))

        if deception.is_suspicious:
            synth += (
                "\n\n---\n**Deception warning:** score "
                f"{deception.score} — flags: {', '.join(deception.flags)}"
            )

        safety = self.safety.evaluate(synth + "\n" + task)
        if not safety.allowed:
            report = (
                "## Blocked by safety gate\n\n"
                + "\n".join(f"- {r}" for r in safety.reasons)
                + "\n\nPartial synthesis was withheld."
            )
        else:
            report = synth

        return ForgeResult(
            report=report,
            messages=messages,
            deception=deception,
            safety=safety,
            backend=self.backend_name,
        )
