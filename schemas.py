"""Tool schemas for the Hermes-decisions plugin."""

GEMINI_DECIDE = {
    "name": "gemini_decide",
    "description": (
        "Evaluate up to 1,000 structured yes/no ('noul'), multiple-choice ('choice'), or rubric ('score') "
        "questions in a single zero-output-token forward pass using Google's Gemini Decisions API "
        "(gemini-decision-1). Accepts text/JSON strings and multimodal file paths (images, PDFs, audio, "
        "video, or text files) and returns calibrated probabilities and confidence scores."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "object",
                "description": (
                    "Map of question_id -> question spec. Each spec has 'type' ('noul', 'choice', or 'score') "
                    "and 'instructions' (string). 'choice' also requires 'criteria' (dict of option_id -> description, "
                    "2 to 255 options). 'score' requires 'criteria' (ordered rubric levels, 2 to 255 levels)."
                ),
            },
            "text": {
                "type": "string",
                "description": "Optional shared text or serialized JSON input to evaluate against the questions.",
            },
            "json_input": {
                "type": "object",
                "description": "Optional structured JSON object to serialize and include as shared input.",
            },
            "files": {
                "type": "array",
                "description": (
                    "Optional list of local file paths (or objects with 'path' and optional 'resolution': "
                    "'low'|'medium'|'high'|'ultra_high') for images, PDFs, audio, video, or text files."
                ),
                "items": {
                    "type": ["string", "object"],
                },
            },
            "resolution": {
                "type": "string",
                "enum": ["low", "medium", "high", "ultra_high"],
                "description": "Default resolution for image/video inputs (default: 'medium').",
            },
        },
        "required": ["questions"],
    },
}
