#!/usr/bin/env python3
"""Interactive onboarding CLI for the Hermes-decisions plugin and skill."""

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_NAME = "hermes-decisions"
SKILL_NAME = "gemini-decisions"
REPO_DIR = Path(__file__).resolve().parent


def _install_skill(dest_skills_root: Path) -> Path:
    src_skill = REPO_DIR / "skills" / SKILL_NAME / "SKILL.md"
    dest_dir = dest_skills_root / SKILL_NAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "SKILL.md"
    shutil.copy2(src_skill, dest_file)
    return dest_file


def main() -> int:
    print("=== Hermes-decisions Onboarding ===")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Get a free key at: https://aistudio.google.com/docs/api-key")
        while not api_key:
            api_key = getpass.getpass("Enter your GEMINI_API_KEY (hidden): ").strip()
            if not api_key:
                print("API key cannot be empty. Please try again.")

    if shutil.which("hermes"):
        print("Setting GEMINI_API_KEY via Hermes CLI...")
        subprocess.run(["hermes", "config", "set", "GEMINI_API_KEY", api_key], check=False)
        print("Installing plugin via Hermes CLI...")
        subprocess.run(["hermes", "plugins", "install", PLUGIN_NAME], check=False)
        print("Enabling plugin via Hermes CLI...")
        subprocess.run(["hermes", "plugins", "enable", PLUGIN_NAME], check=False)
    else:
        print("Note: 'hermes' CLI not found on PATH.")
        print("Once installed, run:")
        print(f"  hermes config set GEMINI_API_KEY {api_key}")
        print(f"  hermes plugins install {PLUGIN_NAME}")
        print(f"  hermes plugins enable {PLUGIN_NAME}")

    extra_harnesses = input("Also install SKILL.md for Claude Code / Codex if present? [y/N]: ").strip().lower()
    if extra_harnesses in {"y", "yes"}:
        for name, root in [
            ("Claude Code", Path.home() / ".claude" / "skills"),
            ("Codex", Path.home() / ".codex" / "skills"),
        ]:
            path = _install_skill(root)
            print(f"[ok] Installed {name} skill to {path}")

    verify = input("Run a quick live API check with gemini-decision-1? [Y/n]: ").strip().lower()
    if verify in {"", "y", "yes"}:
        os.environ["GEMINI_API_KEY"] = api_key
        sys.path.insert(0, str(REPO_DIR.parent))
        import importlib
        tools_mod = importlib.import_module("Hermes-decisions.tools") if (REPO_DIR.parent / "Hermes-decisions" / "tools.py").exists() else None
        if tools_mod is None:
            import tools as tools_mod  # type: ignore
        out = tools_mod.gemini_decide({
            "text": "Onboarding verification ping.",
            "questions": {"ok": {"type": "noul", "instructions": "Is this a valid test message?"}},
        })
        print(f"Verification response: {out}")

    print("\nDone! Restart Hermes (or start a new session) to use `gemini_decide`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())