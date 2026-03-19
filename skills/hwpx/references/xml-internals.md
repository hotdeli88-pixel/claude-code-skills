# HWPX 저수준 XML 구조 참조

> 이 문서는 HWPX 파일의 내부 구조, 네임스페이스, 페이지 설정 등 저수준 XML 조작이 필요할 때 참조한다.

## 문서 구조

HWPX 파일의 내부 ZIP 구조:

```
document.hwpx (ZIP)
├── mimetype
├── META-INF/
│   ├── container.xml
│   ├── container.rdf
│   └── manifest.xml
├── version.xml
├── settings.xml
├── Preview/
│   ├── PrvImage.png
│   └── PrvText.txt
└── Contents/
    ├── content.hpf        ← 매니페스트 (파트 목록, 이미지 참조)
    ├── header.xml          ← 스타일/글꼴/문단속성/테두리배경 정의
    └── section0.xml        ← 본문 내용 (섹션 추가 시 section1.xml 등)
```

## HWPUNIT 변환

```
1mm ≈ 283.46 HWPUNIT   (7200 HWPUNIT = 1 inch)
```

### 주요 변환표

| 항목 | mm | HWPUNIT |
|------|-----|---------|
| A4 너비 | 210 | 59528 |
| A4 높이 | 297 | 84186 |
| 20mm | 20 | 5669 |
| 15mm | 15 | 4252 |
| 10mm | 10 | 2835 |

## 네임스페이스 매핑

| 네임스페이스 URI | 표준 프리픽스 | 사용 위치 |
|-----------------|-------------|----------|
| `http://www.hancom.co.kr/hwpml/2011/head` | `hh` | header.xml |
| `http://www.hancom.co.kr/hwpml/2011/core` | `hc` | header.xml, section*.xml |
| `http://www.hancom.co.kr/hwpml/2011/paragraph` | `hp` | header.xml, section*.xml |
| `http://www.hancom.co.kr/hwpml/2011/section` | `hs` | section*.xml |
| `http://www.hancom.co.kr/hwpml/2011/app` | `ha` | |
| `http://www.hancom.co.kr/hwpml/2016/paragraph` | `hp10` | 2016 확장 |

## header.xml 주요 요소

### 글꼴 정의 (fontfaces)

글꼴은 `<hh:fontface lang="HANGUL|LATIN|...">` 그룹 내에서 id로 참조:

```xml
<hh:fontface lang="HANGUL" fontCnt="8">
  <hh:font id="0" face="함초롬돋움" type="TTF" isEmbedded="0"/>
  <hh:font id="1" face="함초롬바탕" type="TTF" isEmbedded="0"/>
  <hh:font id="2" face="휴먼명조" type="TTF" isEmbedded="0"/>
  <hh:font id="3" face="HY헤드라인M" type="TTF" isEmbedded="0"/>
  <hh:font id="6" face="한양중고딕" type="HFT" isEmbedded="0"/>
</hh:fontface>
```

### 글자 속성 (charPr)

```xml
<hh:charPr id="5" height="1600" textColor="#000000" ...>
  <hh:fontRef hangul="3" .../>  <!-- hangul="3" → HY헤드라인M -->
  <hh:bold .../>
</hh:charPr>
```

- `height`: 1/100pt 단위 (1600 = 16pt)
- `textColor`: 글자 색상
- `fontRef hangul="N"`: HANGUL fontface 내 id=N 글꼴 참조

### 문단 속성 (paraPr)

```xml
<hh:paraPr id="28">
  <hh:align horizontal="JUSTIFY" vertical="BASELINE"/>
  <hh:heading type="NONE" idRef="0" level="0"/>
  <hh:margin><hc:intent value="-2606" unit="HWPUNIT"/></hh:margin>
  <hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>
  <hp:spacing before="0" after="0" .../>
</hh:paraPr>
```

- `horizontal`: JUSTIFY, CENTER, LEFT, RIGHT
- `hc:intent value`: 들여쓰기 (음수 = 내어쓰기)
- `lineSpacing`: 줄간격 (PERCENT=160 → 160%)
- `spacing before/after`: 문단 전/후 간격

### 테두리/배경 (borderFill)

```xml
<hh:borderFill id="9">
  <hh:leftBorder type="SOLID" width="0.12 mm" color="#006699"/>
  <!-- ... 기타 테두리 ... -->
  <hh:fillBrush>
    <hh:windowBrush faceColor="#193AAA" .../>
  </hh:fillBrush>
</hh:borderFill>
```

