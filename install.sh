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
echo "[4/4] Python 의존성 확인..."
pip install python-hwpx lxml python-docx 2>/dev/null && echo "  -> 의존성 설치 완료" || echo "  ⚠ pip install 실패 — 수동 설치 필요: pip install python-hwpx lxml python-docx"

echo ""
echo "=== 설치 완료 ==="
echo "Claude Code에서 /hwpx, /cbci-unit-design, /rjcbci 등 사용 가능"
