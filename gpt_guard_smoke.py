import os, sys, json
sys.path.append(r'C:\giwanos')

# 빠른 환경 검증
need = ['OPENAI_API_KEY', 'OPENAI_MODEL']
missing = [k for k in need if not os.getenv(k)]
if missing:
    raise SystemExit(f'[환경변수 누락] {missing}')

from modules.core.context_aware_decision_engine import generate_gpt_response_with_guard

print('[SMOKE] 모델:', os.getenv('OPENAI_MODEL'))
print('[SMOKE] 엔드포인트:', os.getenv('OPENAI_BASE_URL') or 'default')

try:
    out = generate_gpt_response_with_guard('상태 한 줄 요약', conversation_id='smoke-test')
    print('[OK] 응답:', (out[:200] + ' …') if len(out) > 200 else out)
except Exception as e:
    print('[FAIL] 호출 실패:', e)
    raise
