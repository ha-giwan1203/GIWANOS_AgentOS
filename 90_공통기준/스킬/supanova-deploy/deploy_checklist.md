# supanova-deploy 체크리스트

## 사전 준비
- [ ] supanova-deploy.skill GitHub URL 로드 확인
- [ ] Pinterest 레퍼런스 이미지 5장 이상 수집
- [ ] Gemini Pro 플랜 접근 가능 확인
- [ ] 결합할 템플릿 HTML 보유 확인
- [ ] 출력 폴더명 확정

## Gemini 영상 생성
- [ ] 비디오 생성 모드 (Tools → 동영상 만들기) 진입 확인
- [ ] Pro 모델 선택 확인
- [ ] 16:9 비율 설정 확인
- [ ] 결과 영상 다운로드 완료

## Claude Code 후처리
- [ ] 영상 파일 Claude Code에 드래그앤드롭
- [ ] 지시문에 "WebP 프레임 시퀀스 변환" 명시
- [ ] 지시문에 "/frames 폴더 저장" 명시
- [ ] 지시문에 "부드러운 애니메이션" 명시
- [ ] 상대경로 기준 구성 요청

## 산출물 구조 검증
- [ ] index.html 존재
- [ ] assets/ 존재 (css/, js/, img/)
- [ ] frames/ 존재
- [ ] 프레임 파일 1개 이상
- [ ] 파일명 연속성 확인 (0001.webp, 0002.webp, ...)
- [ ] 절대경로 참조 없음

## 로컬 실행 검증
- [ ] 브라우저 첫 화면 정상 로드
- [ ] 스크롤 시 프레임 전환 동작
- [ ] 404 없음
- [ ] 콘솔 치명 에러 없음

## 배포
- [ ] Netlify Drop: ZIP 아닌 output 폴더 업로드
- [ ] 배포 URL 기록
- [ ] URL 성격 기록 (검수용 임시 / 운영)
- [ ] README_deploy.txt 작성 완료
