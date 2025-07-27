"""
File: C:/giwanos/core/judge_agent.py

설명:
- Hybrid Decision Engine을 사용한 유연한 판단 로직 통합
- evaluate_context(context) 호출 후 반환된 actions 및 tool 호출 실행
- decision이 dict이 아닌 경우에도 안전하게 처리
- 툴매니저 메서드를 통해 fallback 액션 처리 지원
"""

import logging
from core.hybrid_decision_engine import evaluate_context
from core.tool_manager import ToolManager
from core.notifications import send_welcome_email, mark_as_adult

logger = logging.getLogger(__name__)

class JudgeAgent:
    def __init__(self):
        logger.info("Initializing JudgeAgent with hybrid decision engine.")

    def _gather_context(self) -> dict:
        from core.memory import get_latest_metrics
        return get_latest_metrics()

    def _execute_action(self, action: str):
        logger.info(f"Executing action: {action}")
        # 기본 액션
        if action == "send_welcome_email":
            send_welcome_email()
        elif action == "mark_as_adult":
            mark_as_adult()
        # ToolManager 기반 액션
        elif hasattr(ToolManager, action):
            logger.info(f"Invoking ToolManager for action: {action}")
            getattr(ToolManager, action)()
        else:
            logger.warning(f"No handler defined for action: {action}")

    def run(self):
        try:
            context = self._gather_context()
            decision = evaluate_context(context)

            # decision 타입 확인
            if not isinstance(decision, dict):
                logger.warning(f"Invalid decision type: {type(decision)}. Aborting run.")
                return

            # fallback tool 호출
            used = decision.get('used_fallback', False)
            tool_call = decision.get('tool', None)
            if used and isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args', [])
                if hasattr(ToolManager, tool_name):
                    logger.info(f"Invoking tool: {tool_name} with args {tool_args}")
                    getattr(ToolManager, tool_name)(*tool_args)
                else:
                    logger.warning(f"Unknown tool request: {tool_name}. Skipping.")
            elif used and tool_call is not None:
                logger.warning(f"Invalid tool request type: {type(tool_call)}. Skipping.")

            # actions 실행
            actions = decision.get('actions', [])
            if not isinstance(actions, list):
                logger.warning(f"Invalid actions type: {type(actions)}, expected list.")
                return
            for action in actions:
                self._execute_action(action)

            logger.info("JudgeAgent run completed.")
        except Exception as e:
            logger.error(f"JudgeAgent run error: {e}")
            raise
