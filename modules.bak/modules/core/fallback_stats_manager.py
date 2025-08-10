"""
File: C:/giwanos/core/fallback_stats_manager.py

설명:
- evaluate_context 호출 시 통계(전체 평가, fallback 연속 카운터, 총 fallback, 신뢰도 합계)를 기록
- consecutive_fallbacks, last_was_fallback 필드 추가
- 연속 fallback 기준 초과 시 generate_rules() 트리거
"""

import os
import json
from pathlib import Path
from core.judgment_rules_manager import generate_rules
from core.tool_manager import ToolManager

STATS_PATH = Path(os.getenv('GIWANOS_ROOT', 'C:/giwanos')) / 'config' / 'fallback_stats.json'
CONSECUTIVE_THRESHOLD = 3

def load_stats() -> dict:
    if not STATS_PATH.exists():
        init = {
            "evaluations": 0,
            "fallbacks": 0,
            "sum_confidence": 0.0,
            "consecutive_fallbacks": 0,
            "last_was_fallback": False
        }
        save_stats(init)
        return init
    return json.loads(STATS_PATH.read_text(encoding='utf-8'))

def save_stats(stats: dict):
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def record_evaluation(confidence: float, used_fallback: bool):
    stats = load_stats()
    stats['evaluations'] += 1
    stats['sum_confidence'] += confidence
    # consecutive logic
    if used_fallback:
        stats['fallbacks'] += 1
        stats['consecutive_fallbacks'] = stats.get('consecutive_fallbacks', 0) + 1
    else:
        stats['consecutive_fallbacks'] = 0
    stats['last_was_fallback'] = used_fallback
    save_stats(stats)

    # trigger regeneration if threshold exceeded
    if stats['consecutive_fallbacks'] >= CONSECUTIVE_THRESHOLD:
        ToolManager.send_notification(
            f"Consecutive fallback threshold reached ({stats['consecutive_fallbacks']}), regenerating rules."
        )
        generate_rules()
        # reset consecutive counter after regeneration
        stats['consecutive_fallbacks'] = 0
        stats['last_was_fallback'] = False
        save_stats(stats)


