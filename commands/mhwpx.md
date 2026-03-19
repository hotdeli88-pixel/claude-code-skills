---
name: mhwpx
description: "DOCX→HWPX 수식 변환기. DOCX 문서의 수식을 HWP 수식 편집기 형식으로 변환하여 HWPX 한글문서를 생성합니다. 'DOCX를 HWPX로', 'DOCX 한글 변환', 'mhwpx', '수식 변환 한글', 'DOCX to HWPX', '한글문서 변환' 등의 키워드로 호출."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Agent
argument-hint: "<DOCX파일경로> [출력HWPX경로]"
---

# DOCX → HWPX 수식 변환기 (mhwpx)

DOCX 문서를 HWPX 한글문서로 변환합니다. 유니코드 수식(√, ², ³, |a|, 분수 등)을 `hp:equation > hp:script`로 변환하여 HWP 수식 편집기에서 편집 가능한 형태로 삽입합니다. 일반 텍스트는 `hp:t`로 분리하여 수식 편집기가 아닌 일반 텍스트로 유지합니다.

---

## Phase 0: 입력 확인

1. 인자에서 DOCX 파일 경로를 추출한다.
   - 인자가 없으면 사용자에게 "변환할 DOCX 파일 경로를 입력해주세요." 라고 질문한다.
2. 출력 HWPX 경로를 결정한다.
   - 두 번째 인자가 있으면 그것을 사용한다.
   - 없으면 입력 파일과 동일 디렉터리에서 확장자만 `.docx` → `.hwpx`로 변경한다.
3. DOCX 파일 존재를 확인한다 (Bash: `test -f "<경로>"`).
   - 존재하지 않으면 오류 메시지를 출력하고 중단한다.
4. python-hwpx 패키지 설치를 확인한다.
   ```bash
   pip show python-hwpx
   ```
   - 설치되어 있지 않으면 `pip install python-hwpx`를 실행한다.

---

## Phase 1: DOCX 분석 (Agent 사용)

Agent를 사용하여 DOCX 내용을 분석한다.

### 분석 항목
- **문서 구조**: 단락 수, 표 수, 페이지 수
- **수식 포함 텍스트 식별**: 다음 패턴이 포함된 단락을 찾는다.
  - `√` (제곱근)
  - `²`, `³`, `⁴` 등 유니코드 위첨자
  - `|변수|` (절댓값)
  - 분수 표현 (`a/b`)
  - 대문자 2자 연속 (선분, 예: AB, CD)
- **서식 요소**: 색상, 굵기, 크기, 표 배경색

### 출력
- 분석 결과를 사용자에게 간략 보고한다.
- 수식 변환 예상 결과 미리보기를 표시한다. 예:
  ```
  [수식 변환 미리보기]
  원본: √(3²+4²)=5  →  HWP: sqrt {3 ^{2} +4 ^{2}} =5
  원본: |a|≥0       →  HWP: LEFT | a RIGHT | >= 0
  원본: x²+y²       →  HWP: x ^{2} +y ^{2}
  ```

---

## Phase 2: 변환 실행

변환 스크립트를 실행한다.

- **스크립트 경로**: `~/.claude/skills/mhwpx/scripts/convert_docx_to_hwpx.py`
- **실행 명령**:
  ```bash
  python ~/.claude/skills/mhwpx/scripts/convert_docx_to_hwpx.py "<입력DOCX>" "<출력HWPX>"
  ```
- **주의**: `python` 사용 (3.14, 모듈 설치됨). `python3`(3.13)은 사용하지 않는다.
- stdout 출력으로 진행 상황을 확인한다.
- 스크립트 실행 실패 시 에러 로그를 분석하고 Agent로 디버깅한다.

---

## Phase 3: 검증

생성된 HWPX를 ZIP으로 열어 다음 항목을 검증한다.

