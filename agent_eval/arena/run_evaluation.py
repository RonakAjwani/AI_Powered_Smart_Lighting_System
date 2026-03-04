"""
Full Model Evaluation — Run all scenarios across all models and generate
the comparison table (HTML + Markdown reports).

Usage:
    # Run all models × all scenarios (1 run each)
    python -m arena.run_evaluation

    # Specific models only
    python -m arena.run_evaluation --models llama-3.1-8b,qwen-2.5-32b

    # Pass@k evaluation (3 runs per combo)
    python -m arena.run_evaluation --runs 3

    # Docker mode (live Kafka pipeline)
    python -m arena.run_evaluation --mode docker

    # Quick test with 2 scenarios
    python -m arena.run_evaluation --scenarios S1,S2 --models llama-3.1-8b
"""

# ── Load .env BEFORE any other imports (so API keys are available) ──
from dotenv import load_dotenv
load_dotenv()  # reads .env from cwd or parent directories

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("run-evaluation")

# ── Imports ──
try:
    from arena.scenario_runner import ScenarioRunner, load_all_scenarios
    from arena.metrics_evaluator import MetricsEvaluator
    from arena.model_registry import ModelRegistry, MODEL_REGISTRY
except ImportError:
    from scenario_runner import ScenarioRunner, load_all_scenarios
    from metrics_evaluator import MetricsEvaluator
    from model_registry import ModelRegistry, MODEL_REGISTRY


def run_full_evaluation(
    models: Optional[List[str]] = None,
    scenarios: Optional[List[str]] = None,
    runs_per_combo: int = 1,
    mode: str = "local",
    results_dir: str = None,
    generate_reports: bool = True,
):
    """
    Master evaluation loop:
        for each model:
            for each scenario:
                run k times → collect results

    Then feed all results to MetricsEvaluator → HTML + Markdown reports.
    """
    # ── Resolve models ──
    if models is None:
        models = list(MODEL_REGISTRY.keys())
    
    # ── Resolve scenarios ──
    all_scenarios = load_all_scenarios()
    if scenarios is None:
        scenarios = sorted(all_scenarios.keys())
    else:
        # Validate
        for s in scenarios:
            if s not in all_scenarios:
                logger.warning(f"Scenario '{s}' not found — skipping")
        scenarios = [s for s in scenarios if s in all_scenarios]

    # ── Setup ──
    results_path = Path(results_dir) if results_dir else (
        Path(__file__).parent.parent / "results"
    )
    results_path.mkdir(parents=True, exist_ok=True)

    total_combos = len(models) * len(scenarios) * runs_per_combo
    eval_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           AI CYBER ARENA — FULL MODEL EVALUATION                ║