## section0.xml 주요 요소

### 페이지 설정

```xml
<hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY">
  <hp:margin header="4251" footer="4251" gutter="0"
             left="5669" right="5669" top="4251" bottom="4251"/>
</hp:pagePr>
```

### 문단

```xml
<hp:p id="..." paraPrIDRef="28" styleIDRef="0" pageBreak="0">
  <hp:run charPrIDRef="5">
    <hp:t>본문 텍스트</hp:t>
  </hp:run>
</hp:p>
```

- `paraPrIDRef`: header.xml의 paraPr id 참조
- `charPrIDRef`: header.xml의 charPr id 참조
- `pageBreak="1"`: 이 문단 앞에서 페이지 나눔

### 테이블 (⚠️ 정확한 구조 — 반드시 이대로!)

테이블은 별도의 `<hp:p>` 단락 안에 `<hp:run>` → `<hp:tbl>` 순서로 배치한다.

```xml
<hp:p id="..." paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:tbl id="..." zOrder="0" numberingType="TABLE"
            textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES"
            lock="0" dropcapstyle="None" pageBreak="CELL"
            repeatHeader="1" rowCnt="2" colCnt="2"
            cellSpacing="0" borderFillIDRef="3" noAdjust="0">
      <!-- 1. 테이블 크기 -->
      <hp:sz width="42520" widthRelTo="ABSOLUTE"
             height="1600" heightRelTo="ABSOLUTE" protect="0"/>
      <!-- 2. 테이블 위치 (treatAsChar="1" 필수!) -->
      <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1"
              allowOverlap="0" holdAnchorAndSO="0"
              vertRelTo="PARA" horzRelTo="COLUMN"
              vertAlign="TOP" horzAlign="LEFT"
              vertOffset="0" horzOffset="0"/>
      <!-- 3. 바깥/안쪽 여백 -->
      <hp:outMargin left="0" right="0" top="0" bottom="0"/>
      <hp:inMargin left="0" right="0" top="0" bottom="0"/>
      <!-- 4. 행(tr) → 셀(tc) 구조 -->
      <hp:tr>
        <hp:tc name="" header="1" hasMargin="1"
               protect="0" editable="0" dirty="1"
               borderFillIDRef="4">
          <!-- 4a. subList가 셀 콘텐츠를 감싼다 (cellAddr보다 먼저!) -->
          <hp:subList id="" textDirection="HORIZONTAL"
                      lineWrap="BREAK" vertAlign="CENTER"
                      linkListIDRef="0" linkListNextIDRef="0"
                      textWidth="0" textHeight="0"
                      hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="26" styleIDRef="0"
                  pageBreak="0" columnBreak="0" merged="0" id="...">
              <hp:run charPrIDRef="15">
                <hp:t>헤더 텍스트</hp:t>
              </hp:run>
            </hp:p>
          </hp:subList>
          <!-- 4b. 셀 주소/크기는 subList 뒤에! -->
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="21260" height="800"/>
          <hp:cellMargin left="108" right="108" top="54" bottom="54"/>
        </hp:tc>
        <hp:tc name="" header="1" hasMargin="1"
               protect="0" editable="0" dirty="1"
               borderFillIDRef="4">
          <hp:subList id="" textDirection="HORIZONTAL"
                      lineWrap="BREAK" vertAlign="CENTER"
                      linkListIDRef="0" linkListNextIDRef="0"
                      textWidth="0" textHeight="0"
                      hasTextRef="0" hasNumRef="0">
            <hp:p ...><hp:run ...><hp:t>헤더2</hp:t></hp:run></hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="1" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="21260" height="800"/>
          <hp:cellMargin left="108" right="108" top="54" bottom="54"/>
        </hp:tc>
      </hp:tr>
      <hp:tr>
        <hp:tc name="" header="0" hasMargin="1"
               protect="0" editable="0" dirty="1"
               borderFillIDRef="3">
          <hp:subList ...>
            <hp:p ...><hp:run ...><hp:t>데이터</hp:t></hp:run></hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="1"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="21260" height="800"/>
          <hp:cellMargin left="108" right="108" top="54" bottom="54"/>
        </hp:tc>
        <!-- ... -->
      </hp:tr>
    </hp:tbl>
    <hp:t></hp:t>
  </hp:run>
</hp:p>
```

#### 테이블 필수 요소 체크리스트

