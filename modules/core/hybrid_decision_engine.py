"""
File: C:/giwanos/core/hybrid_decision_engine.py

설명:
- 로컬 룰 매칭 시 조건 기반 confidence와 의미 기반 similarity를 결합
- combined_score = ALPHA * confidence + (1-ALPHA) * similarity
- THRESHOLD 이상 시 로컬 사용, 그렇지 않으면 GPT fallback
- invalid rule entries 및 conditions 필터링
- fallback JSON 파싱 에러 안전 처리
- fallback actions normalization: 딕셔너리에서 action 키로 추출
- fallback_stats_manager를 통한 통계 기록
- EmbeddingManager 싱글톤 초기화
"""

import os
import json
import logging
from pathlib import Path
import openai

from core.judgment_rules_manager import load_rules, generate_rules
from core.fallback_stats_manager import record_evaluation
from core.embedding_manager import EmbeddingManager
from core.tool_manager import ToolManager

logger = logging.getLogger(__name__)

# 임계값 및 가중치 설정
THRESHOLD = 0.8
ALPHA = 0.5  # confidence와 similarity 가중치 비율

# EmbeddingManager 싱글톤
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        root = Path(__file__).resolve().parent.parent
        rules_path = root / 'config' / 'judgment_rules.json'
        _embedder = EmbeddingManager(rules_path)
    return _embedder


def evaluate_context(context: dict) -> dict:
    """
    로컬 rules에 대해 결합 점수로 매칭 시도;
    실패 시 GPT fallback 및 캐싱
    """
    rules = load_rules()
    rules_list = rules if isinstance(rules, list) else [rules]

    # invalid rule entries 필터링
    valid_rules = [r for r in rules_list if isinstance(r, dict)]
    if len(valid_rules) < len(rules_list):
        logger.warning(f"Ignored {len(rules_list) - len(valid_rules)} invalid rule entries.")
    rules_list = valid_rules

    # 조건 기반 confidence 계산
    cond_confidences = {}
    for rule in rules_list:
        conditions = rule.get('conditions', {})
        if not isinstance(conditions, dict):
            continue
        total = len(conditions)
        matched = 0
        for key, cond in conditions.items():
            if not isinstance(cond, dict):
                continue
            val = context.get(key)
            if cond.get('operator') == '>=' and isinstance(val, (int, float)) and val >= cond.get('value'):
                matched += 1
        conf = matched / total if total > 0 else 0.0
        cond_confidences[id(rule)] = conf
        record_evaluation(conf, False)

    # 의미 기반 similarity 계산
    embedder = _get_embedder()
    similar = embedder.query_similar_rules(context, top_k=len(rules_list))
    sim_map = {id(item['rule']): item['similarity'] for item in similar}

    # 결합 점수로 매칭
    matched_rules = []
    for rule in rules_list:
        cid = id(rule)
        conf = cond_confidences.get(cid, 0.0)
        sim = sim_map.get(cid, 0.0)
        combined = ALPHA * conf + (1 - ALPHA) * sim
        if combined >= THRESHOLD:
            matched_rules.append(rule)

    if matched_rules:
        actions = []
        for r in matched_rules:
            actions += r.get('actions', [])
        return {'matched_rules': matched_rules, 'actions': list(set(actions)), 'used_fallback': False}

    # fallback 시나리오
    logger.info('Combined match failed, invoking GPT fallback')
    prompt = (
        '다음 context에 기반해 필요한 판단 규칙과 actions를 JSON으로 제안해주세요.\n'
        f'Context: {json.dumps(context, ensure_ascii=False)}\n'
        "JSON 형식: { 'id': ..., 'conditions': {...}, 'actions': [...], 'tool': {...} }"
    )
    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a decision assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    # JSON 스니펫 추출
    if content.startswith('```'):
        parts = content.split('```')
        if len(parts) >= 2:
            content = parts[1]
    start = content.find('{')
    end = content.rfind('}') + 1
    json_str = content[start:end] if start != -1 and end != 0 else content
    try:
        new_rule = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error('Fallback JSON parse error: %s', e)
        ToolManager.send_notification(f'Fallback parse error: {e}')
        return {'matched_rules': [], 'actions': [], 'used_fallback': True, 'tool': None}

    record_evaluation(0.0, True)

    # 캐싱
    config_path = Path(os.getenv('GIWANOS_ROOT', 'C:/giwanos')) / 'config' / 'judgment_rules.json'
    try:
        existing = json.loads(config_path.read_text(encoding='utf-8'))
        existing_list = existing if isinstance(existing, list) else [existing]
        existing_list.append(new_rule)
        config_path.write_text(json.dumps(existing_list, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info('New rule cached in judgment_rules.json')
    except Exception as e:
        logger.error('Failed to cache new rule: %s', e)

    # Fallback actions normalization: extract action names
    raw_actions = new_rule.get('actions', [])
    actions = []
    for act in raw_actions:
        if isinstance(act, dict) and 'action' in act:
            actions.append(act['action'])
        elif isinstance(act, str):
            actions.append(act)

    return {'matched_rules': [], 'actions': actions, 'used_fallback': True, 'tool': new_rule.get('tool')}
