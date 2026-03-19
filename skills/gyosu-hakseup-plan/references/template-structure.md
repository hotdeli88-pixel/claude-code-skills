# 템플릿 HWPX 구조 레퍼런스

## 파일: 2026학년도 교수학습 및 평가 운영 계획 양식(중_배포용).hwpx

## ZIP 구조
```
mimetype                          (STORED, 첫 번째)
version.xml
Contents/
  header.xml                      (스타일 정의, 464KB)
  section0.xml                    (본문, 89KB)
  section1.xml                    (평가 상세, 471KB)
  content.hpf                     (메타데이터)
BinData/
  image1.jpg, image2.jpg
META-INF/
  container.rdf, container.xml, manifest.xml
settings.xml
Preview/
  PrvText.txt, PrvImage.png
```

## section0.xml 표 구조

| 인덱스 | 표 | 설명 |
|--------|-----|------|
| 0 | 제목 표 | 1x1 "교수학습 및 평가 운영 계획안 양식" |
| 1 | 표지 | 3x3 학년도/학기/교과명 |
| 2 | 기본정보 | 2x5 학교명/학년/학급수/교과서명 |
| 3 | 목차 | 1x1 차례 |
| 4 | **교수학습-평가 계획** | 8열 핵심 표 (시기/시수/누계/단원명/성취기준/평가요소/수업평가방법/비고) |
| 5 | 비고 표 | 1x2 (Table 4 뒤에 붙는 참고 표) |

## 8열 교수학습-평가 계획 표 (Table 4)

### 열 너비
```python
COL_WIDTHS = [4742, 3613, 3614, 7122, 14380, 12350, 22255, 4331]
# 합계 = 72407 (테이블 전체 너비)
```

| # | 열 | 너비 |
|---|-----|------|
| 0 | 시기 | 4742 |
| 1 | 시수 | 3613 |
| 2 | 누계 | 3614 |
| 3 | 단원명 | 7122 |
| 4 | 교육과정 성취기준 | 14380 |
| 5 | 평가 요소 | 12350 |
| 6 | 수업·평가 방법 | 22255 |
| 7 | 비고 | 4331 |

### 셀 서식 — 헤더행 (row 0)
- borderFillIDRef: **55**
- header: "1"
- vertAlign: CENTER

| 열 | paraPrIDRef | charPrIDRef |
|----|-------------|-------------|
| 0 (시기) | 28 | 24 |
| 1-7 | 25 | 24 |

### 셀 서식 — 데이터행 (row 1+)
- borderFillIDRef: **4**
- header: "0"
- vertAlign: CENTER

| 열 | paraPrIDRef | charPrIDRef |
|----|-------------|-------------|
| 0 (시기) | 1 | 147 |
| 1 (시수) | 55 | 108 |
| 2 (누계) | 55 | 108 |
| 3 (단원명) | 55 | 104 |
| 4 (성취기준) | 82 | 104 |
| 5 (평가요소) | 83 | 148 |
| 6 (수업평가방법) | 89 | 149 |
| 7 (비고) | 84 | 108 |

## 테이블 속성
```python
TABLE_ATTRIBS = {
    "numberingType": "TABLE",
    "textWrap": "TOP_AND_BOTTOM",
    "pageBreak": "CELL",
    "repeatHeader": "1",
    "colCnt": "8",
    "borderFillIDRef": "4",
    "noAdjust": "1",
}
```

## 콘텐츠 폭 계산
```
page_width = 59528
margin_left = 5669
margin_right = 5669
content_width = 59528 - 5669 - 5669 = 48190
```

## 네임스페이스

| 접두사 | URI |
|--------|-----|
| hp | http://www.hancom.co.kr/hwpml/2011/paragraph |
| hs | http://www.hancom.co.kr/hwpml/2011/section |
| hc | http://www.hancom.co.kr/hwpml/2011/core |
| hh | http://www.hancom.co.kr/hwpml/2011/head |
| ha | http://www.hancom.co.kr/hwpml/2011/app |
| hp10 | http://www.hancom.co.kr/hwpml/2016/paragraph |
| hm | http://www.hancom.co.kr/hwpml/2011/master-page |
| hhs | http://www.hancom.co.kr/hwpml/2011/history |
