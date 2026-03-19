---
name: cbci-worksheet
description: "CBCI 단원설계 기반 차시별 학습지(활동지) DOCX 생성 스킬. 단원설계 결과파일(탐구기법매핑, 활동설계, 핵심개념체계)을 읽어 학생용 활동지를 자동 생성한다. '학습지', '활동지', 'worksheet', '차시별 학습지', '학생용 활동지' 등의 키워드로 호출."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet, TeamCreate, TeamDelete, SendMessage, AskUserQuestion
argument-hint: "<작업 디렉터리 경로> [단원명]"
---

# CBCI 차시별 학습지(활동지) 생성 스킬

## 개요

전북형 개념기반 탐구학습(CBCI) 단원설계의 결과물을 기반으로, 학생이 직접 작성하는 차시별 학습지(활동지) DOCX를 자동 생성한다.

**입력**: 단원설계 결과파일 (활동설계, 탐구기법매핑, 핵심개념체계)
**출력**: `{단원명}_학습지_전체.docx` (전 차시 통합, 차시별 페이지 나눔)

## 사용법

```
/cbci-worksheet <작업 디렉터리> [단원명]
/cbci-worksheet .                          # 현재 디렉터리
/cbci-worksheet                            # 인자 없으면 질문
```

---

## 워크플로우 (6단계)

### Phase 0: 입력 확인 및 환경 준비

1. **작업 디렉터리 결정**: 인자에서 파싱. 없으면 현재 디렉터리 사용.

2. **결과파일 탐색**: 아래 패턴으로 자동 검색한다.
   ```
   Glob: **/result_task*.md, **/result_*.md, **/*활동설계*.md, **/*탐구기법*.md, **/*핵심개념*.md
   ```
   - `result_task1_탐구기법매핑.md` (또는 유사 파일) — 차시별 탐구단계·탐구기법·PYP 발문
   - `result_task2_활동설계.md` (또는 유사 파일) — 차시별 활동 상세 내용·표·발문
   - `result_task3_핵심개념체계.md` (또는 유사 파일) — 일반화 문장, 핵심질문

   결과파일이 없으면 사용자에게 경로를 질문한다.

3. **기존 단원설계 DOCX 탐색** (선택):
   ```
   Glob: **/*단원설계*.docx, **/*최종*.docx
   ```
   있으면 참고용으로 읽는다 (구조/차시 수 확인).

4. **단원명 결정**: 인자 또는 결과파일 내용에서 추출. 없으면 사용자에게 질문.

5. **python-docx 설치 확인**:
   ```bash
   python -c "import docx; print('OK')" 2>&1 || pip install python-docx
   ```

---

### Phase 1: 결과파일 분석

3개 결과파일을 Read로 읽고 다음을 추출한다:

#### 1-1. 활동설계 파일에서 추출 (가장 핵심)

| 추출 항목 | 설명 |
|-----------|------|
| 차시 구성 | 몇 차시인지, 결합 차시(2~3차시, 7~8차시 등)는 어떤 것인지 |
| 소주제 구분 | 소주제명, 소주제별 차시 범위 |
| 차시별 활동 | 활동 번호, 활동명, 활동 내용 (표/서술/빈칸 등) |
| 차시별 표 | 표의 헤더, 행 데이터, 열 수 |
| 차시별 발문 | [사실적], [개념적], [논쟁적] 발문 |
| 평가 문항 | ★ 평가 1/2/3의 문항 내용, 루브릭(있는 경우) |
| 성찰 양식 | 3-2-1 전략, 학습저널 위치 |

#### 1-2. 탐구기법매핑 파일에서 추출

| 추출 항목 | 설명 |
|-----------|------|
| 차시별 탐구단계 | 관계맺기, 집중하기, 조사하기 등 |
| 차시별 탐구기법 | 의견기반전략, 분류전략 등 |
| PYP 핵심개념 발문 | 형태, 기능, 원인 등 발문 |

#### 1-3. 핵심개념체계 파일에서 추출

| 추출 항목 | 설명 |
|-----------|------|
| 단원 일반화 | 전체 단원의 일반화 문장 |
| 소주제 일반화 | 소주제별 일반화 문장 (빈칸 문장 완성에 사용) |
| 핵심질문 | 단원/소주제별 핵심질문 |
| 탐구질문 종합 | 사실적/개념적/논쟁적 질문 목록 |

---

### Phase 2: 설계 확인 (사용자 질문)

AskUserQuestion으로 학습지 구성 옵션을 확인한다:

**질문 1: 출력 형식**
- DOCX (기본, Recommended)
- Markdown

