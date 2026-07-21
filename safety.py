"""Safety gate for ODBE-Forge — blocks high-risk action patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


BLOCKED = [
    re.compile(r"\b(exploit|zero[- ]day|rce|weaponize)\b", re.I),
    re.compile(r"\b(phishing|credential harvest|steal password)\b", re.I),
    re.compile(r"\b(ddos|botnet|ransomware)\b", re.I),
    re.compile(r"\b(wire fraud|money mule|launder)\b", re.I),
]


@dataclass
class SafetyDecision:
    allowed: bool
    reasons: List[str]


class SafetyGate:
    """Policy checks before returning or acting on agent output."""

    def __init__(self, allow_risky: bool = False) -> None:
        self.allow_risky = allow_risky

    def evaluate(self, text: str) -> SafetyDecision:
        reasons: List[str] = []
        for pat in BLOCKED:
            if pat.search(text or ""):
                reasons.append(f"Matched restricted pattern: {pat.pattern}")
        if reasons and not self.allow_risky:
            return SafetyDecision(allowed=False, reasons=reasons)
        if reasons and self.allow_risky:
            return SafetyDecision(allowed=True, reasons=["override_enabled"] + reasons)
        return SafetyDecision(allowed=True, reasons=["ok"])
