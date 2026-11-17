"""Hermes-decisions plugin registration."""

from pathlib import Path

from . import schemas, tools


def register(ctx):
    """Register the gemini_decide tool and its bundled workflow skill with Hermes Agent."""
    ctx.register_tool(
        name="gemini_decide",
        toolset="decisions",
        schema=schemas.GEMINI_DECIDE,
        handler=tools.gemini_decide,
    )

    skill_md = Path(__file__).parent / "skills" / "gemini-decisions" / "SKILL.md"
    if skill_md.exists():
        ctx.register_skill("gemini-decisions", skill_md)
