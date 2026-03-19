---
name: gyosu-hakseup-plan
description: "교수학습 및 평가 운영 계획 HWPX 생성 스킬. 모든 교과(수학, 국어, 영어, 사회, 과학 등)에 대해 배포용 양식 기반으로 교수학습-평가 운영 계획 문서를 HWPX로 생성한다. DOCX 변환 또는 대화 입력 모두 지원. '교수학습', '평가 운영 계획', '평가계획', '교수학습계획', '운영계획 hwpx', '평가계획 hwpx' 등의 키워드로 호출."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
argument-hint: "[DOCX파일경로] [교과명] [학년]"
---

# 교수학습 및 평가 운영 계획 HWPX 생성

## 개요

2026학년도 교수학습 및 평가 운영 계획 양식(중_배포용)을 기반으로,
지정된 교과의 교수학습-평가 운영 계획 HWPX 문서를 완성한다.
모든 교과에 범용으로 사용 가능하다.

## 경로 설정

```python
import os
SKILL_DIR = os.path.expanduser("~/.claude/skills/gyosu-hakseup-plan")
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "template.hwpx")
GENERATE_SCRIPT = os.path.join(SKILL_DIR, "scripts", "generate_hwpx.py")
PARSE_SCRIPT = os.path.join(SKILL_DIR, "scripts", "parse_docx_input.py")
FIX_NS_SCRIPT = os.path.expanduser("~/.claude/skills/hwpx/scripts/fix_namespaces.py")
```

## 사용법

```
/gyosu-hakseup-plan                                  # 대화 모드 (교과/학년 질문)
/gyosu-hakseup-plan 수학 중1                          # 대화 모드 (교과+학년 지정)
/gyosu-hakseup-plan ./수학과_계획.docx                 # DOCX 변환 모드
/gyosu-hakseup-plan ./수학과_계획.docx 수학 중1~중3     # DOCX + 교과 정보
```

---

## 워크플로우 (5단계)

### Phase 0: 입력 확인 및 환경 준비

1. 인자에서 DOCX 경로, 교과명, 학년을 파싱한다. 없으면 AskUserQuestion:
   - **교과명** (필수): 수학, 국어, 영어, 사회, 과학, 도덕, 기술가정, 정보, 체육, 음악, 미술, 진로 등
   - **학년** (필수): 중1, 중2, 중3, 또는 중1~중3 (전 학년)
   - **학기** (필수): 1학기 또는 2학기
   - **학교명** (선택): 기본값 "OO중"
   - **입력 모드**: DOCX 경로 있으면 Mode A, 없으면 Mode B

2. 작업 디렉터리: DOCX 파일 위치 또는 현재 디렉터리

---

### Phase 1: 데이터 수집

#### Mode A: DOCX 파싱

```bash
python "$PARSE_SCRIPT" --docx "입력.docx" --output "_curriculum_data.json"
```

1. `parse_docx_input.py`로 DOCX에서 8열 교수학습-평가 계획 표를 자동 탐지
2. 학교 기본정보, 교과명, 학년 등도 자동 추출
3. `_curriculum_data.json` 생성

추출 확인 후 사용자에게 결과를 보여주고 수정 요청을 받는다.

#### Mode B: 대화 입력

1. AskUserQuestion으로 수집:
   - 주당 수업시수 (기본 4)
   - 교과서명 (선택)
   - 단원 구성 (단원명 + 주차 배분)
   - 평가 계획 (수행평가 횟수, 유형, 배점)
   - 성취기준 코드 (2022 개정 교육과정)

2. AI가 교육과정 지식 기반으로 17주 교수학습-평가 계획 초안을 생성한다:
   - 17주 x 주당시수 = 총 시수 계산
   - 단원별 성취기준 매핑
   - 평가 요소 및 수업-평가 방법 작성
   - 수행평가 시기 배치

3. 초안을 사용자에게 보여주고 확인/수정 요청

4. 확정된 데이터를 `_curriculum_data.json`으로 저장

---

### Phase 2: HWPX 생성

```bash
python "$GENERATE_SCRIPT" --data "_curriculum_data.json" --output "2026학년도_{학기}_{교과}과_교수학습_평가_운영_계획.hwpx"
```

스크립트 동작:
1. 템플릿 HWPX(assets/template.hwpx) 로드
2. section0.xml에서 텍스트 교체 (교과명, 학교명 등)
3. Table 4(교수학습-평가 계획)를 학년별 N개 표로 교체
4. ZIP 리패킹 (mimetype STORED 첫 번째)
5. fix_namespaces.py 후처리

---

### Phase 3: 서식 보정 (필요 시)

생성된 HWPX의 표 서식을 검사하고 보정:
- 8열 교수학습-평가 계획 표 열 너비 확인: `[4742, 3613, 3614, 7122, 14380, 12350, 22255, 4331]`
- 헤더행 borderFillIDRef=55, 데이터행 borderFillIDRef=4
- linesegarray 제거 (한글이 자동 재계산)

필요하면 lxml로 직접 section0.xml을 수정한 후 재패킹.

---

### Phase 4: 검증

검증 항목:
1. ZIP 무결성 (mimetype STORED 첫 번째)
2. section0.xml 표 행 수 확인
3. 네임스페이스 (ns0:/ns1: 없음)
4. 누계 시수 정합성

결과를 사용자에게 보고:
```
검증 결과:
  section0.xml:
    - 기본정보: [학교명] [교과명] [학년] 확인
    - 교수학습-평가 계획: [N]학년 [M]행 완료
  ZIP 무결성: PASS
  네임스페이스: PASS
  출력: [파일경로]
```

---

## JSON 데이터 형식

상세 스키마: `~/.claude/skills/gyosu-hakseup-plan/references/curriculum-data-format.md`

```json
{
  "school_info": {
    "school_name": "OO중",
    "subject": "수학",
    "semester": "1학기",
    "year": "2026",
    "grades": [{"grade": 1, "classes": 6, "hours_per_week": 4, "textbook": ""}]
  },
  "curriculum_tables": [
    {
      "grade": 1,
      "rows": [
        ["3월 1주", "4", "4", "I. 단원명", "[9수01-01] ...", "§ 평가요소", "[수업]...", ""],
        ...
      ]
    }
  ]
}
```

8열: 시기 / 시수 / 누계 / 단원명 / 교육과정 성취기준 / 평가 요소 / 수업·평가 방법 / 비고

---

## 주의사항

1. **python 명령**: `python` 사용 (python3 아님, Python 3.14 설치됨)
2. **cp949 인코딩**: Windows 환경에서 특수문자 출력 시 인코딩 오류 주의
3. **OneDrive 파일 잠금**: 한글이 파일을 열고 있으면 덮어쓰기 불가. 새 이름으로 저장
4. **백업 필수**: 수정 전 반드시 원본 백업
5. **HwpxDocument.open() 사용 금지**: 복잡한 템플릿은 lxml + zipfile로 처리
6. **네임스페이스 후처리 필수**: generate_hwpx.py가 자동으로 fix_namespaces.py를 호출하지만, 수동 수정 시에는 반드시 별도 실행
7. **교과별 데이터만 교체**: 스크립트/템플릿 구조는 교과에 무관. JSON 데이터만 교과별로 다르게 준비하면 됨
