---
name: NotebookLM 연동 체계
description: NotebookLM MCP CLI 기반 소스 질의 스킬 구성 — rjcbci 연동, 인증 구조, 헬퍼 스크립트
type: reference
---

## NotebookLM 스킬 구성

| 구성요소 | 위치 | 용도 |
|----------|------|------|
| notebooklm 스킬 | `~/.claude/commands/notebooklm.md` | `/notebooklm` 명령 정의 |
| nlm_helper.py | `/home/sdm24/notebooklm-server/nlm_helper.py` | 6개 액션 래퍼 (check-auth, query, sources, content, verify-generalization, multi-query) |
| Python venv | `/home/sdm24/notebooklm-server/venv/` | notebooklm-mcp-cli v0.5.0 |
| 인증 프로필 | `~/.notebooklm-mcp-cli/profiles/default/` | cookies.json + metadata.json |

## 인증 구조

- Google 브라우저 쿠키 기반 (공식 API 없음, 리버스 엔지니어링)
- 쿠키 유효: ~1년 (서버측 무효화 시 수 주~수 개월)
- 인증 만료 시: `nlm login` 실행 (Chrome 필요)
- WSL2에서 Windows Chrome 접근: CDP(Chrome DevTools Protocol) + PowerShell 경유
- `nlm_helper.py check-auth`로 무음 확인, 프로세스 내 캐시

## rjcbci 연동

- Step 0.5에서 대화형으로 노트북 선택 (CBCI 키워드 필터링 추천)
- Agent B: ⑥ NLM 소스 참조 (일반화 설계 근거)
- Agent B2: verify-generalization (수정 일반화 소스 대조 검증)
- NLM 연동 실패해도 검증 워크플로우 중단 안 함

## 계정

- hotdeli88@gmail.com
- CBCI 노트북: `1a7876bb-6a1e-4e92-a6a1-72c9050bc5f5` (Jeonbuk Middle School Concept-Based Inquiry Design Cases)