| 요소 | 필수 여부 | 설명 |
|------|----------|------|
| `<hp:tbl>` 속성: `zOrder`, `numberingType`, `textWrap`, `textFlow`, `noAdjust` | ✅ 필수 | 누락 시 파일 열림 오류 |
| `<hp:sz>` | ✅ 필수 | `widthRelTo="ABSOLUTE"` |
| `<hp:pos treatAsChar="1">` | ✅ 필수 | 인라인 테이블 배치 |
| `<hp:outMargin>` + `<hp:inMargin>` | ✅ 필수 | 0이어도 반드시 포함 |
| `<hp:tr>` 행 래퍼 | ✅ 필수 | 모든 셀을 행별로 감쌈 |
| `<hp:subList>` 셀 콘텐츠 래퍼 | ✅ 필수 | `<hp:cellAddr>` **이전**에 배치 |
| `<hp:tc>` 속성: `protect`, `editable`, `dirty` | ✅ 필수 | `dirty="1"` 권장 |
| `<hp:cellAddr>`, `<hp:cellSpan>`, `<hp:cellSz>` | ✅ 필수 | `<hp:subList>` **이후**에 배치 |

#### ⚠️ 흔한 테이블 오류

1. **`<hp:cellzoneList>` 사용** → 잘못됨! `<hp:tr>` 사용해야 함
2. **`<hp:subList>` 누락** → 셀 내용이 표시되지 않음
3. **`<hp:subList>`와 `<hp:cellAddr>` 순서 뒤바뀜** → 파일 손상
4. **`<hp:sz>`, `<hp:pos>` 누락** → 테이블이 렌더링되지 않음
5. **`<hp:tbl>` 내 `<hp:t></hp:t>` 누락** → run 종료 태그 이전에 빈 텍스트 필요

### 이미지 참조

이미지는 3단계로 참조된다:

1. **content.hpf** manifest에 등록:
```xml
<opf:item id="image1" href="BinData/image1.png"
          media-type="image/png" isEmbeded="1"/>
```

