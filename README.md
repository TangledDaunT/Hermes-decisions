# Hermes-decisions

A native [Hermes Agent](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) plugin (`plugin.yaml` v2) and bundled `SKILL.md` for Google's **Gemini Decisions API** (`gemini-decision-1`).

Exposes the `gemini_decide` tool so Hermes (and other `SKILL.md`-compatible harnesses like Claude Code and Codex) can evaluate up to 1,000 structured `noul` (yes/no), `choice` (multiple-choice), and `score` (rubric) questions in a single zero-output-token pass over text, JSON, images, PDFs, audio, and video.

## Quick Onboarding

Run the interactive onboarding script:

```bash
python3 onboard.py
```

The onboarding CLI will:
1. Prompt for your `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/docs/api-key)) and save it to `~/.hermes/.env`.
2. Install the native plugin into `~/.hermes/plugins/hermes-decisions/`.
3. Install `SKILL.md` into `~/.hermes/skills/gemini-decisions/SKILL.md` (and optionally `~/.claude/skills/` and `~/.codex/skills/`).
4. Enable `hermes-decisions` via `hermes plugins enable hermes-decisions` and optionally run a live verification check.

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
