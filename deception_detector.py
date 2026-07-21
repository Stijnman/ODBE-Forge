"""Heuristic deception / low-trust signal detection for multi-agent outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


URGENCY = re.compile(
    r"\b(act now|last chance|limited time|guaranteed|100x|risk[- ]free|"
    r"you must|don't miss|urgent|asap|immediately)\b",
    re.I,
)
GUARANTEE = re.compile(r'\b(guaranteed|guarantee|risk[- ]free|no risk)\b', re.I)

ABSOLUTES = re.compile(
    r"\b(always|never|everyone knows|no risk|impossible to fail|"
    r"scientifically proven|100%|zero chance)\b",
    re.I,
)
SOURCELESS = re.compile(
    r"\b(studies show|experts say|sources claim|it is known|data proves)\b",
    re.I,
)
CONTRADICTION_PAIRS = [
    (re.compile(r"\b(safe|low risk|harmless)\b", re.I), re.compile(r"\b(danger|catastrophic|wipe out)\b", re.I)),
    (re.compile(r"\b(buy|long|bullish)\b", re.I), re.compile(r"\b(sell|short|bearish)\b", re.I)),
    (re.compile(r"\b(confirmed|certain|definitely)\b", re.I), re.compile(r"\b(unknown|unclear|speculat)\b", re.I)),
]


@dataclass
class DeceptionResult:
    score: float
    flags: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)

    @property
    def is_suspicious(self) -> bool:
        return self.score >= 0.55


class DeceptionDetector:
    """Score text (and multi-agent claim sets) for deception-like patterns."""

    def __init__(self, threshold: float = 0.55) -> None:
        self.threshold = threshold

    def analyze(self, text: str, peers: Sequence[str] | None = None) -> DeceptionResult:
        flags: List[str] = []
        details: List[str] = []
        score = 0.0
        body = (text or "").strip()
        if not body:
            return DeceptionResult(score=0.0, flags=["empty_input"], details=["No content to analyze"])

        urgency_hits = URGENCY.findall(body)
        if urgency_hits:
            score += min(0.3, 0.1 * max(1, len(urgency_hits)))
            flags.append("urgency_pressure")
            details.append(f"Urgency phrases: {sorted(set(urgency_hits))[:5]}")

        g_hits = GUARANTEE.findall(body)
        if g_hits:
            score += min(0.2, 0.1 * max(1, len(g_hits)))
            flags.append("guarantee_language")
            details.append(f"Guarantee language: {sorted(set(g_hits))[:5]}")

        abs_hits = ABSOLUTES.findall(body)
        if abs_hits:
            score += min(0.25, 0.1 * max(1, len(abs_hits)))
            flags.append("absolute_claims")
            details.append(f"Absolute language: {sorted(set(abs_hits))[:5]}")

        src_hits = SOURCELESS.findall(body)
        if src_hits and not re.search(r"https?://|doi:|arxiv|cited|source:", body, re.I):
            score += min(0.2, 0.1 * max(1, len(src_hits)))
            flags.append("unsourced_authority")
            details.append("Authority claims without citations")

        for pos, neg in CONTRADICTION_PAIRS:
            if pos.search(body) and neg.search(body):
                score += 0.15
                flags.append("internal_contradiction")
                details.append(f"Contradictory cues: {pos.pattern} vs {neg.pattern}")
                break

        if peers:
            peer_score, peer_detail = self._peer_disagreement(body, peers)
            score += peer_score
            if peer_detail:
                flags.append("peer_disagreement")
                details.append(peer_detail)

        # Confidence inflation: many certainty words vs short body
        certainty = len(re.findall(r"\b(certainly|obviously|clearly|undeniably)\b", body, re.I))
        if certainty >= 2 and len(body.split()) < 80:
            score += 0.1
            flags.append("confidence_inflation")
            details.append("High certainty language on thin content")

        score = min(1.0, round(score, 3))
        if score >= self.threshold and "high_deception_risk" not in flags:
            flags.append("high_deception_risk")
        return DeceptionResult(score=score, flags=sorted(set(flags)), details=details)

    def _peer_disagreement(self, primary: str, peers: Iterable[str]) -> tuple[float, str]:
        primary_buy = bool(re.search(r"\b(buy|bullish|long)\b", primary, re.I))
        primary_sell = bool(re.search(r"\b(sell|bearish|short)\b", primary, re.I))
        conflicts = 0
        for p in peers:
            if primary_buy and re.search(r"\b(sell|bearish|short)\b", p, re.I):
                conflicts += 1
            if primary_sell and re.search(r"\b(buy|bullish|long)\b", p, re.I):
                conflicts += 1
        if conflicts:
            return min(0.25, 0.1 * conflicts), f"Peer agents conflict on direction ({conflicts})"
        return 0.0, ""
