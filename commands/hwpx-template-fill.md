---
name: hwpx-template-fill
description: "HWPX/HWP 템플릿에 콘텐츠 소스 파일(DOCX, PDF, TXT, MD, JSON 등)의 데이터를 자동 매핑하여 채워넣는 스킬. 템플릿의 레이블 셀과 값 셀을 자동 분석하고, 소스에서 추출한 데이터를 매핑한다. '템플릿 채우기', '양식 작성', 'template fill', '서식 채우기', 'HWPX 양식에 내용 넣기', '문서 자동 작성' 등의 키워드로 호출."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Agent, ToolSearch, AskUserQuestion
argument-hint: "<HWPX템플릿경로> <콘텐츠소스파일경로>"
---

# HWPX 템플릿 채우기 스킬

## 개요

HWPX/HWP 양식 템플릿과 콘텐츠 소스 파일(DOCX, PDF, TXT, MD, JSON 등)을 받아, 템플릿 구조를 분석하고 소스 내용을 자동 매핑하여 완성된 HWPX 문서를 생성한다.

**핵심 전략**: MCP 우선(스타일 보존) + lxml 폴백(구조 변경 필요 시)

## 지원 소스 형식

| 형식 | 추출 방법 |
|------|-----------|
| DOCX | python-docx로 표/단락 추출 |
| PDF | Read 도구로 읽기 (페이지별) |
| TXT/MD | Read 도구 + 구조 파싱 |
| JSON | 직접 로드 |
| CSV | csv 모듈로 파싱 |
| 이미지 | Read 도구 (멀티모달) |

## 워크플로우 (6단계)

```
[Phase 0] 입력 검증 및 환경 설정
[Phase 1] 템플릿 구조 분석        ← Agent A (병렬)
[Phase 2] 콘텐츠 추출             ← Agent B (병렬, A와 동시)
[Phase 3] 콘텐츠-템플릿 매핑      ← A,B 완료 후
[Phase 4] 템플릿 채우기           ← MCP tools 사용
[Phase 5] 검증 및 저장
```

---

## Phase 0: 입력 검증

1. 인자 파싱: `<HWPX템플릿경로> <콘텐츠소스파일경로>`
2. 파일 존재 확인
3. 소스 파일 형식 판별 (확장자 기반)
4. 출력 파일명 결정: `{소스파일명}_완성.hwpx`

**인자가 없으면** AskUserQuestion으로 경로를 물어본다.

---

## Phase 1: 템플릿 구조 분석

hwpx MCP 도구를 사용하여 템플릿의 표 구조를 완전히 분석한다.

### 필수 MCP 도구 로드

```
ToolSearch("select:mcp__hwpx-mcp__open_document,mcp__hwpx-mcp__get_table_map,mcp__hwpx-mcp__get_tables_summary,mcp__hwpx-mcp__get_table_as_csv,mcp__hwpx-mcp__get_table_cell")
ToolSearch("select:mcp__hwpx-mcp__update_table_cell,mcp__hwpx-mcp__batch_fill_table,mcp__hwpx-mcp__save_document,mcp__hwpx-mcp__get_document_text")
```

### 분석 순서

1. **문서 열기**: `open_document(file_path)` → doc_id 획득
2. **표 목록 조회**: `get_table_map(doc_id)` → 전체 표 개요
3. **표별 CSV 추출**: `get_table_as_csv(doc_id, section, table)` → 각 표 내용 확인
4. **셀 분류**: 각 표의 셀을 label(헤더) vs value(빈칸/플레이스홀더)로 분류

### 셀 분류 규칙

| 구분 | 판별 기준 |
|------|-----------|
| **Label 셀** | 텍스트 있음 + (col 0 또는 row 0) + 배경색 있음(`#D8E5F5` 등) |
| **Value 셀** | 빈 문자열, 또는 플레이스홀더(`___`, `(입력)`, `□`, `차시`) |
| **Header 행** | 모든 셀이 Label인 행 (표의 열 제목) |
| **구조 셀** | 병합(colSpan/rowSpan > 1)된 장식/구분 셀 |

### 표 유형 분류

