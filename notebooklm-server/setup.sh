#!/bin/bash
# NotebookLM 헬퍼 설치 스크립트
# 사용법: bash setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== NotebookLM 헬퍼 설치 ==="

# 1. venv 생성 + notebooklm-mcp-cli 설치
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "[1/3] Python venv 생성..."
    python3 -m venv "$SCRIPT_DIR/venv"
else
    echo "[1/3] venv 이미 존재"
fi

echo "[2/3] notebooklm-mcp-cli 설치..."
"$SCRIPT_DIR/venv/bin/pip" install -q notebooklm-mcp-cli

echo "[3/3] 인증..."
echo "  다음 명령으로 Google 로그인을 진행하세요:"
echo ""
echo "    $SCRIPT_DIR/venv/bin/nlm login"
echo ""
echo "=== 설치 완료 ==="
echo "nlm_helper.py는 자동으로 venv/bin/nlm을 감지합니다."
