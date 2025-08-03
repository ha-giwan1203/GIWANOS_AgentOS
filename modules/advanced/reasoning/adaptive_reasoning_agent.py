import logging
class ReasoningResult:
    def __init__(self, answer, related_results, related_tasks):
        self.answer = answer; self.related_results = related_results; self.related_tasks = related_tasks
    def get_related_results(self): return self.related_results
class AdaptiveReasoningAgent:
    def __init__(self): self.logger = logging.getLogger("adaptive_reasoning_agent")
    def _intent(self, q): return "simple" if any(k in q for k in ["날씨","환율","FAQ"]) else "complex"
    def perform_reasoning(self, ctx, _):
        model = "gpt-3.5-turbo" if self._intent(ctx["answer"])=="simple" else "gpt-4o-mini"
        ans = f"{model} 결과: {ctx['answer']}"
        tasks=[{"tool":"system_metrics","args":{}}]
        return ReasoningResult(ans, [], tasks)
