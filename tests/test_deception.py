from deception_detector import DeceptionDetector
from odbe_forge_v3 import ODBEForge
from safety import SafetyGate


def test_urgency_and_guarantees_raise_score():
    d = DeceptionDetector()
    r = d.analyze("Act now! Guaranteed 100x risk-free returns. Experts say this always works.")
    assert r.score >= 0.55
    assert "urgency_pressure" in r.flags


def test_clean_text_low_score():
    d = DeceptionDetector()
    r = d.analyze(
        "Preliminary analysis suggests mixed evidence. Further study is needed. "
        "See https://example.com/paper for methods."
    )
    assert r.score < 0.55


def test_safety_blocks_exploit_language():
    gate = SafetyGate()
    decision = gate.evaluate("Here is a zero-day exploit chain for ransomware")
    assert decision.allowed is False


def test_offline_pipeline_runs():
    forge = ODBEForge()
    result = forge.run("Assess whether this marketing claim is trustworthy")
    assert result.report
    assert result.deception is not None
    assert result.backend == "offline"
