#!/bin/bash
# Claude Code Skills 설치 스크립트
# 사용법: bash install.sh

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Claude Code Skills 설치 ==="
echo "설치 경로: $CLAUDE_DIR"
echo ""

# 1. 커맨드 설치
echo "[1/4] 커맨드 설치..."
mkdir -p "$CLAUDE_DIR/commands"
cp "$SCRIPT_DIR/commands/"*.md "$CLAUDE_DIR/commands/"
echo "  -> $(ls "$SCRIPT_DIR/commands/"*.md | wc -l)개 커맨드 설치 완료"

# 2. 스킬 설치
echo "[2/4] 스킬 설치..."
mkdir -p "$CLAUDE_DIR/skills"
for skill_dir in "$SCRIPT_DIR/skills/"*/; do
    skill_name=$(basename "$skill_dir")
    cp -r "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
    echo "  -> $skill_name"
done
echo "  스킬 설치 완료"

# 3. 설정 병합 안내
echo "[3/4] 설정 파일..."
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    echo "  ⚠ 기존 settings.json 발견 — 수동 병합 필요"
    echo "  참조: $SCRIPT_DIR/settings.json"
else
    cp "$SCRIPT_DIR/settings.json" "$CLAUDE_DIR/settings.json"
    echo "  -> settings.json 설치 완료"
fi

# 4. Python 의존성
echo "[4/5] Python 의존성 확인..."
pip install python-hwpx lxml python-docx 2>/dev/null && echo "  -> 의존성 설치 완료" || echo "  ⚠ pip install 실패 — 수동 설치 필요: pip install python-hwpx lxml python-docx"

# 5. NotebookLM 헬퍼 설치
echo "[5/5] NotebookLM 헬퍼..."
NLM_DIR="$HOME/notebooklm-server"
mkdir -p "$NLM_DIR"
cp "$SCRIPT_DIR/notebooklm-server/nlm_helper.py" "$NLM_DIR/"
chmod +x "$NLM_DIR/nlm_helper.py"
if [ ! -d "$NLM_DIR/venv" ]; then
    echo "  venv 생성 + notebooklm-mcp-cli 설치..."
    python3 -m venv "$NLM_DIR/venv" 2>/dev/null && \
    "$NLM_DIR/venv/bin/pip" install -q notebooklm-mcp-cli 2>/dev/null && \
    echo "  -> 설치 완료" || \
    echo "  ⚠ 자동 설치 실패 — 수동 실행: cd ~/notebooklm-server && bash setup.sh"
else
    echo "  -> venv 이미 존재, nlm_helper.py만 갱신"
fi

echo ""
echo "=== 설치 완료 ==="
echo "Claude Code에서 /hwpx, /cbci-unit-design, /rjcbci 등 사용 가능"
echo ""
echo "[선택] NotebookLM 로그인: ~/notebooklm-server/venv/bin/nlm login"
