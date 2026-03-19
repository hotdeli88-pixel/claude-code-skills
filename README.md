# Claude Code Skills - CBCI & HWPX 교육용 스킬 모음

전북형 개념기반 탐구학습(CBCI) 단원설계 및 HWPX 한글문서 자동화를 위한 Claude Code 커스텀 스킬/커맨드 모음입니다.

## 스킬 목록

### HWPX 문서 자동화
| 커맨드 | 용도 |
|--------|------|
| `/hwpx` | HWPX 문서 생성·편집·템플릿 치환·테마 변경 |
| `/hwpx-template-fill` | HWPX 템플릿에 데이터 자동 매핑 |
| `/hwpx-table-format` | HWPX 표 셀서식 통일 |
| `/mhwpx` | DOCX→HWPX 수식 변환 |

### CBCI 단원설계
| 커맨드 | 용도 |
|--------|------|
| `/cbci-unit-design` | 전북형 CBCI 단원설계 생성 (DOCX) |
| `/cbci-unit-eval` | 단원설계 루브릭 기반 평가 (MD) |
| `/cbci-worksheet` | 차시별 학생용 활동지 생성 (DOCX) |
| `/rjcbci` | 단원설계 3단계 검증·개선·재검증 (5개 전문가 에이전트) |

### 교육 플랫폼 연동
| 커맨드 | 용도 |
|--------|------|
| `/aiep` | AIEP(ai.jbedu.kr) 수업·학생·콘텐츠 관리 |
| `/aiep-authoring` | AIEP LCMS 저작도구 콘텐츠 자동 생성 |
| `/notebooklm` | Google NotebookLM 소스 기반 질의·검증 |

### 기타
| 커맨드 | 용도 |
|--------|------|
| `/gyosu-hakseup-plan` | 교수학습 및 평가 운영 계획 HWPX 생성 |
| `/check-hakbu` | 학교생활기록부 PDF 점검 |

## 설치 방법

```bash
# 1. 이 레포를 클론
git clone https://github.com/hotdeli88-pixel/claude-code-skills.git

# 2. 설치 스크립트 실행
cd claude-code-skills
bash install.sh
```

또는 수동으로:
```bash
# 커맨드 복사
cp commands/*.md ~/.claude/commands/

# 스킬 복사
cp -r skills/* ~/.claude/skills/

# 설정 복사 (기존 설정과 병합 필요)
# cp settings.json ~/.claude/settings.json

# 메모리 복사 (선택)
# cp memory/* ~/.claude/projects/<프로젝트경로>/memory/
```

## 의존성

```bash
pip install python-hwpx lxml python-docx
```

## 디렉토리 구조

```
claude-code-skills/
├── commands/          # 슬래시 커맨드 (*.md)
├── skills/            # 스킬 디렉토리
│   ├── hwpx/          # HWPX 코어 (SKILL.md, scripts, assets, references)
│   ├── gyosu-hakseup-plan/  # 교수학습계획 (SKILL.md, templates, scripts)
│   ├── cbci-unit-design/    # CBCI 단원설계 (framework, scripts)
│   ├── cbci-unit-eval/      # CBCI 평가 (rubric criteria)
│   ├── hwpx-table-format/   # 표 서식 통일 (scripts)
│   ├── hwpx-template-fill/  # 템플릿 매핑
│   └── mhwpx/               # 수식 변환 (scripts, references)
├── memory/            # Auto Memory (프로젝트 컨텍스트)
├── settings.json      # Claude Code 설정
├── settings.local.json.example  # 로컬 권한 예시
└── install.sh         # 설치 스크립트
```
