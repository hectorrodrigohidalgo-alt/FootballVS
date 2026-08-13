import json
from pathlib import Path
from typing import Any


def _percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_markdown_report(result: dict[str, Any]) -> str:
    """Convierte resultados agregados en un informe legible y versionable."""
    selection = result["selection"]
    lines = [
        "# Resultado del backtesting temporal",
        "",
        f"- Versión: `{result['backtest_version']}`",
        f"- Competición: `{result['competition_id']}`",
        f"- Modelo seleccionado: `{selection['selected_model']}`",
        "- Los resultados no contienen registros individuales de partidos.",
        "",
        "## Resultados por temporada",
        "",
        "| Temporada | Cobertura | Modelo | Log Loss 1X2 | Brier "
        "| Log Loss marcador | Accuracy |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for season in result["seasons"]:
        for label, key in (("Poisson", "poisson"), ("Dixon-Coles", "dixon_coles")):
            metrics = season[key]
            lines.append(
                f"| {season['season_name']} | {_percentage(season['coverage'])} "
                f"| {label} | {metrics['outcome_log_loss']:.6f} "
                f"| {metrics['brier_score']:.6f} "
                f"| {metrics['exact_score_log_loss']:.6f} "
                f"| {_percentage(metrics['outcome_accuracy'])} |"
            )
        lines.extend(
            [
                "",
                f"`rho` {season['season_name']}: {season['rho']['rho']:.2f} "
                f"con {season['rho']['observations']} observaciones anteriores.",
                "",
            ]
        )
    lines.extend(
        [
            "## Decisión",
            "",
            "| Criterio | Cumplido |",
            "| --- | --- |",
        ]
    )
    for criterion, passed in selection["checks"].items():
        lines.append(f"| `{criterion}` | {'Sí' if passed else 'No'} |")
    lines.extend(
        [
            "",
            "Mejora relativa de Dixon-Coles en Log Loss 1X2: "
            f"**{_percentage(selection['relative_outcome_log_loss_improvement'])}**.",
            "",
            "La selección aplica cobertura mínima por temporada, mejora global "
            "mínima del 1%, estabilidad temporal y mejora del marcador exacto.",
            "",
        ]
    )
    elo = result.get("elo")
    if elo:
        selected = elo["selected"]
        selected_parameters = selected["parameters"]
        lines.extend(
            [
                "## Evaluación Elo",
                "",
                f"- Combinaciones evaluadas: **{elo['grid_size']}**.",
                f"- MSE promedio baseline: "
                f"**{elo['baseline']['average_mean_squared_error']:.6f}**.",
                f"- MSE promedio mejor candidato: "
                f"**{elo['best_candidate']['average_mean_squared_error']:.6f}**.",
                f"- Mejora relativa: **{_percentage(elo['relative_improvement'])}**.",
                "- Baseline reemplazado: "
                f"**{'Sí' if elo['baseline_replaced'] else 'No'}**.",
                "- Configuración seleccionada: "
                f"K={selected_parameters['k_factor']:.0f}, "
                f"localía={selected_parameters['home_advantage']:.0f}, "
                f"retención={_percentage(selected_parameters['season_retention'])}, "
                f"ascendidos={selected_parameters['promoted_rating']:.0f}.",
                "",
            ]
        )
    return "\n".join(lines)


def write_aggregate_reports(result: dict[str, Any], output_directory: Path) -> None:
    """Escribe exclusivamente resultados agregados; nunca partidos originales."""
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "backtest-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_directory / "backtest-summary.md").write_text(
        render_markdown_report(result), encoding="utf-8"
    )
