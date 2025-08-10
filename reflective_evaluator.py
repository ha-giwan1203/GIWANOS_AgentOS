import logging
from typing import Any, Dict

class ReflectionAgent:
    """Stub Reflection agent – always passes. Extend later with LLM calls."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("reflection_agent")
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.INFO)

    def evaluate(self, answer: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.logger.info("🔍 Reflection pass (stub) — OK")
        return {"verdict": "pass", "critique": "", "revised_answer": answer}

    # Wrapper expected by master‑loop
    def perform_reflection(self, answer: str, context: Dict[str, Any] | None = None):
        return self.evaluate(answer, context)