- **key_value**: Label-Value 쌍으로 구성 (양식 필드형)
- **data_grid**: 헤더행 + 데이터행 (표 형태)
- **section_header**: 단일행 제목/구분 표
- **mixed**: 위 유형이 혼합된 복합 표

### 출력: 템플릿 맵

분석 결과를 구조화된 형태로 정리:

```
템플릿 분석 결과:
  표 0 (1x3): section_header — "Ⅳ 전북형 개념 기반 탐구학습 설계 실습"
  표 1 (1x8): key_value — 학년[C1], 교과[C3], 운영유형[C5], 학습모형[C7]
  표 2 (15x4): mixed — 단원명[R0C1], 학생상[R1C1], ...소주제[R7-9], 평가[R12-14]
  표 3 (8x6): key_value — 소주제일반화[R1C1], 탐구질문[R2C1]
  표 4 (5x4): data_grid — 탐구단계|차시|교수학습활동|비고
  ...
```

---

## Phase 2: 콘텐츠 추출

소스 파일에서 구조화된 데이터를 추출한다. **Phase 1과 병렬 실행 가능.**

### DOCX 추출 (python-docx)

```python
# Bash로 실행
python -c "
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document

doc = Document('소스파일.docx')

# 모든 표 추출
for i, table in enumerate(doc.tables):
    print(f'=== TABLE {i} ({len(table.rows)}x{len(table.columns)}) ===')
    for r, row in enumerate(table.rows):
        cells = [cell.text.strip().replace(chr(10), ' | ') for cell in row.cells]
        print(f'  Row {r}: {cells}')
    print()

# 모든 단락 추출 (필요시)
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        style = para.style.name if para.style else 'Normal'
        print(f'PARA {i} [{style}]: {para.text.strip()[:200]}')
" 2>&1
```

### PDF 추출

```
Read(file_path="소스.pdf", pages="1-5")  # 페이지별 읽기
```

### TXT/MD 추출

```
Read(file_path="소스.md")  # 직접 읽기
```

### 추출 데이터 정리

소스에서 추출한 데이터를 **label → value** 딕셔너리로 정리:

```
추출 결과:
  "단원명" → "이차방정식의 판별식과 이차함수의 관계"
  "교과/학년" → "공통수학1 / 고등학교 1학년"
  "핵심개념" → "관계(주) + 변화(보조) + 형태(보조)"
  "총 차시" → "12차시"
  ...
  [표 데이터] → 소주제 개요 3행, 탐구질문 10행, 평가계획 4행, 활동 12행
```

---

## Phase 3: 콘텐츠-템플릿 매핑

추출된 콘텐츠를 템플릿의 각 value 셀에 매핑한다.

### 매핑 전략 (우선순위)

1. **정확 일치**: 템플릿 label == 소스 key (예: "단원명" == "단원명")
2. **부분 일치**: 템플릿 label ⊂ 소스 key (예: "학년" ∈ "교과/학년")
3. **동의어 매핑**: 사전 기반 (예: "핵심 기능" ↔ "핵심 역량", "총 차시" ↔ "전체 차시")
4. **구조 매핑**: data_grid 표 ↔ 소스 표 (헤더 매칭)
5. **AI 추론**: 위 방법 실패 시 내용 기반 추론

### 동의어 사전 (확장 가능)

```
"학년" ↔ "교과/학년", "학년/교과"
"핵심 개념" ↔ "핵심개념(렌즈)", "핵심 개념(렌즈)"
"핵심 기능" ↔ "핵심 역량", "핵심역량"
"전체 차시" ↔ "총 차시", "차시 수"
"일반화" ↔ "단원 일반화"
"핵심 질문" ↔ "단원 핵심질문", "핵심질문"
```

### 매핑 결과 제시

매핑 결과를 사용자에게 보여주고 확인을 받는다:

```
=== 매핑 결과 ===
✓ 단원명 → "이차방정식의 판별식과 이차함수의 관계"
✓ 학년 → "고등학교 1학년"  (부분일치: "교과/학년"에서 추출)
✓ 교과 → "공통수학1"  (부분일치: "교과/학년"에서 추출)
✓ 핵심 개념 → "관계(주) + 변화(보조) + 형태(보조)"
...
⚠ 학생상 → (소스에 없음, AI 추론으로 생성)
⚠ 핵심 가치 → (소스에 없음, AI 추론으로 생성)

진행하시겠습니까? (수정할 항목이 있으면 알려주세요)
```

