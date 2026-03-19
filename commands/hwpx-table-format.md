---
name: hwpx-table-format
description: "HWPX 문서 내 표 서식 통일 스킬. 기준 표(reference table)의 셀서식(테두리, 글꼴, 정렬, 열너비 등)을 분석하여 동일 유형의 다른 표들에 일괄 적용한다. '표 서식 통일', '셀서식 맞춰줘', '표 디자인 통일', 'table format', '서식 일괄 적용' 등의 키워드로 호출."
allowed-tools: Read, Bash, Grep, Glob, Write, Edit, Task
argument-hint: "<hwpx파일경로> [기준표 설명 또는 페이지 번호]"
---

# HWPX 표 서식 통일 스킬

## 개요

HWPX 파일 내 여러 표의 셀서식(borderFillIDRef, charPrIDRef, paraPrIDRef, 열너비, 정렬 등)을 기준 표에 맞춰 일괄 통일하는 스킬이다. **클로드 팀즈(Task 에이전트 병렬 실행)** 패턴으로 작동한다.

## 핵심 원리

HWPX 표의 셀서식은 XML 속성으로 제어된다:
- **borderFillIDRef**: 테두리+배경 스타일 (header.xml에 정의)
- **charPrIDRef**: 글꼴·크기·굵기 (hp:run 속성)
- **paraPrIDRef**: 정렬·줄간격 (hp:p 속성)
- **styleIDRef**: 스타일 참조 (hp:p 속성)
- **cellSz**: 셀 너비·높이
- **header**: 헤더행 여부 ("1" or "0")

## 워크플로우 (5단계)

```
[Phase 1] 기준 표 분석      ← Task 에이전트 A
[Phase 2] 대상 표 조사      ← Task 에이전트 B  (A와 병렬)
[Phase 3] 서식 적용         ← Task 에이전트 C  (A,B 완료 후)
[Phase 4] 검증             ← Task 에이전트 D  (C 완료 후)
[Phase 5] 잔여 수정         ← 필요시 직접 수정
```

---

## Phase 1: 기준 표 분석 (Reference Table Analysis)

기준 표를 찾아 셀별 서식을 완전히 추출한다.

### 에이전트 프롬프트 템플릿

```
Task: 기준 표 서식 분석
File: {HWPX_PATH}
Section: Contents/{SECTION_NAME}.xml

기준 표(Table {REF_INDEX})의 모든 셀에서 다음을 추출:
1. 표 레벨: width, height, noAdjust, colCnt, rowCnt
2. 각 셀: borderFillIDRef, charPrIDRef, paraPrIDRef, styleIDRef, cellSz, header, vertAlign
3. borderFillIDRef별 실제 스타일 (header.xml에서 색상·테두리 두께 확인)
4. charPrIDRef별 실제 폰트 (header.xml에서 폰트명·크기·굵기 확인)

결과를 {OUTPUT_DIR}/ref_format.txt에 저장
```

### 추출할 핵심 데이터 구조

```python
# 위치별 borderFillIDRef 패턴 (예: 3열 표)
BF_PATTERN = {
    'header':    [28, 24, 27],   # 좌상단, 상단, 우상단
    'mid_data':  [22, 20, 21],   # 좌측, 내부, 우측
    'last_data': [26, 23, 25],   # 좌하단, 하단, 우하단
}

# 2열 표의 경우 (중간 열 없음)
BF_PATTERN_2COL = {
    'header':    [28, 27],       # 좌상단, 우상단
    'mid_data':  [22, 21],       # 좌측, 우측
    'last_data': [26, 25],       # 좌하단, 우하단
}
```

### 열 수에 따른 borderFillIDRef 매핑 규칙

```
┌──────────────────────────────────────┐
│  bf=28(좌상)  bf=24(상)  bf=27(우상)  │ ← 헤더행
├──────────────────────────────────────┤
│  bf=22(좌)    bf=20(내부) bf=21(우)   │ ← 중간 데이터행
│  bf=22(좌)    bf=20(내부) bf=21(우)   │
├──────────────────────────────────────┤
│  bf=26(좌하)  bf=23(하)  bf=25(우하)  │ ← 마지막행
└──────────────────────────────────────┘

※ 2열 표: 24(상), 20(내부), 23(하) 생략
※ N열 표: 중간 열은 모두 상/내부/하 사용
```

---

## Phase 2: 대상 표 조사 (Target Table Survey)

서식을 적용할 대상 표를 모두 찾는다.

### 에이전트 프롬프트 템플릿

```
Task: 대상 표 전수 조사
File: {HWPX_PATH}
Section: Contents/{SECTION_NAME}.xml

모든 표(hp:tbl)에 대해:
1. 인덱스, 행수, 열수
2. 헤더 텍스트
3. 현재 borderFillIDRef, charPrIDRef
4. 표 유형 분류 (rubric/standard_level/eval_plan/section_header/other)
5. 기준 표와의 차이점 (GOOD/BAD 분류)

결과를 {OUTPUT_DIR}/table_survey.txt에 저장
```

