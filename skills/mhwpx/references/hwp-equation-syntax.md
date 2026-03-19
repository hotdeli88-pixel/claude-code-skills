# HWP 수식 편집기 스크립트 문법 레퍼런스

## 1. 기본 구조

- 수식은 HWPX에서 `hp:equation > hp:script` 요소에 텍스트로 저장
- 한글(한컴오피스)의 수식 편집기가 이 스크립트를 파싱하여 수식을 렌더링
- Equation Version 60 기준

## 2. 기본 문법

### 2.1 그룹화

- `{내용}` : 중괄호로 그룹화
- 예: `{a + b}`, `{x^2 + 1}`

### 2.2 분수

- `{분자} over {분모}` : 분수 표현
- 예: `{1} over {2}` → 1/2
- 예: `{x + 1} over {x - 1}` → (x+1)/(x-1)

### 2.3 위첨자/아래첨자

- `^숫자` 또는 `^{그룹}` : 위첨자
- `_숫자` 또는 `_{그룹}` : 아래첨자
- 예: `x^2`, `x^{10}`, `a_1`, `a_{ij}`
- 위첨자+아래첨자 동시: `x_1^2`

### 2.4 제곱근

- `sqrt {내용}` : 제곱근
- 예: `sqrt {x}` → √x
- 예: `sqrt {x^2 + 1}` → √(x²+1)
- n제곱근: `root n of {내용}` (예: `root 3 of {8}`)

### 2.5 괄호

- `LEFT ( 내용 RIGHT )` : 크기 자동 조정 괄호
- `LEFT [ 내용 RIGHT ]` : 대괄호
- `LEFT { 내용 RIGHT }` : 중괄호
- `LEFT | 내용 RIGHT |` : 절댓값
- 예: `LEFT ( {1} over {2} RIGHT )` → (1/2) 크기 맞춤

### 2.6 공백

- `` ` `` (백틱) : 작은 공백
- `` `` `` `` `` : 중간 공백
- `~` : 약간의 공백 (수식 내부)

### 2.7 폰트 지시자

- `rm` : 로마체(Roman, 직립) — `rmA`, `rmcm`
- `RM` : 로마체(대문자 전체) — 기하 선분에 사용
- `bold` : 굵게 — `bold {y = 2x + 3}`
- `it` : 이탤릭체
- 기본: 수식 내 소문자는 이탤릭, 대문자는 직립

## 3. 특수 기호

### 3.1 연산자

| 명령어 | 기호 | 용도 |
|---|---|---|
| `TIMES` | × | 곱셈 |
| `DIV` | ÷ | 나눗셈 |
| `pm` 또는 `+-` | ± | 플러스마이너스 |
| `mp` | ∓ | 마이너스플러스 |
| `CDOTS` / `cdots` | ⋯ | 가운데 줄임표 |
| `LDOTS` / `ldots` | … | 아래 줄임표 |

### 3.2 관계 연산자

| 명령어 | 기호 |
|---|---|
| `=` | = |
| `<>` 또는 `!=` | ≠ |
| `<=` | ≤ |
| `>=` | ≥ |
| `<<` | ≪ |
| `>>` | ≫ |
| `APPROX` | ≈ |
| `EQUIV` | ≡ |
| `PROP` | ∝ |

### 3.3 그리스 문자

| 소문자 | 대문자 |
|---|---|
| `alpha` α | `ALPHA` Α |
| `beta` β | `BETA` Β |
| `gamma` γ | `GAMMA` Γ |
| `delta` δ | `DELTA` Δ |
| `theta` θ | `THETA` Θ |
| `pi` π | `PI` Π |
| `sigma` σ | `SIGMA` Σ |
| `omega` ω | `OMEGA` Ω |

### 3.4 논리/집합 기호

| 명령어 | 기호 |
|---|---|
| `THEREFORE` | ∴ |
| `BECAUSE` | ∵ |
| `FORALL` | ∀ |
| `EXISTS` | ∃ |
| `IN` | ∈ |
| `SUBSET` | ⊂ |
| `UNION` | ∪ |
| `INTERSECTION` | ∩ |
| `EMPTYSET` | ∅ |

### 3.5 기하 기호

| 명령어 | 기호 | 용도 |
|---|---|---|
| `bar {AB}` | AB̄ | 선분 |
| `angle` 또는 `#` | ∠ | 각도 |
| `//` | ∥ | 평행 |
| `PERP` | ⊥ | 수직 |
| `arch {AB}` | ⌢AB | 호 |
| `DEG` | ° | 도 |

