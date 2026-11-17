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

PLUGIN_FILES = [
    "plugin.yaml",
    "pyproject.toml",
    "__init__.py",
    "schemas.py",
    "tools.py",
]


def _upsert_env_var(env_path: Path, key: str, value: str) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updated = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            updated.append(f"{key}={value}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(f"{key}={value}")
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _read_existing_key(env_path: Path) -> str:
    if os.getenv("GEMINI_API_KEY", "").strip():
        return os.getenv("GEMINI_API_KEY", "").strip()
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val and val != "your_api_key_here":
                    return val
    return ""


def _copy_plugin(dest_plugin_dir: Path) -> None:
    dest_plugin_dir.mkdir(parents=True, exist_ok=True)
    for fname in PLUGIN_FILES:
        src = REPO_DIR / fname
        if src.exists():
            shutil.copy2(src, dest_plugin_dir / fname)

    src_skills = REPO_DIR / "skills"
    dest_skills = dest_plugin_dir / "skills"
    if src_skills.exists():
        if dest_skills.exists():
            shutil.rmtree(dest_skills)
        shutil.copytree(src_skills, dest_skills)


def _install_skill(dest_skills_root: Path) -> Path:
    src_skill = REPO_DIR / "skills" / SKILL_NAME / "SKILL.md"
    dest_dir = dest_skills_root / SKILL_NAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "SKILL.md"
    shutil.copy2(src_skill, dest_file)
    return dest_file


def main() -> int:
    print("=== Hermes-decisions Onboarding ===")
    hermes_home = Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
    hermes_env = hermes_home / ".env"

    existing = _read_existing_key(hermes_env)
    if existing:
        use_existing = input("Found existing GEMINI_API_KEY. Keep it? [Y/n]: ").strip().lower()
        api_key = existing if use_existing in {"", "y", "yes"} else ""
    else:
        api_key = ""

    while not api_key:
        print("Get a free key at: https://aistudio.google.com/docs/api-key")
        api_key = getpass.getpass("Enter your GEMINI_API_KEY (hidden): ").strip()
        if not api_key:
            print("API key cannot be empty. Please try again.")

    _upsert_env_var(hermes_env, "GEMINI_API_KEY", api_key)
    print(f"[ok] Saved GEMINI_API_KEY to {hermes_env}")

    plugin_dest = hermes_home / "plugins" / PLUGIN_NAME
    _copy_plugin(plugin_dest)
    print(f"[ok] Installed Hermes plugin to {plugin_dest}")

    hermes_skill_path = _install_skill(hermes_home / "skills")
    print(f"[ok] Installed Hermes skill to {hermes_skill_path}")

    extra_harnesses = input("Also install SKILL.md for Claude Code / Codex if present? [y/N]: ").strip().lower()
    if extra_harnesses in {"y", "yes"}:
        for name, root in [
            ("Claude Code", Path.home() / ".claude" / "skills"),
            ("Codex", Path.home() / ".codex" / "skills"),
        ]:
            path = _install_skill(root)
            print(f"[ok] Installed {name} skill to {path}")

    if shutil.which("hermes"):
        print("Enabling plugin via Hermes CLI...")
        subprocess.run(["hermes", "plugins", "enable", PLUGIN_NAME], check=False)
    else:
        print("Note: 'hermes' CLI not found on PATH. Once installed, run: hermes plugins enable hermes-decisions")

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
