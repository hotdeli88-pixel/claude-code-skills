# HWPX 테마/스타일 변경 가이드

> 문서 전체의 색상·글꼴·테두리를 일괄 변경할 때 참조한다.
> "서식 개선", "색상 변경", "테마 적용", "디자인 통일" 요청 시 이 문서를 따른다.

## 개요

HWPX 문서의 시각적 스타일은 `header.xml`의 borderFill/charPr 정의와 `section0.xml`의 ID 참조로 제어된다. 테마 변경은 (1) 새 스타일 정의를 header.xml에 추가하고, (2) section0.xml에서 기존 ID를 새 ID로 교체하는 방식이다.

## 워크플로우 (8단계)

```
[1] header.xml 분석 — 기존 borderFill/charPr 전수 조사, 역할 추론
[2] section0.xml 분석 — 테이블 구조, ID 용도 매핑
[3] 타겟 색상 팔레트 결정 (사용자 지정 또는 프리셋)
[4] 새 borderFill XML 작성 (기존 max ID + 1부터)
[5] 새 charPr XML 작성 (기존 max ID + 1부터)
[6] header.xml에 주입 (</hh:borderFills> 앞 삽입 + itemCnt 업데이트)
[7] section0.xml에서 ID 참조 교체 (re.sub 콜백으로 테이블 블록 내부만)
[8] ZIP 재구성 → 결과 검증 (bf 수, cp 수, 텍스트 보존 확인)
```

## 색상 프리셋

### 공문서 네이비 (기본)
| 용도 | 색상 | 적용 대상 |
|------|------|-----------|
| primary | `#1B3A5C` | 헤더 배경, 로마숫자 박스, 섹션 제목 텍스트 |
| label_bg | `#E8EDF2` | 테이블 라벨 셀 배경 |
| border | `#8C9BAA` | 테이블 테두리 |
| body_text | `#333333` | 본문, 불릿 텍스트 |
| white | `#FFFFFF` | 네이비 배경 위 반전 텍스트 |

### 교육청 블루
| 용도 | 색상 |
|------|------|
| primary | `#2E75B6` |
| label_bg | `#D6E4F0` |
| border | `#2E75B6` |
| body_text | `#000000` |

## 역할 자동 감지 규칙

borderFill의 역할을 색상·테두리 패턴으로 추론:

| 패턴 | 역할 |
|------|------|
| 배경 채움 + 두꺼운 테두리(0.5mm+) + 같은 색 | 강조 박스 (로마숫자 셀, 표지 제목) |
| 하단만 실선, 나머지 NONE | 밑줄 효과 (섹션 제목 셀) |
| 좌측만 실선 | 간격 셀 (섹션 헤더 구분) |
| 배경 채움 + 얇은 테두리(0.15mm) | 테이블 헤더/라벨 셀 |
| 배경 없음 + 얇은 테두리 | 테이블 본문 셀 |
| 배경 채움 + 비대칭 두께 | 표지 제목 박스 셀 |

charPr 역할은 height(크기) + textColor + bold 조합으로 추론:

| 패턴 | 역할 |
|------|------|
| 18pt+ BOLD WHITE | 로마숫자, 표지 제목 (배경색 위) |
| 18pt+ BOLD 진한색 | 섹션 제목 텍스트 |
| 14pt 색상 | 소제목 |
| 11~12pt BOLD WHITE | 테이블 헤더 텍스트 |
| 11~12pt BOLD 진한색 | 테이블 라벨 텍스트 |
| 11pt 검정/회색 | 일반 본문 |

## 테이블 유형별 정밀 타겟팅

`<hp:tbl>` 속성으로 구분하여 안전하게 수정:

```python
def fix_by_table_type(text):
    def callback(m):
        tbl = m.group(0)
        # tbl 태그의 첫 200자에서 colCnt, borderFillIDRef 확인
        header = tbl[:300]

        if 'colCnt="1"' in header:
            return fix_cover_title(tbl)     # 표지 제목 (1x1)
        elif 'colCnt="3"' in header and has_roman_numeral(tbl):
            return fix_section_header(tbl)  # 섹션 헤더 (1x3)
        else:
            return fix_data_table(tbl)      # 데이터 테이블

    return re.sub(r'<hp:tbl\b[^>]*>.*?</hp:tbl>', callback, text, flags=re.DOTALL)
```

## borderFill XML 템플릿

### 배경+테두리 있음 (헤더/강조 셀)
```xml
<hh:borderFill id="{ID}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0"><hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/><hh:leftBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:rightBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:topBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:bottomBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/><hc:fillBrush><hc:winBrush faceColor="{FILL}" hatchColor="{FILL}" alpha="0"/></hc:fillBrush></hh:borderFill>
```

### 배경 없음 (본문 셀)
```xml
<hh:borderFill id="{ID}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0"><hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/><hh:leftBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:rightBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:topBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:bottomBorder type="SOLID" width="{WIDTH}" color="{COLOR}"/><hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/></hh:borderFill>
```

## charPr XML 템플릿

### 볼드체
```xml
<hh:charPr id="{ID}" height="{H}" textColor="{COLOR}" shadeColor="none" useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2"><hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/><hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/><hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/><hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/><hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/><hh:underline type="NONE" shape="SOLID" color="#000000"/><hh:strikeout shape="NONE" color="#000000"/><hh:outline type="NONE"/><hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/><hh:bold/></hh:charPr>
```

### 일반체 — `<hh:bold/>` 대신 바로 `</hh:charPr>`

## itemCnt 업데이트 (필수)

```python
text = re.sub(
    r'(<hh:borderFills[^>]*?)itemCnt="(\d+)"',
    lambda m: m.group(1) + f'itemCnt="{int(m.group(2)) + 추가수}"', text)
text = re.sub(
    r'(<hh:charProperties[^>]*?)itemCnt="(\d+)"',
    lambda m: m.group(1) + f'itemCnt="{int(m.group(2)) + 추가수}"', text)
```

## 주의사항

1. **비파괴 방식**: 원본 유지, 새 파일명으로 출력
2. **ID 충돌 방지**: 기존 max ID 확인 후 +1부터 시작
3. **테이블 블록 스코프**: re.sub 콜백에서 매치된 `<hp:tbl>...</hp:tbl>` 내부만 수정
4. **텍스트 보존 확인**: 수정 전후 `<hp:t>` 요소 수 비교
5. **fontRef 확인**: charPr의 fontRef가 header.xml의 fontfaces에 정의된 ID여야 함
