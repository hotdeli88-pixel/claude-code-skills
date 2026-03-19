#!/usr/bin/env python3
"""NotebookLM query helper for Claude Code agents.

Usage:
    nlm_helper.py check-auth
    nlm_helper.py query <notebook_id> "<query>"
    nlm_helper.py sources <notebook_id>
    nlm_helper.py content <notebook_id> <source_id>
    nlm_helper.py verify-generalization <notebook_id> "<generalization>"
    nlm_helper.py multi-query <notebook_id> "<q1>" "<q2>" ...

Setup:
    pip install notebooklm-mcp-cli
    nlm login
"""
import json
import shutil
import subprocess
import sys
import os

# Auto-detect nlm CLI: venv sibling > PATH > ~/notebooklm-server/venv
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_NLM = os.path.join(_SCRIPT_DIR, "venv", "bin", "nlm")
_HOME_NLM = os.path.expanduser("~/notebooklm-server/venv/bin/nlm")

NLM_CLI = (
    _VENV_NLM if os.path.isfile(_VENV_NLM) else
    shutil.which("nlm") or
    (_HOME_NLM if os.path.isfile(_HOME_NLM) else "nlm")
)
os.environ.setdefault("NOTEBOOKLM_HL", "ko")

# Auth cache: skip repeated checks within same process
_auth_verified = False


def check_auth(silent=False):
    """Check if NotebookLM auth is valid. Returns dict with status."""
    global _auth_verified
    if _auth_verified:
        return {"status": "ok", "cached": True}
    try:
        result = subprocess.run(
            [NLM_CLI, "login", "--check"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            _auth_verified = True
            return {"status": "ok", "message": result.stdout.strip()}
        else:
            return {
                "status": "error",
                "code": "AUTH_EXPIRED",
                "message": "NotebookLM 인증 만료. 재인증 필요.",
                "fix": "/home/sdm24/notebooklm-server/venv/bin/nlm login"
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "code": "TIMEOUT", "message": "Auth check timeout"}


def run_nlm(*args, timeout=120):
    """Run nlm CLI command and return parsed output."""
    try:
        result = subprocess.run(
            [NLM_CLI, *args],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "Authentication" in stderr or "expired" in stderr or "login" in stderr:
                return {"status": "error", "message": stderr, "code": "AUTH_EXPIRED"}
            return {"status": "error", "message": stderr or result.stdout.strip(), "code": "CLI_ERROR"}
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"Timeout after {timeout}s", "code": "TIMEOUT"}
    except FileNotFoundError:
        return {"status": "error", "message": "nlm CLI not found", "code": "NOT_FOUND"}


def try_parse_json(text):
    """Try to parse JSON from CLI output."""
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def cmd_query(notebook_id, query_text):
    """Query notebook AI about sources."""
    raw = run_nlm("notebook", "query", notebook_id, query_text, "--json")
    parsed = try_parse_json(raw)
    if parsed and parsed.get("status") == "error":
        return parsed
    if parsed:
        return {"status": "ok", "answer": parsed.get("answer", str(parsed)), "sources_cited": parsed.get("sources", [])}
    # Fallback: raw text output
    if isinstance(raw, str) and raw:
        return {"status": "ok", "answer": raw, "sources_cited": []}
    return {"status": "error", "message": "Empty response", "code": "EMPTY"}


def cmd_sources(notebook_id):
    """List sources in a notebook."""
    raw = run_nlm("source", "list", notebook_id, "--json")
    parsed = try_parse_json(raw)
    if isinstance(parsed, dict) and parsed.get("status") == "error":
        return parsed
    if isinstance(parsed, list):
        return {"status": "ok", "sources": parsed}
    if isinstance(parsed, dict):
        sources = parsed.get("sources", [parsed])
        return {"status": "ok", "sources": sources}
    return {"status": "ok", "sources": [], "raw": str(raw)}


def cmd_content(notebook_id, source_id):
    """Get raw text content of a source."""
    raw = run_nlm("source", "content", source_id, "--json")
    parsed = try_parse_json(raw)
    if parsed and parsed.get("status") == "error":
        return parsed
    if parsed:
        content = parsed.get("content", str(parsed))
        return {"status": "ok", "content": content}
    return {"status": "ok", "content": str(raw)}


def cmd_verify_generalization(notebook_id, generalization):
    """Verify a generalization statement against CBCI sources."""
    prompt = (
        f"다음 일반화 진술이 이 자료의 CBCI 기준에 부합하는지 평가해주세요.\n\n"
        f"일반화 진술: \"{generalization}\"\n\n"
        f"평가 기준:\n"
        f"1. 보편성: 특정 교과를 넘어 다른 영역에도 적용 가능한가?\n"
        f"2. 추상성: 구체적 행위가 아닌 관계·원리를 진술하고 있는가?\n"
        f"3. 초월성: 특정 단원 내용을 넘어선 전이 가능한 통찰인가?\n"
        f"4. 교과특수용어가 주어·목적어에 없는가?\n\n"
        f"각 기준별 PASS/FAIL 판정과 근거를 제시하고, "
        f"개선이 필요하면 구체적 수정 제안을 해주세요."
    )
    raw = run_nlm("notebook", "query", notebook_id, prompt, "--json")
    parsed = try_parse_json(raw)
    if parsed and parsed.get("status") == "error":
        return parsed
    answer = ""
    if parsed:
        answer = parsed.get("answer", str(parsed))
    elif isinstance(raw, str):
        answer = raw
    return {"status": "ok", "evaluation": answer, "generalization": generalization}


def cmd_multi_query(notebook_id, queries):
    """Run multiple queries sequentially."""
    results = []
    for q in queries:
        r = cmd_query(notebook_id, q)
        results.append({"query": q, **r})
    all_ok = all(r.get("status") == "ok" for r in results)
    return {"status": "ok" if all_ok else "partial", "results": results}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Usage: nlm_helper.py <action> [notebook_id] [args...]",
            "code": "USAGE",
            "actions": ["check-auth", "query", "sources", "content", "verify-generalization", "multi-query"]
        }, ensure_ascii=False))
        sys.exit(1)

    action = sys.argv[1]

    # check-auth doesn't need notebook_id
    if action == "check-auth":
        result = check_auth()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] == "ok" else 1)

    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "message": "Missing notebook_id", "code": "USAGE"}, ensure_ascii=False))
        sys.exit(1)

    notebook_id = sys.argv[2]

    # Silent auth check before any API call
    auth = check_auth(silent=True)
    if auth["status"] != "ok":
        print(json.dumps(auth, ensure_ascii=False, indent=2))
        sys.exit(1)

    if action == "query":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Missing query text", "code": "USAGE"}, ensure_ascii=False))
            sys.exit(1)
        result = cmd_query(notebook_id, sys.argv[3])

    elif action == "sources":
        result = cmd_sources(notebook_id)

    elif action == "content":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Missing source_id", "code": "USAGE"}, ensure_ascii=False))
            sys.exit(1)
        result = cmd_content(notebook_id, sys.argv[3])

    elif action == "verify-generalization":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Missing generalization text", "code": "USAGE"}, ensure_ascii=False))
            sys.exit(1)
        result = cmd_verify_generalization(notebook_id, sys.argv[3])

    elif action == "multi-query":
        if len(sys.argv) < 4:
            print(json.dumps({"status": "error", "message": "Missing queries", "code": "USAGE"}, ensure_ascii=False))
            sys.exit(1)
        result = cmd_multi_query(notebook_id, sys.argv[3:])

    else:
        result = {"status": "error", "message": f"Unknown action: {action}", "code": "UNKNOWN_ACTION"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
