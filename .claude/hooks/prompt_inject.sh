#!/bin/bash
# UserPromptSubmit hook — 도메인 키워드 감지 시 CLAUDE.md 경로 + 체크리스트 자동 주입
# 정책: domain_guard_config.yaml (단일 기준)
# v2: bash 변수 경유 제거 — stdin JSON을 Python에서 직접 처리 (cp949 인코딩 깨짐 방지)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
hook_log "UserPromptSubmit" "prompt_inject 발화"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/../logs"
mkdir -p "$LOG_DIR" 2>/dev/null

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# 전체 처리를 단일 Python 호출로 통합 (bash 변수 경유 없음, 인코딩 안전)
RESULT=$(echo "$INPUT" | PYTHONIOENCODING=utf-8 python3 -c "
import yaml, re, sys, json, os

# stdin에서 직접 JSON 읽기 (bash 변수 경유 없음)
try:
    raw = sys.stdin.buffer.read()
    data = json.loads(raw.decode('utf-8'))
    prompt = data.get('prompt', '')
except:
    sys.exit(0)

if not prompt:
    sys.exit(0)

config_path = sys.argv[1]
log_dir = sys.argv[2]

# 감사 로그
import datetime
ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
with open(os.path.join(log_dir, 'prompt_inject_audit.log'), 'a', encoding='utf-8') as f:
    f.write(f'[{ts}] prompt_inject fired | prompt_len={len(prompt)} | prompt_head={prompt[:80]}\n')

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
    # 2단 조합 패턴
    combos = d.get('keyword_combos', [])
    for combo in combos:
        if all(re.search(re.escape(w), prompt, re.IGNORECASE) for w in combo):
            matched = (name, d)
            break
    if matched:
        break

if not matched:
    with open(os.path.join(log_dir, 'prompt_inject_audit.log'), 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] no domain matched\n')
    sys.exit(0)

name, d = matched
claude_path = d.get('claude_path', '')
flag_prefix = d.get('flag_prefix', '')

# 플래그 생성 + 다른 도메인 cleanup
if flag_prefix:
    for other_name, other_d in domains.items():
        if other_name == name:
            continue
        other_prefix = other_d.get('flag_prefix', '')
        if other_prefix:
            for suffix in ('_active', '_loaded', '_phase'):
                try:
                    os.remove(other_prefix + suffix)
                except FileNotFoundError:
                    pass

    # 같은 도메인이 이미 활성이면 _loaded/_phase 유지 (세션 내 재초기화 방지)
    already_active = False
    try:
        with open(flag_prefix + '_active', 'r') as f:
            already_active = (f.read().strip() == name)
    except FileNotFoundError:
        pass

    with open(flag_prefix + '_active', 'w') as f:
        f.write(name)

    if not already_active:
        for suffix in ('_loaded', '_phase'):
            try:
                os.remove(flag_prefix + suffix)
            except FileNotFoundError:
                pass

# additionalContext 구성
entry_path = d.get('entry_path', '')
if entry_path:
    ctx_lines = [
        f'[Hook 자동 주입] 도메인 진입 순서: ①{entry_path} → ②{claude_path}',
        '→ ENTRY.md를 먼저 읽고, CLAUDE.md를 읽어야 도구가 해제됩니다.',
        '→ 순서를 지키지 않으면 domain_guard가 모든 도구를 차단합니다.'
    ]
else:
    ctx_lines = [
        f'[Hook 자동 주입] 도메인 로드 필수: {claude_path}',
        '→ 이 문서에 명시된 규칙·selector·입력방식을 읽기 전 임의 실행 금지.'
    ]

# 도메인별 Active Laws
domain_laws = {
    'debate': [
        '',
        '토론모드 Active Laws (NEVER):',
        '1. JS입력만(execCommand) — 클립보드/form_input/DataTransfer 금지',
        '2. [data-testid=\"send-button\"] JS클릭만 — ref클릭 금지',
        '3. 하네스 분석 필수 — 채택/보류/버림 누락 금지',
        '4. 프로젝트방만 — 새 대화 개설 금지',
        '5. SEND GATE: 전송 직전 assistant 최신 텍스트 재읽기 → 변경 시 재계산 필수 — 생략 금지'
    ],
    'settlement': [
        '',
        '정산 Preflight Laws (NEVER):',
        '1. 이번 월 권위값 확인 — 3월=GERP원본, 4월+=기준정보',
        '2. 동일품번 다중단가 정상 — 대표단가 1개로 덮기 금지',
        '3. 매칭키 = (라인, 품번, 조립품번) 3중키 — (라인,품번)만 사용 금지',
        '4. 기준정보 수정 전 백업 확인 + 적용 범위 명시',
        '5. 구조(시트/컬럼/다중행) 보존 우선 — 값만 수정'
    ],
    'linebatch': [
        '',
        '→ 라인코드·품번규칙·ERP 입력방식이 이 문서에 명시됨.'
    ],
    'mes_upload': [
        '',
        '→ MES API URL·iframe jQuery 강제·중복확인·COL매핑·안전원칙이 이 문서에 명시됨.',
        '→ fetch 사용 금지, iframe 내부 \$.ajax 필수, 당일 데이터 제외 원칙 확인 필수.'
    ],
    'zdm_inspection': [
        '',
        '→ ZDM 시스템 일상점검 입력 도메인. API 직호출 방식(CDP Playwright 경유).',
        '→ SP3M3 라인 19개 점검표, 75개 항목/일. POST /api/daily-inspection/{id}/record 사용.',
        '→ 실행 전 SKILL.md의 API 스펙·금지사항 필수 확인.'
    ],
    'youtube_analysis': [
        '',
        '→ youtube-analysis 스킬 수동/자동 모드 SKILL.md 참조.',
        '→ 자막 추출: youtube_transcript.py 스크립트 사용 필수.',
        '→ 분석 관점 9개 + A/B/C 판정 + 교차검증 절차를 따를 것.',
        '→ URL 포함 시 수동 모드, URL 없이 \"영상분석\"만 입력 시 자동 모드.'
    ]
}

if name in domain_laws:
    ctx_lines.extend(domain_laws[name])

output = {'additionalContext': '\n'.join(ctx_lines)}
result_json = json.dumps(output, ensure_ascii=False)

with open(os.path.join(log_dir, 'prompt_inject_audit.log'), 'a', encoding='utf-8') as f:
    f.write(f'[{ts}] matched={name} | result_len={len(result_json)}\n')

print(result_json)
" "$CONFIG" "$LOG_DIR" 2>>"$LOG_DIR/prompt_inject_debug.log")

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
