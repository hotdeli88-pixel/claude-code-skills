---
name: rjcbci Agent B2 재검증 루프
description: rjcbci 스킬의 Agent B2 수정→재검증 루프 및 NotebookLM 소스 참조 기능 추가 내역
type: project
---

rjcbci 스킬에 Agent B2 재검증 루프 + NotebookLM 연동 추가 (2026-03-19).

**Why:** Agent B가 제안한 일반화를 사용자가 수정할 때, 수정본의 CBCI 3요건(보편성·추상성·초월성) 적합성을 자동 재검증해야 한다. NotebookLM 소스와 대조하면 근거 기반 판정이 가능.

**How to apply:**
- rjcbci.md 변경: Step 0.5(노트북 선택 UI), Agent B ⑥(NLM 참조), Agent B2(재검증 루프 최대 3회), 주의사항 #6
- B2는 사용자가 수정한 경우에만 실행, 수락 시 건너뜀
- NLM 연동은 선택적 — 없어도 기존 워크플로우 정상 동작