**질문 2: 파일 구성**
- 전 차시 통합 1개 파일 (Recommended)
- 차시별 개별 파일

**질문 3: 포함 범위**
- 학생용 활동지만 (Recommended)
- 학생용 + 교사 가이드
- 학생용 + 교사 가이드 + 정답/예시 답안

---

### Phase 3: 스크립트 생성 (팀즈 활용 가능)

차시 수가 많으면(12차시 이상) 팀즈를 활용하여 병렬 작업한다.

#### 3-1. 팀 구성 (선택적 — 12차시 이상일 때)

```
팀 구조:
- 팀 리더 (나): 헬퍼 함수 작성, 메인 스크립트, 검증
- st{N}-worksheet (소주제 수만큼): 소주제별 차시 함수 작성
```

#### 3-2. 헬퍼 함수 모듈 (팀 리더 작성)

`_worksheet_helpers.py` 파일에 다음 12개 헬퍼 함수를 작성한다:

```python
# === 페이지 설정 ===
def setup_page(doc)
# A4 (210x297mm), 여백 상20/하20/좌25/우20mm

# === 텍스트 서식 ===
def _run(p, text, size=10, bold=False, italic=False, color=None, underline=False)
# 맑은 고딕, 지정 크기/스타일의 run 추가

# === 셀 배경색 ===
def set_cell_bg(cell, hex_color)
# w:shd 요소로 셀 배경 설정

# === 페이지 나눔 ===
def add_page_break(doc)
# w:br type="page" 삽입

# === 차시 헤더 ===
def add_lesson_header(doc, lesson_num, subtopic, stage, title)
# 1x1 표, 회색(#D9D9D9) 배경, 차시번호/소주제/탐구단계/제목
# 형식: "{차시}  |  {소주제}  |  {탐구단계}" + 제목(12pt Bold)

# === 섹션 라벨 ===
def add_section_label(doc, text, prefix='◆')
# ◆ 활동 N, ★ 평가 N 등 10.5pt Bold

# === 본문 텍스트 ===
def add_body(doc, text, indent=False)
# 10pt 본문, 선택적 0.5cm 들여쓰기

# === 표 생성 ===
def add_table(doc, headers, rows, col_widths=None)
# Table Grid 스타일, 헤더행 회색 음영, 9.5pt

# === 밑줄 응답 공간 ===
def add_blank_lines(doc, count=3, label=None)
# w:pBdr bottom으로 밑줄, 줄간 14pt after

# === 그리기 공간 ===
def add_diagram_box(doc, label, height_cm=4)
# 1x1 Table Grid, 지정 높이(trHeight), 안내 라벨 연회색

# === 빈칸 문장 완성 ===
def add_sentence_frame(doc, template)
# "(_____)" 를 밑줄 빈칸으로 변환

# === 발문 블록 ===
def add_questions(doc, qs)
# [(type_label, question_text), ...] → [사실적]/[개념적]/[논쟁적] 색상 구분

# === 3-2-1 성찰 ===
def add_reflection_321(doc)
# 3가지 알게 된 점 / 2가지 흥미로웠던 점 / 1가지 더 알고 싶은 점

# === 학습저널 ===
def add_learning_journal(doc)
# 가장 중요하게 배운 것 / 아직 궁금한 점

# === 구분선 ===
def add_divider(doc, label)
# ─── {label} ─── 형식
```

#### 3-3. 차시 함수 작성 규칙

각 차시(또는 결합 차시) 함수는 다음 구조를 따른다:

```python
def lesson_XX(doc):
    # 1) 차시 헤더
    add_lesson_header(doc, '{N}차시', '소주제{M}: {소주제명}',
                      '{탐구단계}', '{차시 제목}')

    # 2) 활동 섹션 (결과파일의 활동 내용 반영)
    add_section_label(doc, '활동 1: {활동명}')
    add_body(doc, '{활동 안내 텍스트}')
    # → 활동 유형에 따라 적절한 헬퍼 사용:
    #   - 표 작성: add_table()
    #   - 서술형 응답: add_blank_lines()
    #   - 그리기/도식: add_diagram_box()
    #   - 빈칸 문장: add_sentence_frame()

    # 3) 핵심 발문 (탐구기법매핑 파일의 PYP 발문 반영)
    add_questions(doc, [
        ('사실적', '...'),
        ('개념적', '...'),
        ('논쟁적', '...'),
    ])

    # 4) 성찰 (소주제 마지막 차시에만)
    # add_reflection_321(doc)
    # add_learning_journal(doc)

    # 5) 평가 (평가 차시에만)
    # add_section_label(doc, '평가 N', prefix='★')
```

