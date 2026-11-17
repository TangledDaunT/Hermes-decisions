"""Unit tests for the Hermes-decisions plugin."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools  # noqa: E402


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch("tools._get_api_key", return_value=""):
        res = json.loads(tools.gemini_decide({"questions": {"q1": {"type": "noul", "instructions": "Test?"}}}))
    assert res["ok"] is False
    assert "GEMINI_API_KEY" in res["error"]


def test_invalid_questions():
    with patch("tools._get_api_key", return_value="fake-key"):
        res = json.loads(tools.gemini_decide({"questions": {}}))
    assert res["ok"] is False


def test_noul_choice_score_and_json_input(tmp_path):
    note_file = tmp_path / "ticket.txt"
    note_file.write_text("Customer asks for immediate refund.", encoding="utf-8")

    mock_result = SimpleNamespace(
        answers={
            "urgent": SimpleNamespace(type="noul", noul=0.94, confidence=0.94),
            "team": SimpleNamespace(
                type="choice",
                choice="billing",
                probabilities={"billing": 0.91, "support": 0.09},
                confidence=0.91,
            ),
            "severity": SimpleNamespace(
                type="score",
                score=4.2,
                probabilities={"1": 0.0, "5": 0.6},
                confidence=0.6,
            ),
        },
        usage=SimpleNamespace(total_input_tokens=120, total_output_tokens=0),
    )

    mock_client = MagicMock()
    mock_client.decisions.create.return_value = mock_result

    with patch("tools._get_api_key", return_value="fake-key"), patch("google.genai.Client", return_value=mock_client):
        raw = tools.gemini_decide({
            "text": "Triage this ticket",
            "json_input": {"tier": "pro", "country": "IN"},
            "files": [str(note_file)],
            "questions": {
                "urgent": {"type": "noul", "instructions": "Is this urgent?"},
                "team": {"type": "choice", "instructions": "Route team", "criteria": {"billing": "Billing", "support": "Support"}},
                "severity": {"type": "score", "instructions": "Score 1-5", "criteria": {"1": "Low", "5": "High"}},
            },
        })

    data = json.loads(raw)
    assert data["ok"] is True
    assert data["usage"]["total_output_tokens"] == 0
    assert data["answers"]["urgent"]["decision"] == "Yes"
    assert data["answers"]["team"]["choice"] == "billing"
    assert data["answers"]["severity"]["score"] == 4.2
