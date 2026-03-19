# Auto Memory

## HWPX 테마/스타일 변경 패턴

문서 전체의 색상·글꼴·테두리 스타일을 일괄 변경하는 워크플로우. 상세: [hwpx-theme-pattern.md](hwpx-theme-pattern.md)

- 워크플로우: header.xml 분석 → 새 borderFill/charPr 정의 추가 → section0.xml에서 ID 참조 교체
- 핵심: 테이블 유형별로 구분하여 정밀 타겟팅 (colCnt + tbl의 borderFillIDRef로 구분)
- 참조 스크립트: `improve_hwpx_style.py` (26.03.11 디지털선도학교 계획서 디렉토리)
- 공문서 색상 프리셋: `#1B3A5C` (딥 네이비), `#E8EDF2` (연회색), `#8C9BAA` (중간회색), `#333333` (본문)

## HWPX 스킬 체계

| 스킬 | 위치 | 용도 |
|------|------|------|
| hwpx | `~/.claude/commands/hwpx.md` | 텍스트 치환 중심 생성·편집 |
| hwpx-table-format | `~/.claude/commands/hwpx-table-format.md` | 표 셀서식 통일 (lxml) |
| hwpx-template-fill | `~/.claude/commands/hwpx-template-fill.md` | 템플릿에 데이터 매핑 (MCP) |

스킬 에셋: `/mnt/c/Users/sdm24/.claude/skills/hwpx/` (SKILL.md, assets/, references/, scripts/)

## NotebookLM 연동 체계

NotebookLM 소스 기반 질의·검증 스킬 및 rjcbci 연동. 상세: [notebooklm-integration.md](notebooklm-integration.md)

- 스킬: `~/.claude/commands/notebooklm.md`, 헬퍼: `/home/sdm24/notebooklm-server/nlm_helper.py`
- 인증: Google 쿠키 기반, `~/.notebooklm-mcp-cli/profiles/default/`
- CBCI 노트북: `1a7876bb-...` (Jeonbuk Middle School Concept-Based Inquiry)

## rjcbci B2 재검증 루프

Agent B2 수정→재검증 + NLM 소스 대조. 상세: [rjcbci-b2-loop.md](rjcbci-b2-loop.md)

- Step 0.5: 대화형 노트북 선택 (CBCI 키워드 필터 추천)
- Agent B2: 사용자 수정 일반화 재검증 (최대 3회, NLM verify-generalization)

## 사용자 환경

- WSL2 + Windows, OneDrive 경로 사용
- python3 (pip install python-hwpx)
- 한글과컴퓨터 한글 사용
- 학교 업무 문서 (계획서, 보고서, 공문) 자주 작업