### 검증 항목
1. **mimetype 검증**: ZIP의 첫 번째 엔트리가 `mimetype`이고, 압축 방식이 STORED(0)인지 확인.
2. **수식 요소 검증**: `section0.xml`에서 `hp:equation` 요소 개수를 세고, Phase 1에서 식별한 수식 수와 비교.
3. **수식 스크립트 검증**: `hp:script` 내용이 올바른 HWP 수식 스크립트 문법인지 확인.
   - `sqrt`, `over`, `^{}`, `LEFT |`, `RIGHT |` 등의 키워드가 올바르게 사용되었는지.
4. **인코딩 검증**: 텍스트 인코딩이 UTF-8인지 확인.
5. **스타일 검증**: `header.xml`에 필요한 스타일(CharPr, BorderFill)이 존재하는지 확인.

### 검증 스크립트 (Bash 인라인)
```python
import zipfile, xml.etree.ElementTree as ET
z = zipfile.ZipFile("<출력HWPX>", "r")
# mimetype 확인
info = z.infolist()[0]
assert info.filename == "mimetype" and info.compress_type == 0
# section0.xml 파싱
ns = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
tree = ET.parse(z.open("Contents/section0.xml"))
eqs = tree.findall(".//hp:equation", ns)
print(f"수식 개수: {len(eqs)}")
for eq in eqs:
    script = eq.find("hp:script", ns)
    if script is not None and script.text:
        print(f"  - {script.text[:60]}")
z.close()
```

- 문제 발견 시 Agent로 디버깅 및 수정한다.

---

## Phase 4: 보고

변환 결과를 사용자에게 요약 보고한다.

### 보고 항목
- **파일 정보**: 입력/출력 파일 경로 및 크기
- **수식 변환 매핑 테이블**: 원본 유니코드 수식 → HWP 수식 스크립트 (주요 항목)
- **문서 구조**: 표 수, 단락 수, 수식 개수
- **안내**: "한글에서 열어 수식이 정상적으로 표시되는지 확인해주세요."

---

## 수식 변환 규칙 (레퍼런스)

변환 스크립트(`convert_docx_to_hwpx.py`)가 처리하는 수식 패턴:

| 유니코드 입력 | HWP 수식 스크립트 | 설명 |
|---|---|---|
| `√(expr)` | `sqrt {expr}` | 제곱근 (중첩 괄호 지원) |
| `√49` | `sqrt {49}` | 독립 제곱근+연속숫자 (다자리 캡처) |
| `√` (단독) | `sqrt{~}` | 독립 제곱근 기호 |
| `²` `³` `⁴` ... | `^{2}` `^{3}` `^{4}` ... | 유니코드 위첨자 |
| `(expr)²` | `(expr)^{2}` | 괄호식+위첨자 |
| `3²` | `3^{2}` | 숫자+위첨자 |
| `\|a\|` | `LEFT \| a RIGHT \|` | 절댓값 |
| `±7` | `+-7` | 플러스마이너스 |
| `a/b` | `{a} over {b}` | 분수 (향후 확장) |
| `AB` (대문자2개) | `bar {AB}` | 선분 (향후 확장) |

## 수식 분리 규칙

텍스트에서 수식과 일반 텍스트를 분리하는 규칙:

1. `√(` 로 시작하면 균형 괄호까지 수식으로 추출한다.
2. `√숫자` (괄호 없음) → 연속 숫자/알파벳/소수점 전체를 캡처한다 (예: `√49`, `√0.64`).
3. `√expr = 값` 뒤에 등호+값이 이어지면 수식에 포함한다 (소수/분수 포함).
   - **단, 값 뒤에 한글이 바로 이어지면 포함하지 않음** (예: `√49 = 49의 양의 제곱근` → `√49`만 수식)
4. `(expr)²` 패턴을 수식으로 추출한다.
5. 변수+위첨자 (`a²`, `x³`) 및 **숫자+위첨자** (`3²`, `9²`)를 수식으로 추출한다.
6. `|변수|` 절댓값 패턴을 수식으로 추출한다.
7. `±숫자` 패턴을 수식으로 추출한다.
8. 수식-연산자(`=`, `<`, `>`)-수식이 이어지면 병합한다.
9. 한글 문자가 나오면 수식 종료한다.
10. **표(table) 셀 내부의 수식도 동일하게 처리한다** (단락뿐 아니라 셀 내에서도 수식 변환 적용).

