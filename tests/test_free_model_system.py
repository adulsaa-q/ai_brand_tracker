from __future__ import annotations

import json

from src.free_models.contractor import ContractorTask, FreeModelContractor
from src.free_models.radar import FreeModelRadar


def test_radar_curates_free_text_models_and_tool_support():
    models = [
        {"id": "poolside/laguna-s-2.1:free", "name": "Laguna", "context_length": 262144,
         "pricing": {"prompt": "0", "completion": "0"}, "supported_parameters": ["tools"]},
        {"id": "acme/audio:free", "context_length": 999999, "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "acme/lyria-audio:free", "context_length": 999999, "pricing": {"prompt": "0", "completion": "0"}},
        {"id": "paid/model", "context_length": 999999, "pricing": {"prompt": "1", "completion": "1"}},
    ]
    result = FreeModelRadar.curate(models)
    assert list(result) == ["poolside/laguna-s-2.1:free"]
    assert result["poolside/laguna-s-2.1:free"]["tools"] is True


def test_radar_first_and_second_run_transition(tmp_path, monkeypatch):
    radar = FreeModelRadar(tmp_path)
    monkeypatch.setattr(radar, "fetch_catalog", lambda: [{"id": "a/model:free", "context_length": 40000,
        "pricing": {"prompt": "0", "completion": "0"}}])
    first = radar.run()
    assert first["status"] == "changed" and first["added"] == ["a/model:free"]
    second = radar.run()
    assert second["status"] == "unchanged" and second["added"] == []
    assert json.loads((tmp_path / "registry.json").read_text())["models"]["a/model:free"]["free"] is True


def test_contractor_envelope_rejects_escape_and_dry_run(tmp_path):
    task = ContractorTask("review code", str(tmp_path), ["src/app.py"], ["python -m pytest -q"])
    result = FreeModelContractor().run(task, "stepfun/step-3.7-flash:free", dry_run=True)
    assert result.status == "DRY_RUN"
    assert "review code" in result.output

    bad = ContractorTask("bad", str(tmp_path), ["../secrets.txt"])
    try:
        bad.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("path escape was accepted")
