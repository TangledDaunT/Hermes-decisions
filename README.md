# Hermes-decisions

A native [Hermes Agent](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) plugin (`plugin.yaml` v2) and bundled `SKILL.md` for Google's **Gemini Decisions API** (`gemini-decision-1`).

Exposes the `gemini_decide` tool so Hermes (and other `SKILL.md`-compatible harnesses like Claude Code and Codex) can evaluate up to 1,000 structured `noul` (yes/no), `choice` (multiple-choice), and `score` (rubric) questions in a single zero-output-token pass over text, JSON, images, PDFs, audio, and video.

## Quick Onboarding

Install the plugin via the Hermes CLI:

```bash
hermes plugins install hermes-decisions
```

Then set your API key and enable the plugin:

```bash
hermes config set GEMINI_API_KEY <your-key-from-google-ai-studio>
hermes plugins enable hermes-decisions
```

Get a free key at: https://aistudio.google.com/docs/api-key

### Optional: Install the skill for Claude Code / Codex

The bundled skill can also be installed for other harnesses:

```bash
# For Claude Code
mkdir -p ~/.claude/skills/gemini-decisions
cp skills/gemini-decisions/SKILL.md ~/.claude/skills/gemini-decisions/

# For Codex
mkdir -p ~/.codex/skills/gemini-decisions
cp skills/gemini-decisions/SKILL.md ~/.codex/skills/gemini-decisions/
```

## Tool Usage (`gemini_decide`)

```json
{
  "json_input": {"order_id": "ORD-42", "amount": 15},
  "text": "Customer requested a refund due to damaged packaging.",
  "files": ["/path/to/photo.jpg"],
  "questions": {
    "approve_refund": {
      "type": "noul",
      "instructions": "Does the photo show damaged packaging justifying a refund?"
    },
    "category": {
      "type": "choice",
      "instructions": "Select the issue category.",
      "criteria": {
        "damaged": "Physical damage visible",
        "wrong_item": "Incorrect item delivered",
        "other": "Other reason"
      }
    }
  }
}
```