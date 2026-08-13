import json
from pathlib import Path

from data_repository import SQLiteDataRepository
from tools import run_backtesting


def test_reports_missing_competition(tmp_path: Path, monkeypatch, capsys) -> None:
    database = tmp_path / "empty.db"
    output = tmp_path / "results"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_backtesting",
            "--database",
            str(database),
            "--output",
            str(output),
        ],
    )

    assert run_backtesting.main() == 2
    assert "not synchronized" in capsys.readouterr().err
    assert not output.exists()


def test_reports_missing_target_seasons_without_writing_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    database = tmp_path / "partial.db"
    output = tmp_path / "results"
    repository = SQLiteDataRepository(database)
    repository.initialize()
    repository.upsert_many(
        "competition", [{"id": "competition:pl", "code": "PL"}]
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_backtesting",
            "--database",
            str(database),
            "--output",
            str(output),
        ],
    )

    assert run_backtesting.main() == 3
    assert "Missing target seasons" in capsys.readouterr().err
    assert not output.exists()


def test_prints_only_aggregate_execution_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    output = tmp_path / "results"
    repository = SQLiteDataRepository(tmp_path / "database.db")
    repository.initialize()
    repository.upsert_many(
        "competition", [{"id": "competition:pl", "code": "PL"}]
    )
    fake_result = {
        "selection": {"selected_model": "poisson-v0.1.0"},
        "seasons": [
            {
                "season_name": "2024/25",
                "coverage": 0.9,
                "evaluated_matches": 342,
            }
        ],
    }
    monkeypatch.setattr(
        run_backtesting, "run_temporal_backtest", lambda *a, **k: fake_result
    )
    monkeypatch.setattr(
        run_backtesting, "write_aggregate_reports", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_backtesting",
            "--database",
            str(tmp_path / "database.db"),
            "--output",
            str(output),
        ],
    )

    assert run_backtesting.main() == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["selected_model"] == "poisson-v0.1.0"
    assert printed["seasons"][0]["evaluated_matches"] == 342