#### 3-4. 차시 함수 → 학습지 요소 매핑 가이드

활동설계 내용을 학습지 요소로 변환하는 규칙:

| 활동설계 내용 | 학습지 요소 | 헬퍼 함수 |
|--------------|------------|----------|
| "~를 나열/분류/기록하세요" + 표 | 빈 표 (헤더만 채움, 데이터 행은 빈칸) | `add_table()` |
| "~를 설명/서술하세요" | 밑줄 응답 공간 | `add_blank_lines()` |
| "수형도/관계도/다이어그램을 그려 보세요" | 그리기 박스 | `add_diagram_box()` |
| "~의 빈칸을 채우세요" | 빈칸 문장 완성 | `add_sentence_frame()` |
| "~에 대해 비교하세요" | 교차비교차트 (표) | `add_table()` |
| 발문 (사실적/개념적/논쟁적) | 발문 블록 | `add_questions()` |
| 3-2-1 전략 | 3-2-1 성찰 양식 | `add_reflection_321()` |
| 학습저널 | 학습저널 양식 | `add_learning_journal()` |
| 실험 기록 | 기록표 (표) | `add_table()` |
| 루브릭 | 평가 루브릭 표 | `add_table()` |

#### 3-5. 결합 차시 처리

2개 이상의 차시가 결합된 경우:
- 함수명: `lesson_02_03()`, `lesson_07_08()` 등
- `add_divider(doc, 'N차시')` 로 차시 내 구분
- 헤더의 차시번호: `'2~3차시'` 형식

---

### Phase 4: 메인 스크립트 조립 및 실행

#### 4-1. 메인 스크립트 구조

`generate_worksheets.py` (또는 `generate_{단원명}_학습지.py`) 파일:

```python
# -*- coding: utf-8 -*-
"""
{N}차시 학습지(활동지) DOCX 생성 스크립트
{단원명} — 전북형 개념기반 탐구학습
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT = '{단원명}_학습지_전체.docx'
doc = Document()

# ── 헬퍼 함수 (12개) ──
# ... (Phase 3-2의 함수들)

# ── 차시 함수 ({K}개) ──
# ... (Phase 3-3~3-5의 함수들)

# ── 메인 실행 ──
def main():
    setup_page()
    lessons = [lesson_01, lesson_02_03, ...]  # 차시 함수 목록
    for i, fn in enumerate(lessons):
        fn()
        if i < len(lessons) - 1:
            add_page_break()
        print(f'[OK] {fn.__name__}')
    doc.save(OUTPUT)
    print(f'\n저장 완료: {OUTPUT}')

if __name__ == '__main__':
    main()
```

#### 4-2. 팀즈 활용 시

소주제별 에이전트가 각각 차시 함수 코드 블록을 작성하여 결과를 리더에게 전달한다.
리더는 헬퍼 함수 + 차시 함수들 + main() 을 하나의 스크립트로 조립한다.

```
에이전트 프롬프트 핵심:
- 헬퍼 함수 시그니처와 사용법 전달
- 해당 소주제의 결과파일 내용 전달
- "차시 함수 코드만 작성하여 반환" 지시
- 변환 규칙(Phase 3-4) 전달
```

#### 4-3. 실행

```bash
cd "작업 디렉터리" && python generate_worksheets.py
```

---

### Phase 5: 검증

생성된 DOCX를 python-docx로 읽어 검증한다:

```python
from docx import Document
doc = Document('{출력파일}.docx')

# 검증 항목:
# 1. 총 표 수 (차시별 활동 표 + 헤더 표 + 다이어그램 박스)
# 2. 페이지 나눔 수 (차시 함수 수 - 1)
# 3. 차시 헤더 내용 (소주제명, 탐구단계 정확성)
# 4. 핵심 표 내용 (패턴발견표, 실험기록표, 루브릭 등)
# 5. 발문 유형 균형 (사실적/개념적/논쟁적)
```

검증 결과를 표로 정리하여 사용자에게 보고한다.

---

### Phase 6: 정리 및 보고

1. 팀즈 사용 시: 에이전트 종료 + 팀 삭제
2. 최종 보고:
   - 생성 파일 경로 및 크기
   - 검증 결과 요약 (표 수, 페이지 나눔, 차시 구성)
   - 차시별 주요 학습지 요소 목록

---

## 서식 사양

