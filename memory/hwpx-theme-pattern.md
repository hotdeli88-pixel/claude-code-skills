# HWPX 테마/스타일 변경 패턴

## 워크플로우

```
[1] header.xml 분석 (borderFill, charPr 전수 조사)
[2] section0.xml 분석 (테이블 구조, charPrIDRef/borderFillIDRef 용도 매핑)
[3] 타겟 색상 팔레트 결정
[4] 새 borderFill 정의 작성 (기존 max ID + 1부터)
[5] 새 charPr 정의 작성 (기존 max ID + 1부터)
[6] header.xml에 주입 (</hh:borderFills> 앞에 삽입, itemCnt 업데이트)
[7] section0.xml에서 ID 참조 교체 (re.sub 콜백으로 테이블 블록 내부만 타겟)
[8] ZIP 재구성 → 검증
```

## 핵심 XML 구조

### borderFill (배경 있음)
```xml
<hh:borderFill id="13" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
  <hh:slash type="NONE" Crooked="0" isCounter="0"/>
  <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
  <hh:leftBorder type="SOLID" width="0.7 mm" color="#1B3A5C"/>
  <hh:rightBorder type="SOLID" width="0.7 mm" color="#1B3A5C"/>
  <hh:topBorder type="SOLID" width="0.7 mm" color="#1B3A5C"/>
  <hh:bottomBorder type="SOLID" width="0.7 mm" color="#1B3A5C"/>
  <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>
  <hc:fillBrush><hc:winBrush faceColor="#1B3A5C" hatchColor="#1B3A5C" alpha="0"/></hc:fillBrush>
</hh:borderFill>
```

### borderFill (배경 없음, 하단만 실선)
```xml
<hh:borderFill id="15" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
  <hh:slash type="NONE" Crooked="0" isCounter="0"/>
  <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
  <hh:leftBorder type="NONE" width="0.1 mm" color="#1B3A5C"/>
  <hh:rightBorder type="NONE" width="0.1 mm" color="#1B3A5C"/>
  <hh:topBorder type="NONE" width="0.1 mm" color="#1B3A5C"/>
  <hh:bottomBorder type="SOLID" width="0.7 mm" color="#1B3A5C"/>
  <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>
</hh:borderFill>
```

### charPr (볼드)
```xml
<hh:charPr id="33" height="2000" textColor="#FFFFFF" shadeColor="none"
  useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">
  <hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
  <hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
  <hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
  <hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
  <hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
  <hh:underline type="NONE" shape="SOLID" color="#000000"/>
  <hh:strikeout shape="NONE" color="#000000"/>
  <hh:outline type="NONE"/>
  <hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/>
  <hh:bold/>
</hh:charPr>
```

### charPr (일반체) — `<hh:bold/>` 제거, `</hh:charPr>`로 바로 닫기

## 색상 프리셋

### 공문서 네이비
```python
THEME = {
    "primary": "#1B3A5C",      # 딥 네이비 (헤더, 로마숫자 박스, 섹션 제목)
    "label_bg": "#E8EDF2",     # 연회색 (테이블 라벨 셀)
    "border": "#8C9BAA",       # 중간회색 (테이블 테두리)
    "body_text": "#333333",    # 본문 텍스트
    "white": "#FFFFFF",        # 반전 텍스트 (네이비 배경 위)
}
```

## 테이블 유형 구분 (정밀 타겟팅)

section0.xml에서 `<hp:tbl>` 태그의 속성으로 구분:

| 유형 | colCnt | tbl borderFillIDRef | 셀 특징 |
|------|--------|---------------------|---------|
| 표지 제목 | 1 | varies | 셀에 큰 제목 텍스트 |
| 섹션 헤더 | 3 | varies | C0=로마숫자, C1=간격, C2=제목 |
| 데이터 테이블 | 2~N | varies | 헤더행+라벨+본문 셀 |

re.sub 콜백에서 매치된 블록 내부만 수정하여 안전하게 교체:

```python
def fix_tables(text):
    def callback(m):
        tbl = m.group(0)
        if 'colCnt="3"' in tbl[:200] and '로마숫자텍스트' in tbl:
            # 섹션 헤더 처리
            ...
        return tbl
    return re.sub(r'<hp:tbl\b[^>]*>.*?</hp:tbl>', callback, text, flags=re.DOTALL)
```

## itemCnt 업데이트

```python
import re
# borderFills
text = re.sub(
    r'(<hh:borderFills[^>]*?)itemCnt="(\d+)"',
    lambda m: m.group(1) + f'itemCnt="{int(m.group(2)) + NEW_COUNT}"',
    text
)
# charProperties
text = re.sub(
    r'(<hh:charProperties[^>]*?)itemCnt="(\d+)"',
    lambda m: m.group(1) + f'itemCnt="{int(m.group(2)) + NEW_COUNT}"',
    text
)
```

## 참조 스크립트

- 작동 예시: `/mnt/c/Users/sdm24/OneDrive/바탕 화면/01_학교업무/26.03.11 디지털선도학교 계획서/improve_hwpx_style.py`
- 입력: 학부모_연수자료_AI디지털선도학교(한윤석) - 복사본.hwpx
- 출력: 학부모_연수자료_개선본.hwpx
- 결과: bf 12→18, cp 33→41, 텍스트 106개 보존, 전체 검증 PASS