╠══════════════════════════════════════════════════════════════════╣
║  Eval ID:    {eval_id:<50}║
║  Models:     {len(models):<50}║
║  Scenarios:  {len(scenarios):<50}║
║  Runs/combo: {runs_per_combo:<50}║
║  Total runs: {total_combos:<50}║
║  Mode:       {mode:<50}║
║  Output:     {str(results_path):<50}║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Print model lineup
    print("  Models:")
    for i, m in enumerate(models, 1):
        cfg = MODEL_REGISTRY.get(m)
        name = cfg.display_name if cfg else m
        params = cfg.parameters if cfg else "?"
        print(f"    {i}. {name} ({params})")

    print(f"\n  Scenarios: {', '.join(scenarios)}\n")

    # ── Per-model evaluation ──
    all_run_records = []        # All RunRecord objects across all models
    model_summaries = {}        # model_id → summary stats
    eval_start = time.time()

    for model_idx, model_id in enumerate(models, 1):
        model_cfg = MODEL_REGISTRY.get(model_id)
        model_name = model_cfg.display_name if model_cfg else model_id

        print(f"\n{'━'*70}")
        print(f"  MODEL {model_idx}/{len(models)}: {model_name}")
        print(f"{'━'*70}")

        model_start = time.time()

        # Create a fresh runner for each model
        runner = ScenarioRunner(
            mode=mode,
            results_dir=str(results_path / model_id),
        )

        model_runs = []
        correct = 0
        total = 0

        for scenario_id in scenarios:
            for k in range(1, runs_per_combo + 1):
                total += 1
                progress = f"[{total}/{len(scenarios) * runs_per_combo}]"

                try:
                    run = runner.run_scenario(
                        scenario_id=scenario_id,
                        model_id=model_id,
                        run_index=k,
                    )
                    model_runs.append(run)
                    all_run_records.append(run)

                    if run.correct_detection:
                        correct += 1

                    status = "✓" if run.correct_detection else "✗"
                    print(
                        f"  {progress} {scenario_id}: "
                        f"{status} detected={run.attack_detected} "
                        f"type={run.detected_type} "
                        f"conf={run.confidence:.0f}%"
                    )

                except Exception as e:
                    logger.error(f"  {progress} {scenario_id}: FAILED — {e}")
                    total -= 1  # Don't count failed runs

        model_elapsed = round(time.time() - model_start, 1)
        accuracy = (correct / len(model_runs) * 100) if model_runs else 0

        model_summaries[model_id] = {
            "display_name": model_name,
            "total_runs": len(model_runs),
            "correct_detections": correct,
            "accuracy": round(accuracy, 1),
            "elapsed_sec": model_elapsed,
            "runs": [_run_to_dict(r) for r in model_runs],
        }

        print(f"\n  {model_name}: {correct}/{len(model_runs)} correct "
              f"({accuracy:.1f}%) in {model_elapsed}s")

    # ── Save raw evaluation data ──
    eval_elapsed = round(time.time() - eval_start, 1)
    eval_data = {
        "eval_id": eval_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "models": models,
        "scenarios": scenarios,
        "runs_per_combo": runs_per_combo,
        "total_runs": len(all_run_records),
        "elapsed_sec": eval_elapsed,
        "model_summaries": model_summaries,
    }

    eval_file = results_path / f"{eval_id}.json"
    with open(eval_file, "w") as f:
        json.dump(eval_data, f, indent=2, default=str)

    # ── Generate Reports ──
    if generate_reports:
        print(f"\n{'═'*70}")
        print(f"  GENERATING COMPARISON REPORTS")
        print(f"{'═'*70}")

        try:
            evaluator = MetricsEvaluator()

            # Convert all RunRecords to dicts and load into evaluator
            run_dicts = []
            for run in all_run_records:
                rd = _run_to_dict(run)
                run_dicts.append(rd)

            evaluator.load_runs(run_dicts)

            # Compute all metrics (confusion matrix, rankings, etc.)
            report = evaluator.compute_all()

            # Generate reports
            html_path = results_path / f"{eval_id}_report.html"
            md_path = results_path / f"{eval_id}_report.md"

            evaluator.generate_html_report(report, str(html_path))
            evaluator.generate_markdown_report(report, str(md_path))

            print(f"  ✓ HTML report: {html_path}")
            print(f"  ✓ Markdown report: {md_path}")

            # Print best model
            if report.best_model:
                cfg = MODEL_REGISTRY.get(report.best_model)
                best_name = cfg.display_name if cfg else report.best_model
                print(f"\n  ★ Best Model: {best_name} (F1 = {report.best_f1:.2%})")

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)

    # ── Print Summary Table ──
    _print_comparison_table(model_summaries, models)

    print(f"\n  Total time: {eval_elapsed}s")
    print(f"  Results: {results_path}")
    print(f"  Evaluation: {eval_file}")

    return eval_data


def _run_to_dict(run) -> dict:
    """Convert a RunRecord to a serializable dict."""
    try:
        from dataclasses import asdict
        return asdict(run)
    except Exception:
        return {
            "run_id": run.run_id,
            "scenario_id": run.scenario_id,
            "model_id": run.model_id,
            "attack_detected": run.attack_detected,
            "detected_type": run.detected_type,
            "confidence": run.confidence,
            "correct_detection": run.correct_detection,
            "correct_classification": run.correct_classification,
            "ttp_coverage": run.ttp_coverage,
            "duration_sec": run.duration_sec,
            "status": run.status,
        }