| 요소 | 폰트 | 크기 | 스타일 |
|------|------|------|--------|
| 차시 헤더 (상단) | 맑은 고딕 | 9pt | Bold, 회색(`#D9D9D9`) 배경 |
| 차시 헤더 (제목) | 맑은 고딕 | 12pt | Bold |
| 섹션 라벨 | 맑은 고딕 | 10.5pt | Bold, ◆/★ 접두사 |
| 본문 | 맑은 고딕 | 10pt | Regular |
| 표 셀 | 맑은 고딕 | 9.5pt | Table Grid, 헤더행 음영 |
| 발문 유형 라벨 | 맑은 고딕 | 10pt | Bold, 파랑(`#336699`) |
| 그리기 안내 | 맑은 고딕 | 9pt | Italic, 연회색(`#999999`) |
| 구분선 | 맑은 고딕 | 9pt | Bold, 회색(`#666666`) |
| 밑줄 응답 | — | — | pBdr bottom, 줄간 14pt after |
| 페이지 | A4 | — | 여백: 상20/하20/좌25/우20mm |

---

## 학습지 구성 원칙

### 1. 차시별 필수 구조

```
[차시 헤더] — 차시번호, 소주제, 탐구단계, 제목
    ↓
[활동 1~N] — 안내 텍스트 + 응답 공간 (표/밑줄/그리기/빈칸)
    ↓
[핵심 발문] — 사실적·개념적·논쟁적 3개
    ↓
(소주제 마지막만) [성찰] — 3-2-1 전략 + 학습저널
    ↓
(평가 차시만) [평가] — 문항 + 응답 공간 (+ 루브릭)
```

### 2. 탐구단계별 활동 유형 가이드

| 탐구단계 | 주된 활동 유형 | 주된 헬퍼 |
|----------|---------------|----------|
| 관계맺기 | 직관 예측, 분류, 실험 | `add_table()`, `add_blank_lines()` |
| 집중하기 | 패턴 발견, 정리, 수형도/표 | `add_table()`, `add_diagram_box()` |
| 조사하기 | 비율 계산, 대조 실험 | `add_table()`, `add_blank_lines()` |
| 조직+정리 | 비교차트, 흐름도, 구조화 | `add_table()`, `add_diagram_box()` |
| 일반화 | 빈칸 문장, 검증 | `add_sentence_frame()`, `add_table()` |
| 전이 | 새 맥락 적용 | `add_blank_lines()` |
| 성찰 | 3-2-1, 학습저널 | `add_reflection_321()`, `add_learning_journal()` |

### 3. 응답 공간 크기 가이드

| 활동 유형 | 밑줄 수 / 박스 높이 |
|-----------|-------------------|
| 간단 서술 (1~2문장) | `add_blank_lines(1~2)` |
| 중간 서술 (3~5문장) | `add_blank_lines(3~4)` |
| 수형도/관계도 | `add_diagram_box(height_cm=3.5~4)` |
| 벤 다이어그램 | `add_diagram_box(height_cm=4)` |
| 흐름도/판단트리 | `add_diagram_box(height_cm=4~5)` |
| 평가 서술 | `add_blank_lines(4~5)` |

### 4. 소주제 경계 처리

- 소주제가 바뀌는 차시에서는 이전 소주제의 성찰(3-2-1 + 학습저널)을 포함
- 소주제 마지막 차시에 해당 소주제의 평가를 배치
- 마지막 소주제의 마지막 차시에 단원 전체 일반화 빈칸 완성 포함

---

## 이전 프로젝트 사례

| 단원 | 차시 | 차시 함수 수 | 표 수 | 파일 |
|------|------|-------------|------|------|
| 경우의 수와 확률 | 16 | 12 (결합4) | 35 | `경우의수와확률_학습지_전체.docx` |

---

## 주의사항

1. **인코딩**: Windows 환경에서 `sys.stdout` UTF-8 래핑 필수 (`errors='replace'`)
2. **python-docx**: `python -m pip install python-docx` 로 설치
3. **폰트**: 맑은 고딕이 설치되어 있어야 정상 표시. 미설치 시 대체 폰트로 렌더링
4. **표 셀 내용**: 학생이 채울 칸은 반드시 빈 문자열(`''`)로 비워둘 것
5. **활동 번호**: 차시 내에서 1부터 순차 번호 부여
6. **결합 차시**: `add_divider()` 로 차시 경계를 명시
7. **평가 루브릭**: 상/중/하 또는 A/B/C/D 기준으로 표 구성
8. **파일명**: 공백 대신 밑줄, 한글 포함 가능
9. **팀즈**: 8차시 이하이면 팀즈 없이 단일 스크립트로 충분