### 표 유형 분류 기준

| 유형 | 헤더 키워드 | 열수 | 행수 |
|------|-----------|------|------|
| rubric | 등급, 배점, 평가 기준 | 3 | 6 |
| standard_level | 성취수준, 수준, 특성 | 2 | 4-6 |
| assessment | 시기, 시수, 누계 | 8 | 18+ |
| eval_plan | 명칭, 유형, 만점 | 5-8 | 6-8 |
| section_header | 로마숫자(I,II,III) | 2 | 1 |

---

## Phase 3: 서식 적용 (Format Application)

### Python 스크립트 핵심 로직

```python
import zipfile, sys, io, os
from lxml import etree

# ── 1. 네임스페이스 등록 (필수!) ──
NS_REGISTRY = {
    'ha': 'http://www.hancom.co.kr/hwpml/2011/app',
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hp10': 'http://www.hancom.co.kr/hwpml/2016/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'hhs': 'http://www.hancom.co.kr/hwpml/2011/history',
    'hm': 'http://www.hancom.co.kr/hwpml/2011/master-page',
    'hpf': 'http://www.hancom.co.kr/schema/2011/hpf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf/',
    'ooxmlchart': 'http://www.hancom.co.kr/hwpml/2016/ooxmlchart',
    'hwpunitchar': 'http://www.hancom.co.kr/hwpml/2016/HwpUnitChar',
    'epub': 'http://www.idpf.org/2007/ops',
    'config': 'urn:oasis:names:tc:opendocument:xmlns:config:1.0',
}
for prefix, uri in NS_REGISTRY.items():
    etree.register_namespace(prefix, uri)

ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'}


# ── 2. 표 서식 적용 함수 ──
def apply_table_format(tbl, ncols, col_widths, table_width,
                       bf_pattern, hdr_charpr, data_charpr,
                       hdr_parapr_map, data_parapr_map):
    """
    하나의 hp:tbl 요소에 서식을 적용한다.

    Args:
        tbl: lxml Element (hp:tbl)
        ncols: 열 수
        col_widths: 열 너비 리스트 [w0, w1, ...]
        table_width: 표 전체 너비
        bf_pattern: dict {'header': [...], 'mid_data': [...], 'last_data': [...]}
        hdr_charpr: 헤더행 charPrIDRef (str)
        data_charpr: 데이터행 charPrIDRef (str)
        hdr_parapr_map: dict {col_index: paraPrIDRef} 헤더행
        data_parapr_map: dict {col_index: paraPrIDRef} 데이터행
    """
    rows = tbl.findall('.//hp:tr', ns)
    nrows = len(rows)

    # 표 레벨
    sz = tbl.find('hp:sz', ns)
    sz.set('width', str(table_width))
    tbl.set('noAdjust', '1')

    for ri, row in enumerate(rows):
        cells = row.findall('hp:tc', ns)
        for ci, cell in enumerate(cells):
            # cellSz
            csz = cell.find('hp:cellSz', ns)
            if csz is not None:
                csz.set('width', str(col_widths[ci]))

            # borderFillIDRef (위치별)
            if ri == 0:
                cell.set('borderFillIDRef', str(bf_pattern['header'][ci]))
                cell.set('header', '1')
            elif ri == nrows - 1:
                cell.set('borderFillIDRef', str(bf_pattern['last_data'][ci]))
                cell.set('header', '0')
            else:
                cell.set('borderFillIDRef', str(bf_pattern['mid_data'][ci]))
                cell.set('header', '0')

            # charPrIDRef
            cpr = hdr_charpr if ri == 0 else data_charpr
            for run in cell.findall('.//hp:run', ns):
                run.set('charPrIDRef', cpr)

            # paraPrIDRef
            ppr_map = hdr_parapr_map if ri == 0 else data_parapr_map
            for p in cell.findall('.//hp:p', ns):
                p.set('paraPrIDRef', str(ppr_map.get(ci, '0')))
                p.set('styleIDRef', '0')

            # linesegarray 제거 (한글이 자동 재계산)
            for lsa in cell.findall('.//hp:linesegarray', ns):
                lsa.getparent().remove(lsa)


# ── 3. HWPX 리패킹 함수 ──
def repack_hwpx(original_path, output_path, section_name, new_section_bytes):
    """
    HWPX ZIP을 다시 압축한다.
    mimetype은 반드시 첫 번째 엔트리, STORED로 저장.
    """
    zf = zipfile.ZipFile(original_path, 'r')
    files = {}
    for info in zf.infolist():
        files[info.filename] = zf.read(info.filename)
    zf.close()

    with zipfile.ZipFile(output_path, 'w') as zout:
        # mimetype STORED (첫 번째!)
        zout.writestr('mimetype', files['mimetype'],
                      compress_type=zipfile.ZIP_STORED)
        for fname, fdata in files.items():
            if fname == 'mimetype':
                continue
            if fname == f'Contents/{section_name}.xml':
                zout.writestr(fname, new_section_bytes,
                              compress_type=zipfile.ZIP_DEFLATED)
            else:
                zout.writestr(fname, fdata,
                              compress_type=zipfile.ZIP_DEFLATED)
```

