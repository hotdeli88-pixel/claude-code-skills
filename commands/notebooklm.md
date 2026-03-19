---
name: notebooklm
description: "Google NotebookLM 노트북의 소스 기반 질의·검증 스킬. NotebookLM, 노트북, 소스 기반 질의, 소스 검색, CBCI 검증, 일반화 검증, source query, notebook query 등의 키워드로 호출. 업로드된 소스(PDF, 텍스트 등)를 대상으로 AI 기반 질의·검증을 수행한다."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Agent
argument-hint: "<notebook_id> <query or action>"
---

# NotebookLM 소스 기반 질의 스킬

## 개요

Google NotebookLM 노트북의 업로드된 소스(PDF, 텍스트 등)를 대상으로 AI 기반 질의·검증을 수행한다. CBCI 단원설계 검증, 일반화 진술 검증, 교육 자료 탐색 등에 활용.

## 사용법

```
/notebooklm <notebook_id> query "질문 내용"
/notebooklm <notebook_id> sources
/notebooklm <notebook_id> verify "일반화 진술문"
/notebooklm <notebook_id> content <source_id>
```

## 환경 설정

- Python venv: `/home/sdm24/notebooklm-server/venv/`
- Helper script: `/home/sdm24/notebooklm-server/nlm_helper.py`
- Auth profile: `~/.notebooklm-mcp-cli/profiles/default/`
- 인증 만료 시: `nlm login` 실행하여 재인증

## 실행 방법

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py <action> <args...>
```

## 액션 목록

### query — 소스 기반 질의

노트북에 업로드된 소스를 기반으로 AI가 답변.

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py query <notebook_id> "질문"
```

### sources — 소스 목록 조회

노트북에 포함된 소스 목록(ID, 제목, 유형) 반환.

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py sources <notebook_id>
```

### content — 소스 원문 추출

특정 소스의 원문 텍스트를 추출.

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py content <notebook_id> <source_id>
```

### verify-generalization — 일반화 검증 (CBCI 특화)

일반화 진술이 CBCI 기준(보편성, 추상성, 초월성)에 부합하는지 소스 기반으로 평가.

- rjcbci 스킬의 Agent B2가 사용자 수정 일반화를 재검증할 때 호출
- 소스에 CBCI 공식 가이드가 업로드되어 있으면 근거 기반 판정 가능

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py verify-generalization <notebook_id> "일반화 진술문"
```

### multi-query — 복수 질의

여러 질문을 순차 실행하여 통합 결과 반환.

```bash
/home/sdm24/notebooklm-server/venv/bin/python /home/sdm24/notebooklm-server/nlm_helper.py multi-query <notebook_id> "질문1" "질문2" "질문3"
```

## 출력 형식

모든 응답은 JSON:

```json
{"status": "ok", "answer": "...", "sources_cited": [...]}
```

```json
{"status": "error", "message": "...", "code": "AUTH_EXPIRED"}
```

## 다른 스킬과의 연동

- **rjcbci**: Agent B2 재검증 시 `verify-generalization` 호출
- **cbci-unit-design**: 설계 중 소스 참조
- 독립 실행도 가능

## 인증 관리

1. 최초: `/home/sdm24/notebooklm-server/venv/bin/nlm login`
2. 만료 시: 동일 명령 재실행
3. 프로필 확인: `ls ~/.notebooklm-mcp-cli/profiles/default/`

## 주의사항

1. NotebookLM 노트북에 관련 소스가 미리 업로드되어 있어야 함
2. 인증 만료 시 AUTH_EXPIRED 에러 → `nlm login` 안내
3. 쿼리 타임아웃: 120초 (대용량 소스 시 지연 가능)
4. notebook_id는 NotebookLM URL에서 확인 가능 (notebooklm.google.com/notebook/...)
