#!/bin/bash
# UserPromptSubmit hook — 도메인 키워드 감지 시 CLAUDE.md 경로 + 체크리스트 자동 주입
# 정책: domain_guard_config.yaml (단일 기준)

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    obj = json.loads(sys.stdin.read())
    print(obj.get('prompt', ''))
except:
    pass
" 2>/dev/null)

# 실검증 로그: UserPromptSubmit 발동 확인
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/../logs"
mkdir -p "$LOG_DIR" 2>/dev/null
echo "[$(date '+%Y-%m-%d %H:%M:%S')] prompt_inject fired | prompt_len=${#PROMPT} | prompt_head=$(echo "$PROMPT" | head -c 80)" >> "$LOG_DIR/prompt_inject_audit.log"

if [ -z "$PROMPT" ]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python으로 YAML 파싱 + 키워드 매칭 + JSON 출력
RESULT=$(python3 -c "
import yaml, re, sys, json

config_path = sys.argv[1]
prompt = sys.argv[2]

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

domains = cfg.get('domains', {})
matched = None

for name, d in domains.items():
    keywords = d.get('keywords', [])
    pattern = '|'.join(re.escape(k) for k in keywords)
    if pattern and re.search(pattern, prompt, re.IGNORECASE):
        matched = (name, d)
        break

if not matched:
    sys.exit(0)

name, d = matched
claude_path = d.get('claude_path', '')
flag_prefix = d.get('flag_prefix', '')

# 플래그 생성 (active 설정, loaded 초기화) + 다른 도메인 플래그 cleanup
import os
if flag_prefix:
    # 다른 도메인의 active/loaded 플래그 정리 (도메인 전환 시 오염 방지)
    for other_name, other_d in domains.items():
        if other_name == name:
            continue
        other_prefix = other_d.get('flag_prefix', '')
        if other_prefix:
            for suffix in ('_active', '_loaded'):
                try:
                    os.remove(other_prefix + suffix)
                except FileNotFoundError:
                    pass

    # 현재 도메인 활성화
    with open(flag_prefix + '_active', 'w') as f:
        f.write(name)
    try:
        os.remove(flag_prefix + '_loaded')
    except FileNotFoundError:
        pass

# 도메인별 additionalContext 구성
ctx_lines = [
    f'[Hook 자동 주입] 도메인 로드 필수: {claude_path}',
    '→ 이 문서에 명시된 규칙·selector·입력방식을 읽기 전 임의 실행 금지.'
]

# 토론모드 전용 하네스 체크리스트
if name == 'debate':
    ctx_lines.extend([
        '',
        '토론모드/공동작업 하네스 체크리스트:',
        '1. GPT 응답 수신 후 반드시 주장 분해 → 라벨링(실증/일반론/환경미스매치/과잉) → 채택/보류/버림 판정 수행',
        '2. 반박문 첫 문단에 채택:/보류:/버림: 필수 포함. 버림 0건이면 재분해',
        '3. 사용자에게 중간 승인 요청 금지. 합의 후 즉시 실행 → GPT 공유 → 추가수정 루프',
        '4. 허용 문장: \"이 기준으로 바로 적용한다\", \"합의 반영 후 결과만 보고한다\"',
        '5. 입력 전 미확인 응답 점검 필수 (Step 1.5)'
    ])

if name == 'settlement':
    ctx_lines.extend([
        '',
        '→ 정산 파이프라인 규칙·단가 기준·검증 절차가 이 문서에 명시됨.'
    ])

if name == 'linebatch':
    ctx_lines.extend([
        '',
        '→ 라인코드·품번규칙·ERP 입력방식이 이 문서에 명시됨.'
    ])

if name == 'mes_upload':
    ctx_lines.extend([
        '',
        '→ MES API URL·iframe jQuery 강제·중복확인·COL매핑·안전원칙이 이 문서에 명시됨.',
        '→ fetch 사용 금지, iframe 내부 $.ajax 필수, 당일 데이터 제외 원칙 확인 필수.'
    ])

if name == 'zdm_inspection':
    ctx_lines.extend([
        '',
        '→ ZDM 시스템 일상점검 입력 도메인. API 직호출 방식(CDP Playwright 경유).',
        '→ SP3M3 라인 19개 점검표, 75개 항목/일. POST /api/daily-inspection/{id}/record 사용.',
        '→ 실행 전 SKILL.md의 API 스펙·금지사항 필수 확인.'
    ])

if name == 'youtube_analysis':
    ctx_lines.extend([
        '',
        '→ youtube-analysis 스킬 수동/자동 모드 SKILL.md 참조.',
        '→ 자막 추출: youtube_transcript.py 스크립트 사용 필수.',
        '→ 분석 관점 9개 + A/B/C 판정 + 교차검증 절차를 따를 것.',
        '→ URL 포함 시 수동 모드, URL 없이 "영상분석"만 입력 시 자동 모드.'
    ])

output = {'additionalContext': '\\n'.join(ctx_lines)}
print(json.dumps(output, ensure_ascii=False))
" "$CONFIG" "$PROMPT" 2>>"$LOG_DIR/prompt_inject_debug.log")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] config=$CONFIG | result_len=${#RESULT} | result=$(echo "$RESULT" | head -c 200)" >> "$LOG_DIR/prompt_inject_audit.log"

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