2. **BinData/** 폴더에 실제 파일 존재

3. **section0.xml**에서 참조:
```xml
<hc:img binaryItemIDRef="image1" bright="0" contrast="0"
        effect="REAL_PIC" alpha="0"/>
<hp:imgRect>
  <hc:pt0 x="0" y="0"/>
  <hc:pt1 x="8196" y="0"/>
  <hc:pt2 x="8196" y="3382"/>
  <hc:pt3 x="0" y="3382"/>
</hp:imgRect>
```

## secPr (섹션 속성) 주의사항

### secPr은 반드시 첫 번째 단락의 첫 번째 run에 위치

```xml
<hp:p id="..." paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" ...>
      <hp:pagePr landscape="WIDELY" width="59528" height="84186" ...>
        <hp:margin header="4252" footer="4252" gutter="0"
                   left="8504" right="8504" top="5668" bottom="4252"/>
      </hp:pagePr>
      <!-- ... footNotePr, endNotePr, pageBorderFill 등 ... -->
    </hp:secPr>
    <hp:ctrl>
      <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
    </hp:ctrl>
  </hp:run>
  <hp:run charPrIDRef="0"><hp:t></hp:t></hp:run>
</hp:p>
```

### ⚠️ lxml 직렬화 시 secPr 중복 네임스페이스 문제

lxml으로 secPr 엘리먼트를 `etree.tostring()`으로 직렬화하면 **모든 네임스페이스가 중복 선언**된다.
이를 부모 `<hs:sec>` 루트에 이미 선언된 section0.xml에 삽입하면 파일 오류가 발생할 수 있다.

```python
import re

# lxml에서 추출한 secPr
sec_pr_raw = etree.tostring(sec_pr_el, encoding='unicode')

# 중복 xmlns 선언 제거
sec_pr_clean = re.sub(r'\s+xmlns:\w+="[^"]*"', '', sec_pr_raw)
```

### ctrl (colPr) 도 함께 추출

secPr과 같은 run 안에 `<hp:ctrl>` → `<hp:colPr>`이 있다. 빠뜨리면 컬럼 설정이 손실된다.

```python
ctrl_el = first_run.find('hp:ctrl', NS)
ctrl_clean = re.sub(r'\s+xmlns:\w+="[^"]*"', '',
                    etree.tostring(ctrl_el, encoding='unicode'))
```

---

## header.xml 커스텀 스타일 주입

lxml으로 header.xml을 파싱한 뒤, 커스텀 폰트/charPr/paraPr/borderFill을 추가할 수 있다.

### 폰트 추가 (예: 맑은 고딕 = id 2)

```python
fontfaces = tree.find('.//hh:fontfaces', NS)
for ff in fontfaces.findall('hh:fontface', NS):
    cnt = int(ff.get('fontCnt', '0'))
    font = etree.SubElement(ff, '{%s}font' % NS['hh'])
    font.set('id', '2'); font.set('face', '맑은 고딕')
    font.set('type', 'TTF'); font.set('isEmbedded', '0')
    ti = etree.SubElement(font, '{%s}typeInfo' % NS['hh'])
    ti.set('familyType', 'FCAT_GOTHIC')
    # weight, proportion, contrast, strokeVariation, armStyle,
    # letterform, midline, xHeight 도 설정
    ff.set('fontCnt', str(cnt + 1))
```

### charPr 추가 (예: 28pt bold 파란색)

```python
cps = tree.find('.//hh:charProperties', NS)
cp = etree.SubElement(cps, '{%s}charPr' % NS['hh'])
cp.set('id', '7'); cp.set('height', '2800')  # 28pt = 2800
cp.set('textColor', '#1B4F72'); cp.set('bold', '1')
cp.set('shadeColor', 'none'); cp.set('useFontSpace', '0')
cp.set('useKerning', '0'); cp.set('symMark', 'NONE')
cp.set('borderFillIDRef', '2')
# fontRef, ratio, spacing, relSz, offset 하위 요소 추가
for tag in ['fontRef', 'ratio', 'spacing', 'relSz', 'offset']:
    el = etree.SubElement(cp, '{%s}%s' % (NS['hh'], tag))
    v = '2' if tag == 'fontRef' else ('100' if tag in ['ratio','relSz'] else '0')
    for lang in ['hangul','latin','hanja','japanese','other','symbol','user']:
        el.set(lang, v)
# underline, strikeout, outline, shadow 하위 요소도 추가
# itemCnt 증가
cps.set('itemCnt', str(int(cps.get('itemCnt')) + 1))
```

### paraPr 추가 (예: 중앙 정렬, 줄간 200%)

```python
pps = tree.find('.//hh:paraProperties', NS)
pp = etree.SubElement(pps, '{%s}paraPr' % NS['hh'])
pp.set('id', '20'); pp.set('tabPrIDRef', '0')
# align, heading, breakSetting, switch(case+default 안에 margin+lineSpacing), border, autoSpacing
# ⚠️ switch 안에 hp:case와 hp:default 두 개 모두 필요!
pps.set('itemCnt', str(int(pps.get('itemCnt')) + 1))
```

### borderFill 추가 (예: 파란 배경 + 흰 테두리)

```python
bfs = tree.find('.//hh:borderFills', NS)
bf = etree.SubElement(bfs, '{%s}borderFill' % NS['hh'])
bf.set('id', '4'); bf.set('threeD', '0'); bf.set('shadow', '0')
# slash, backSlash, leftBorder, rightBorder, topBorder, bottomBorder, diagonal
# fillBrush → winBrush (faceColor, hatchColor, alpha)
bfs.set('itemCnt', str(int(bfs.get('itemCnt')) + 1))
```

### lxml 직렬화 → 네임스페이스 후처리 필수

```python
new_header = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
# ZIP에 저장 후 fix_namespaces 실행 (ns0 → hh 등)
```

---

## 페이지 설정 변경 (코드)

```python
import xml.etree.ElementTree as ET
from hwpx.document import HwpxDocument

doc = HwpxDocument.open("document.hwpx")
sec = doc.sections[0]
ns = {"p": "http://www.hancom.co.kr/hwpml/2011/paragraph"}

pagePr = sec.element.find(".//p:pagePr", ns)
if pagePr is not None:
    pagePr.set("width", "59528")   # A4 너비
    pagePr.set("height", "84186")  # A4 높이
    margin = pagePr.find("p:margin", ns)
    if margin is not None:
        margin.set("left", "5669")    # 20mm
        margin.set("right", "5669")   # 20mm
        margin.set("top", "4252")     # 15mm (보고서 기준)
        margin.set("bottom", "4252")  # 15mm (보고서 기준)

doc.save("resized.hwpx")
fix_hwpx_namespaces("resized.hwpx")
```

## 호환성

- **HWPX ↔ HWP**: python-hwpx는 HWPX만 처리. 레거시 `.hwp`는 별도 도구 필요
- **한컴오피스 버전**: HWPX는 2014 이후 지원, 2021년부터 기본 포맷
- **다른 뷰어**: 제한적. 배포 시 PDF 변환 병행 권장