## 4. 고급 구문

### 4.1 행렬

```
LEFT ( matrix { a # b ## c # d } RIGHT )
```

- `#` : 열 구분
- `##` : 행 구분

### 4.2 연립방정식

```
LEFT { pile { x + y = 5 # x - y = 1 } RIGHT .
```

- `pile` : 수직 스택
- `RIGHT .` : 오른쪽 괄호 없음

### 4.3 적분/시그마

```
INT _{a}^{b} f(x) dx
SUM _{i=1}^{n} a_i
PROD _{i=1}^{n} a_i
```

### 4.4 극한

```
lim _{x -> INF} f(x)
lim _{x -> 0} {sin x} over {x}
```

### 4.5 삼각함수

- `sin`, `cos`, `tan`, `csc`, `sec`, `cot`
- `arcsin`, `arccos`, `arctan`
- `log`, `ln`, `exp`
- 예: `sin^{2} theta + cos^{2} theta = 1`

## 5. HWPX XML 구조

### 5.1 인라인 수식 요소

```xml
<hp:run charPrIDRef="0">
  <hp:equation id="1000000001"
               version="Equation Version 60"
               baseLine="85"
               textColor="#000000"
               baseUnit="1100"
               lineMode="CHAR"
               font="HYhwpEQ"
               zOrder="0"
               numberingType="EQUATION"
               textWrap="TOP_AND_BOTTOM"
               textFlow="BOTH_SIDES"
               lock="0"
               dropcapstyle="None">
    <hp:sz width="3916" widthRelTo="ABSOLUTE" height="1125" heightRelTo="ABSOLUTE" protect="0"/>
    <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
            holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA"
            vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
    <hp:outMargin left="56" right="56" top="0" bottom="0"/>
    <hp:script>sqrt {x^2 + 1}</hp:script>
  </hp:equation>
</hp:run>
```

### 5.2 핵심 속성

| 속성 | 값 | 설명 |
|---|---|---|
| version | "Equation Version 60" | 수식 엔진 버전 |
| baseLine | "85" | 기준선 오프셋 (%) |
| textColor | "#000000" | 수식 텍스트 색상 |
| baseUnit | "1000"~"1100" | 기본 폰트 크기 (HWP 단위) |
| lineMode | "CHAR" | 줄 모드 |
| font | "HYhwpEQ" | 수식 폰트 |
| treatAsChar | "1" | 인라인 수식 (1=인라인) |

### 5.3 혼합 텍스트+수식 구조

한 단락에 텍스트와 수식이 섞인 경우:

```xml
<hp:p paraPrIDRef="0" styleIDRef="0">
  <hp:run charPrIDRef="0">
    <hp:equation ...>
      <hp:script>sqrt {(-3)^{2}}</hp:script>
    </hp:equation>
  </hp:run>
  <hp:run charPrIDRef="0">
    <hp:t> 의 값을 구하고, 풀이 과정을 서술하시오.</hp:t>
  </hp:run>
</hp:p>
```

## 6. 유니코드 → HWP 스크립트 변환 매핑

### 6.1 기본 변환

| 유니코드 | HWP 스크립트 |
|---|---|
| √ (U+221A) | sqrt |
| ² (U+00B2) | ^{2} |
| ³ (U+00B3) | ^{3} |
| ⁴ (U+2074) | ^{4} |
| ¹ (U+00B9) | ^{1} |
| ⁰ (U+2070) | ^{0} |
| \| (pipe) | LEFT \| ... RIGHT \| (절댓값 맥락) |

### 6.2 복합 변환 예시

| 원본 | 변환 결과 | 설명 |
|---|---|---|
| √((-3)²) | sqrt {(-3)^{2}} | 중첩 괄호+위첨자 |
| √(a²) = \|a\| | sqrt {a^{2}} = LEFT \| a RIGHT \| | 제곱근+절댓값 |
| (-5)² = -5 | (-5)^{2} = -5 | 괄호식+위첨자 |
| 3/5 | {3} over {5} | 분수 (향후 확장) |
| AB | bar {AB} | 선분 (향후 확장) |