## 수식 크기 추정 (동적)

수식의 `hp:sz` width/height를 스크립트 내용 기반으로 동적 추정한다 (`_estimate_equation_size`):

- 렌더링 글자 수 = 스크립트에서 키워드(sqrt, over, LEFT, RIGHT) 및 중괄호/공백 제거 후 문자 수
- 기본 너비: 글자당 ~280 hwpunit
- sqrt 기호: +350 hwpunit/개
- 위첨자 보정: -80 hwpunit/개 (작은 글꼴)
- 범위: min=800, max=20000
- 높이: 기본 1000, sqrt→1200, over(분수)→1600, 위첨자→1100
- **하드코딩 금지**: 이전 `width="3916"` 고정값은 짧은 수식에 과도한 공간, 긴 수식에 겹침 유발

## 스크립트 기술 요구사항

- **python** 사용 (3.14, 모듈 설치됨), `python3`(3.13) 아님.
- `xml.etree.ElementTree` 사용 (`lxml` 아님).
- `ET.register_namespace()`로 네임스페이스 등록 필수.
- mimetype은 ZIP 첫 엔트리, 압축 없이(STORED) 저장.
- section0.xml 루트에 모든 네임스페이스 선언 (ha, hp, hp10, hs, hc, hh, hhs, hm).
- `print()`에 유니코드 특수문자(`✓`, `×`) 사용 금지 (cp949 인코딩 오류).
- 수식의 `hp:equation` 속성:
  - `version="Equation Version 60"`
  - `baseLine="85"`
  - `font="HYhwpEQ"`
  - `lineMode="CHAR"`
  - `treatAsChar="1"` (인라인)

## 주의사항

- DOCX 내 OMML 수식(`m:oMath`)은 현재 미지원. 유니코드 평문 수식만 처리한다.
- 복잡한 LaTeX 수식 변환은 향후 확장 예정.
- OneDrive 파일 잠금 주의: 한글이 열고 있으면 덮어쓰기 불가.
- 백업: 기존 HWPX 파일이 있으면 `_backup` 접미사를 붙여 백업 생성 후 덮어쓴다.
- 수식 크기(`width`/`height`)는 `_estimate_equation_size()`로 동적 추정하며, 한글에서 열면 자동 재조정된다.
- **표 셀 내 수식 처리**: `_build_table_paragraph`에서도 `has_math_chars()` + `split_text_and_math()` 적용 필수 (이전 버그: 셀 내 수식 미변환).
- **한글 lookahead**: `= 값` 뒤에 한글(가-힣)이 바로 이어지면 수식으로 포함하지 않음 (예: `49의` → 텍스트).

## 해결된 버그 이력 (2026-03-13)

1. **표 셀 내 수식 미변환**: `_build_table_paragraph`에서 런 텍스트를 그대로 `hp:t`로 넣음 → `has_math_chars` + `split_text_and_math` 분기 추가
2. **`√숫자` 한 자리만 캡처**: `√49` → `sqrt{4}` + `9` → 연속 숫자/소수점 전체 캡처로 수정
3. **등호 뒤 소수/분수 미캡처**: `= 0.8`, `= 2/3` → regex에 `\.?\d*(?:/\d+)?` 추가
4. **한글 뒤 수식 오분리**: `= 49의` → 한글 lookahead 추가
5. **수식 너비 하드코딩**: `width="3916"` 고정 → 스크립트 내용 기반 동적 추정
6. **`±` 미처리**: `has_math_chars`에 `\u00B1` 추가, `unicode_to_hwp_equation`에 `±→+-` 변환 추가
7. **`숫자²` 미인식**: `split_text_and_math`에서 `ch.isalpha()` → `ch.isalpha() or ch.isdigit()` 확장

## 향후 확장 계획

1. OMML(Office Math ML) 수식 변환 지원
2. `formula_converter.py` 로직 통합 (분수, 선분, 단위 등)
3. LaTeX 수식 → HWP 수식 스크립트 변환
4. 이미지 포함 DOCX 지원
5. 복수 DOCX 일괄 변환 모드