### 사용 예시: 3열 채점기준 표 서식 통일

```python
# 기준 표에서 추출한 서식
bf_3col = {
    'header':    [28, 24, 27],
    'mid_data':  [22, 20, 21],
    'last_data': [26, 23, 25],
}
col_widths_3col = [10120, 10120, 52004]

for ti in bad_table_indices:
    tbl = tables[ti]
    apply_table_format(
        tbl, ncols=3,
        col_widths=col_widths_3col,
        table_width=72244,
        bf_pattern=bf_3col,
        hdr_charpr='51',
        data_charpr='2',
        hdr_parapr_map={0: 1, 1: 1, 2: 1},
        data_parapr_map={0: 1, 1: 1, 2: 0},  # C2=JUSTIFY
    )
```

### 사용 예시: 2열 성취수준 표 서식 통일

```python
bf_2col = {
    'header':    [28, 27],
    'mid_data':  [22, 21],
    'last_data': [26, 25],
}
col_widths_2col = [10120, 62124]

for ti in standard_level_indices:
    tbl = tables[ti]
    apply_table_format(
        tbl, ncols=2,
        col_widths=col_widths_2col,
        table_width=72244,
        bf_pattern=bf_2col,
        hdr_charpr='51',
        data_charpr='2',
        hdr_parapr_map={0: 1, 1: 1},
        data_parapr_map={0: 1, 1: 0},  # C1=JUSTIFY
    )
```

---

## Phase 4: 검증 (Verification)

### 에이전트 프롬프트 템플릿

```
Task: 서식 적용 결과 전수 검증
File: {OUTPUT_HWPX_PATH}

수정된 모든 표에 대해 셀별 검증:
1. borderFillIDRef가 위치별 패턴과 일치하는지
2. charPrIDRef가 헤더/데이터 기준과 일치하는지
3. paraPrIDRef가 올바른지
4. cellSz width가 올바른지
5. linesegarray가 제거되었는지
6. 텍스트 내용이 보존되었는지
7. ZIP 무결성 (mimetype STORED 여부)

결과: XX/XX PASS, 0 FAIL
```

---

## Phase 5: 잔여 수정 (Edge Cases)

에이전트가 놓친 1-2개 표를 직접 수정하는 단계. Phase 4에서 FAIL이 나온 표만 수동으로 처리.

---

## 팀즈 실행 패턴

```
# Phase 1 + 2 병렬 실행
Task A: 기준 표 분석 (run_in_background=true)
Task B: 대상 표 조사 (run_in_background=true)

# A, B 완료 대기 후
Task C: 서식 적용 (foreground, bypassPermissions)

# C 완료 후
Task D: 검증 (foreground)

# D에서 FAIL 발견 시
직접 Bash로 잔여 수정 → 재검증
```

---

## 주의사항

1. **네임스페이스 등록 필수**: `etree.register_namespace()`를 직렬화 전에 반드시 호출. 안 하면 `ns0:`, `ns1:` 접두사로 바뀌어 한글에서 손상됨
2. **mimetype STORED**: HWPX ZIP의 첫 번째 엔트리는 mimetype이며, 반드시 `ZIP_STORED`(압축 없음)로 저장
3. **linesegarray 제거**: 서식 변경 시 linesegarray는 제거해도 안전. 한글이 열 때 자동 재계산
4. **borderFillIDRef는 header.xml에 의존**: 사용하려는 bf ID가 header.xml에 정의되어 있어야 함. 없는 ID를 참조하면 파일 손상
5. **cp949 인코딩**: Windows에서 print() 시 유니코드 특수문자 오류 방지를 위해 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` 사용
6. **python 명령**: `python` 사용 (python3 아님)
7. **OneDrive 파일 잠금**: 한글이 파일을 열고 있으면 덮어쓰기 불가. `_v2.hwpx` 등 새 이름으로 저장
8. **section 구분**: section0.xml(개요), section1.xml(상세) 등 섹션이 나뉠 수 있음. 대상 섹션을 정확히 파악할 것
9. **표 유형별 열 수 차이**: 같은 "서식"이라도 2열/3열/8열 표는 borderFillIDRef 패턴이 다름. 열 수에 맞게 적응해야 함
10. **백업 필수**: 수정 전 반드시 `_backup.hwpx` 복사본 생성
