import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from openai import OpenAI


REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL = os.getenv("AI_AUTOFIX_MODEL", "gpt-4o-mini")


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def get_compile_errors() -> str:
    result = run_cmd(["python", "-m", "compileall", "-q", "."])
    if result.returncode == 0:
        return ""
    return (result.stdout + "\n" + result.stderr).strip()


def list_repo_files() -> List[str]:
    result = run_cmd(["git", "ls-files"])
    files = result.stdout.splitlines()
    allowed_ext = (".py", ".md", ".yml", ".yaml", ".sql", ".toml", ".txt", ".json")
    return [f for f in files if f.endswith(allowed_ext)]


def build_prompt(errors: str, files: List[str]) -> str:
    files_block = "\n".join(files[:500])
    return f"""
You are an autonomous code maintenance bot. Fix the errors below.

ERROR LOG:
{errors}

REPO FILES (subset):
{files_block}

Return JSON only:
{{
  "files": [
    {{
      "path": "relative/path/file.py",
      "content": "FULL FILE CONTENT HERE"
    }}
  ]
}}

Rules:
- Only modify existing files from the repo list.
- Keep changes minimal to fix the error.
- If you cannot safely fix, return {{"files": []}}.
""".strip()


def apply_changes(changes: List[Dict[str, Any]]) -> int:
    applied = 0
    for item in changes:
        path = item.get("path", "")
        content = item.get("content", "")
        if not path or not isinstance(content, str):
            continue
        target = (REPO_ROOT / path).resolve()
        if not target.is_file():
            continue
        if REPO_ROOT not in target.parents:
            continue
        target.write_text(content, encoding="utf-8")
        applied += 1
    return applied


def main() -> int:
    errors = get_compile_errors()
    if not errors:
        print("✅ No compile errors detected.")
        return 0

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("❌ OPENAI_API_KEY not set.")
        return 1

    files = list_repo_files()
    prompt = build_prompt(errors, files)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response.")
        print(raw)
        return 1

    changes = data.get("files", [])
    if not changes:
        print("⚠️ AI returned no changes.")
        return 0

    applied = apply_changes(changes)
    print(f"✅ Applied changes to {applied} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
