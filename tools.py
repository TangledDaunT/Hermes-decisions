"""Tool handler for the Gemini Decisions API (gemini-decision-1)."""

import base64
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

TEXT_MIME_PREFIXES = ("text/",)
TEXT_MIME_EXACT = {
    "application/json",
    "application/xml",
    "application/javascript",
    "application/csv",
}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
AUDIO_MIMES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/aac",
    "audio/flac",
    "audio/mp4",
}
VIDEO_MIMES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}


def _get_api_key() -> str:
    try:
        from agent.secret_scope import get_secret  # type: ignore

        val = (get_secret("GEMINI_API_KEY") or "").strip()
        if val:
            return val
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "").strip()


def _detect_mime(path: Path, explicit_mime: Optional[str] = None) -> str:
    if explicit_mime:
        mime = explicit_mime.split(";")[0].strip().lower()
    else:
        guessed, _ = mimetypes.guess_type(str(path))
        mime = (guessed or "application/octet-stream").lower()
    if mime == "image/jpg":
        mime = "image/jpeg"
    if mime == "audio/mp3":
        mime = "audio/mpeg"
    return mime


def _build_file_block(entry: Any, default_resolution: str) -> Dict[str, Any]:
    if isinstance(entry, str):
        raw_path, explicit_mime, res = entry, None, default_resolution
    elif isinstance(entry, dict):
        raw_path = str(entry.get("path", "")).strip()
        explicit_mime = entry.get("mime_type")
        res = str(entry.get("resolution") or default_resolution)
    else:
        raise ValueError(f"Unsupported file entry: {entry!r}")

    if not raw_path:
        raise ValueError("File entry is missing 'path'.")

    path = Path(raw_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    raw_bytes = path.read_bytes()
    if not raw_bytes:
        raise ValueError(f"File is empty: {path}")

    mime = _detect_mime(path, explicit_mime)
    encoded = base64.b64encode(raw_bytes).decode("ascii")

    if mime in IMAGE_MIMES:
        block: Dict[str, Any] = {"type": "image", "data": encoded, "mime_type": mime}
        if res in {"low", "medium", "high", "ultra_high"}:
            block["resolution"] = res
        return block
    if mime == "application/pdf":
        return {"type": "document", "data": encoded, "mime_type": "application/pdf"}
    if mime in AUDIO_MIMES or mime.startswith("audio/"):
        return {"type": "audio", "data": encoded, "mime_type": mime}
    if mime in VIDEO_MIMES or mime.startswith("video/"):
        block = {"type": "video", "data": encoded, "mime_type": mime}
        if res in {"low", "medium", "high", "ultra_high"}:
            block["resolution"] = res
        return block
    if mime.startswith(TEXT_MIME_PREFIXES) or mime in TEXT_MIME_EXACT:
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1")
        return {"type": "text", "text": f"File ({path.name}):\n{content}\n"}

    raise ValueError(f"Unsupported file type '{mime}' for {path.name}")


def _serialize_answer(ans: Any) -> Dict[str, Any]:
    ans_type = getattr(ans, "type", None)
    confidence = round(float(getattr(ans, "confidence", 0.0) or 0.0), 4)
    if ans_type == "noul" or hasattr(ans, "noul"):
        yes_prob = round(float(ans.noul), 4)
        return {
            "type": "noul",
            "decision": "Yes" if yes_prob >= 0.5 else "No",
            "yes_probability": yes_prob,
            "no_probability": round(1.0 - yes_prob, 4),
            "confidence": confidence,
        }
    if ans_type == "choice" or hasattr(ans, "choice"):
        probs = {k: round(float(v), 4) for k, v in (getattr(ans, "probabilities", {}) or {}).items()}
        return {
            "type": "choice",
            "choice": ans.choice,
            "probabilities": probs,
            "confidence": confidence,
        }
    if ans_type == "score" or hasattr(ans, "score"):
        probs = {str(k): round(float(v), 4) for k, v in (getattr(ans, "probabilities", {}) or {}).items()}
        return {
            "type": "score",
            "score": round(float(ans.score), 4),
            "probabilities": probs,
            "confidence": confidence,
        }
    return {"raw": str(ans), "confidence": confidence}


def gemini_decide(args: dict, **kwargs) -> str:
    """Evaluate structured noul/choice/score questions with gemini-decision-1. Always returns JSON."""
    try:
        api_key = _get_api_key()
        if not api_key:
            return json.dumps({
                "ok": False,
                "error": "Missing GEMINI_API_KEY. Run onboard.py or set GEMINI_API_KEY in your environment/.env.",
            })

        questions = args.get("questions")
        if isinstance(questions, str):
            questions = json.loads(questions)
        if not isinstance(questions, dict) or not questions:
            return json.dumps({
                "ok": False,
                "error": "'questions' must be a non-empty JSON object mapping question IDs to noul/choice/score specs.",
            })

        default_res = str(args.get("resolution") or "medium").strip().lower()
        input_blocks: List[Dict[str, Any]] = []

        text_val = args.get("text")
        if isinstance(text_val, str) and text_val.strip():
            input_blocks.append({"type": "text", "text": text_val.strip()})

        json_input = args.get("json_input")
        if json_input is not None:
            if isinstance(json_input, str):
                input_blocks.append({"type": "text", "text": f"JSON Input:\n{json_input}"})
            else:
                input_blocks.append({"type": "text", "text": f"JSON Input:\n{json.dumps(json_input, indent=2)}"})

        files = args.get("files") or []
        if isinstance(files, (str, dict)):
            files = [files]
        for entry in files:
            input_blocks.append(_build_file_block(entry, default_res))

        if not input_blocks:
            input_blocks.append({"type": "text", "text": "Evaluate the provided questions."})

        from google import genai

        client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        started = time.perf_counter()
        result = client.decisions.create(
            model="gemini-decision-1",
            input=input_blocks,
            questions=questions,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        answers = {
            qid: _serialize_answer(ans)
            for qid, ans in (getattr(result, "answers", {}) or {}).items()
        }
        usage = getattr(result, "usage", None)
        return json.dumps({
            "ok": True,
            "model": "gemini-decision-1",
            "answers": answers,
            "latency_ms": latency_ms,
            "usage": {
                "total_input_tokens": int(getattr(usage, "total_input_tokens", 0) or 0),
                "total_output_tokens": int(getattr(usage, "total_output_tokens", 0) or 0),
            },
        })
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
