# 교수학습 및 평가 운영 계획 HWPX 생성 스킬

## 개요

2026학년도 교수학습 및 평가 운영 계획 양식(중_배포용) HWPX 템플릿을 기반으로
교과별 교수학습-평가 운영 계획 문서를 자동 생성하는 스킬.

- **범용**: 수학, 국어, 영어, 사회, 과학 등 모든 교과에서 사용 가능
- **2가지 모드**: DOCX 변환 (Mode A) / 대화 입력 (Mode B)
- **출력**: 완성된 HWPX 파일

## 파일 구조

```
~/.claude/skills/gyosu-hakseup-plan/
  SKILL.md                          # 이 문서
  assets/
    template.hwpx                   # 배포용 양식 템플릿
    template_header_row.xml         # 8열 헤더행 XML 템플릿
    template_data_row.xml           # 8열 데이터행 XML 템플릿
  references/
    template-structure.md           # 템플릿 HWPX 내부 구조
    curriculum-data-format.md       # JSON 데이터 스키마
  scripts/
    generate_hwpx.py                # 핵심: JSON → HWPX
    parse_docx_input.py             # DOCX → JSON 추출
```

## 스크립트 사용법

### generate_hwpx.py
```bash
python generate_hwpx.py --data data.json --output result.hwpx
python generate_hwpx.py --data data.json --template custom.hwpx --output result.hwpx
```

### parse_docx_input.py
```bash
python parse_docx_input.py --docx input.docx --output data.json
python parse_docx_input.py --analyze --docx input.docx
```

## 핵심 기술 사항

| 항목 | 값 |
|------|-----|
| 템플릿 | template.hwpx (배포용 양식) |
| 8열 너비 | [4742, 3613, 3614, 7122, 14380, 12350, 22255, 4331] |
| 헤더 borderFillIDRef | 55 |
| 데이터 borderFillIDRef | 4 |
| 네임스페이스 후처리 | fix_namespaces.py (hwpx 스킬에서 참조) |
| Python | python (3.14) |

## 의존성

- lxml (XML 파싱)
- python-docx (DOCX 파싱, Mode A)
- fix_namespaces.py (hwpx 스킬)