### 누락 필드 처리

- 소스에 없는 템플릿 필드: AI가 문맥 기반으로 생성하거나 사용자에게 물어봄
- 소스에 있지만 템플릿에 없는 데이터: 무시 (보고만 함)
- 체크박스(□/☑): 소스 내용에 따라 자동 체크

---

## Phase 4: 템플릿 채우기

확정된 매핑을 기반으로 MCP 도구를 사용하여 템플릿을 채운다.

### 채우기 전략

#### A. 개별 셀 채우기 (key_value 유형)

```
update_table_cell(doc_id, section_index, table_index, row, col, text=value)
```

- 스타일이 자동 보존됨 (charPrIDRef, paraPrIDRef 유지)
- 자동 들여쓰기(hanging indent) 적용: ▫, -, •, ◆ 등 마커 감지 시

#### B. 일괄 채우기 (data_grid 유형)

```
batch_fill_table(doc_id, table_index, data=[[...], [...]], start_row=N, start_col=M)
```

- 헤더행은 건너뛰고 데이터행만 채움
- Label 열(col 0 등)은 건너뛰어야 할 경우 start_col 조정

#### C. 텍스트 치환 (비표 영역)

```
replace_text(doc_id, old_text="{{placeholder}}", new_text=value)
```

### 병렬 실행 (대규모 템플릿)

독립적인 표들은 **병렬 MCP 호출**로 동시에 채운다:

```
# 모든 update_table_cell / batch_fill_table 호출을
# 독립적이면 하나의 메시지에서 병렬로 실행
```

### 주의사항

- **병합 셀**: `get_table_cell`로 실제 colAddr 확인 후 정확한 col 인덱스 사용
- **outOfBounds**: batch_fill에서 병합된 행은 건너뛸 수 있음 → 개별 update_table_cell로 대체
- **줄바꿈**: 여러 줄 내용은 `\n`으로 구분
- **특수문자**: ☑, □, ◆, ▫, •, ≥, ≤ 등 유니코드 문자 직접 사용 가능

---

## Phase 5: 검증 및 저장

### 검증

1. **내용 확인**: 주요 셀을 `get_table_cell` 또는 `get_table_as_csv`로 다시 읽어 확인
2. **빈 셀 점검**: 채워야 할 value 셀 중 여전히 비어있는 것 확인
3. **잔여 텍스트 정리**: 템플릿 플레이스홀더가 남아있으면 `replace_text_in_cell`로 제거

### 저장

```
save_document(doc_id, output_path=출력경로, create_backup=true, verify_integrity=true)
```

### 결과 보고

```
=== 완성 결과 ===
  템플릿: {템플릿 파일명}
  소스: {소스 파일명}
  출력: {출력 파일명}
  채워진 필드: {N}/{M}개
  빈 필드: {목록 또는 "없음"}
  무결성 검증: PASS
```

---

## 오류 처리

| 오류 | 대응 |
|------|------|
| 템플릿 파일 없음 | AskUserQuestion으로 경로 확인 |
| MCP 서버 미작동 | ToolSearch로 MCP 도구 로드 재시도 |
| 소스 형식 불명 | AskUserQuestion으로 형식 확인 |
| 셀 인덱스 오류(outOfBounds) | get_table_cell로 실제 구조 확인 후 재시도 |
| 매핑 실패 (라벨 불일치) | AI 추론 또는 사용자 입력 |
| OneDrive 파일 잠금 | 다른 파일명으로 저장 |
| cp949 인코딩 오류 | Python stdout UTF-8 래퍼 적용 |

---

## 사용 예시

```
/hwpx-template-fill "설계 템플릿.hwpx" "이차방정식_단원설계.docx"
/hwpx-template-fill "보고서양식.hwpx" "내용정리.md"
/hwpx-template-fill "공문서식.hwpx" "데이터.json"
```

또는 자연어로:

```
"이 템플릿에 이 DOCX 내용 채워줘"
"양식 작성해줘"
"서식에 데이터 넣어줘"
```