def _print_comparison_table(summaries: dict, models: list):
    """Print a formatted comparison table to console with academic metrics."""
    print(f"\n{'═'*80}")
    print(f"  MODEL COMPARISON TABLE — Performance Metrics for Paper")
    print(f"{'═'*80}")

    # Header
    print(f"\n  {'Model':<25} {'Acc %':>7} {'Prec %':>8} {'Rec %':>7} {'F1 %':>6} {'FPR %':>7} {'Runs':>6}")
    print(f"  {'─'*25} {'─'*7} {'─'*8} {'─'*7} {'─'*6} {'─'*7} {'─'*6}")

    # Compute per-model metrics from runs
    from collections import Counter
    model_metrics = {}
    for model_id in models:
        if model_id not in summaries:
            continue
        s = summaries[model_id]
        runs = s.get("runs", [])
        tp = fp = tn = fn = 0
        for r in runs:
            scenario_id = r.get("scenario_id", "")
            expected = scenario_id != "S1"  # S1 is baseline (no attack)
            detected = r.get("attack_detected", False)
            if expected and detected: tp += 1
            elif expected and not detected: fn += 1
            elif not expected and detected: fp += 1
            else: tn += 1

        total = tp + fp + tn + fn
        acc = (tp + tn) / total * 100 if total else 0
        prec = tp / (tp + fp) * 100 if (tp + fp) else 0
        rec = tp / (tp + fn) * 100 if (tp + fn) else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        fpr = fp / (fp + tn) * 100 if (fp + tn) else 0

        model_metrics[model_id] = {
            "accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "fpr": fpr, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        }

    # Rows sorted by F1
    ranked = sorted(
        [(m, model_metrics.get(m, {}), summaries.get(m, {})) for m in models if m in summaries],
        key=lambda x: x[1].get("f1", 0),
        reverse=True,
    )

    medals = ["🥇", "🥈", "🥉"]

    for i, (model_id, metrics, summary) in enumerate(ranked):
        medal = medals[i] if i < len(medals) else "  "
        print(
            f"  {medal} {summary.get('display_name', model_id):<22} "
            f"{metrics.get('accuracy', 0):>6.1f} "
            f"{metrics.get('precision', 0):>7.1f} "
            f"{metrics.get('recall', 0):>6.1f} "
            f"{metrics.get('f1', 0):>5.1f} "
            f"{metrics.get('fpr', 0):>6.1f} "
            f"{summary.get('total_runs', 0):>5}"
        )

    print(f"  {'─'*72}")

    # Confusion matrix summary
    print(f"\n  Confusion Matrix Summary:")
    print(f"  {'Model':<25} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}")
    print(f"  {'─'*25} {'─'*5} {'─'*5} {'─'*5} {'─'*5}")
    for model_id, metrics, summary in ranked:
        print(
            f"  {summary.get('display_name', model_id):<25} "
            f"{metrics.get('tp', 0):>5} "
            f"{metrics.get('fp', 0):>5} "
            f"{metrics.get('tn', 0):>5} "
            f"{metrics.get('fn', 0):>5}"
        )

    # Best model
    if ranked:
        best_id, best_metrics, best_summary = ranked[0]
        print(f"\n  ★ Best Model: {best_summary.get('display_name', best_id)} "
              f"(F1 = {best_metrics.get('f1', 0):.1f}%, "
              f"Accuracy = {best_metrics.get('accuracy', 0):.1f}%)")


# ═════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Cyber Arena — Full Model Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m arena.run_evaluation                          # All models × all scenarios
  python -m arena.run_evaluation --models llama-3.1-8b    # Single model
  python -m arena.run_evaluation --scenarios S1,S2,M1     # Subset of scenarios
  python -m arena.run_evaluation --runs 3                 # Pass@3 evaluation
  python -m arena.run_evaluation --mode docker            # Docker mode
        """,
    )
    parser.add_argument(
        "--models", default=None,
        help="Comma-separated model IDs (default: all registered models)",
    )
    parser.add_argument(
        "--scenarios", default=None,
        help="Comma-separated scenario IDs (default: all YAML scenarios)",
    )
    parser.add_argument(
        "--runs", type=int, default=1,
        help="Runs per model×scenario combo (default: 1)",
    )
    parser.add_argument(
        "--mode", choices=["local", "docker"], default="local",
        help="Execution mode (default: local)",
    )
    parser.add_argument(
        "--results-dir", default=None,
        help="Output directory for results",
    )
    parser.add_argument(
        "--no-reports", action="store_true",
        help="Skip HTML/Markdown report generation",
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List all available models and exit",
    )
    args = parser.parse_args()

    # List models
    if args.list_models:
        registry = ModelRegistry()
        models = registry.list_models()
        print(f"\n{'ID':<20} {'Name':<25} {'Params':<10} {'Providers'}")
        print("─" * 70)
        for m in models:
            providers = ", ".join(m["available_providers"]) or "(no API key)"
            print(f"{m['model_id']:<20} {m['display_name']:<25} {m['parameters']:<10} {providers}")
        return

    # Parse models
    models = args.models.split(",") if args.models else None

    # Parse scenarios
    scenarios = args.scenarios.split(",") if args.scenarios else None

    # Run evaluation
    run_full_evaluation(
        models=models,
        scenarios=scenarios,
        runs_per_combo=args.runs,
        mode=args.mode,
        results_dir=args.results_dir,
        generate_reports=not args.no_reports,
    )


if __name__ == "__main__":
    main()
