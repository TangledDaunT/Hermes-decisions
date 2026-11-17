---
name: gemini-decisions
description: Use the Gemini Decisions API (gemini-decision-1) via the gemini_decide tool for fast, zero-output-token yes/no (noul), multiple-choice (choice), and rubric (score) evaluations over text, JSON, images, PDFs, audio, and video.
version: 1.0.0
---

# Gemini Decisions Skill

Use `gemini_decide` whenever a task needs fast, calibrated, closed-set decisions rather than open-ended text generation:

* **Routing & triage:** Classify user intents, support tickets, or leads into fixed categories (`choice`).
* **Guardrails & verification:** Run up to 1,000 yes/no (`noul`) policy, safety, or state-verification checks in a single forward pass.
* **Rubric grading:** Score candidates or outputs on an ordered scale (`score`).
* **Multimodal inspection:** Evaluate images, PDFs, audio, or video directly without separate OCR or transcription.

## Question Formats

Pass a JSON object to `questions`:

```json
{
  "is_urgent": {
    "type": "noul",
    "instructions": "Is this request urgent or time-sensitive?"
  },
  "department": {
    "type": "choice",
    "instructions": "Which team should handle this?",
    "criteria": {
      "billing": "Invoices, refunds, or payment issues",
      "support": "Technical troubleshooting or bugs",
      "other": "Anything else"
    }
  },
  "quality": {
    "type": "score",
    "instructions": "Rate clarity from 1 (unclear) to 5 (crystal clear).",
    "criteria": {
      "1": "Very unclear",
      "2": "Somewhat unclear",
      "3": "Acceptable",
      "4": "Clear",
      "5": "Crystal clear"
    }
  }
}
```

## Inputs

* `text`: Plain text or serialized context.
* `json_input`: Structured JSON object to evaluate.
* `files`: List of local file paths (or `{"path": "...", "resolution": "low|medium|high"}`) for images, PDFs, audio, video, or text files.
* Batch all related questions against the same shared input in a single `gemini_decide` call to save latency and quota.
