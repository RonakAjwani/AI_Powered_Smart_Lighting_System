"""
Metrics Evaluator — Computes security evaluation metrics from scenario run results.

Metrics computed:
  - Per-scenario: Accuracy, Recall, Precision, FPR, F1-score
  - Per-scenario: Time-to-Detect (TTD), MITRE TTP coverage
  - Per-model: Aggregated scores across all scenarios
  - Cross-model: Comparative rankings and deltas

Usage:
    evaluator = MetricsEvaluator()
    evaluator.load_results("results/")
    report = evaluator.compute_all()
"""

import os
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("metrics-evaluator")


# ═══════════════════════════════════════════════════════════════════════════════
# Metric Data Structures
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConfusionMatrix:
    """Binary confusion matrix for detection evaluation."""
    tp: int = 0     # True Positive: attack present, correctly detected
    fp: int = 0     # False Positive: no attack, incorrectly detected
    tn: int = 0     # True Negative: no attack, correctly not detected
    fn: int = 0     # False Negative: attack present, missed

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.total if self.total > 0 else 0.0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def fpr(self) -> float:
        """False Positive Rate = FP / (FP + TN)."""
        denom = self.fp + self.tn
        return self.fp / denom if denom > 0 else 0.0

    @property
    def fnr(self) -> float:
        """False Negative Rate = FN / (FN + TP)."""
        denom = self.fn + self.tp
        return self.fn / denom if denom > 0 else 0.0


@dataclass
class ScenarioMetrics:
    """Metrics for a single scenario across k runs."""
    scenario_id: str
    scenario_name: str = ""
    num_runs: int = 0
    # Detection metrics
    detection_rate: float = 0.0
    classification_rate: float = 0.0
    avg_confidence: float = 0.0
    # TTP coverage
    avg_ttp_coverage: float = 0.0
    # Time metrics
    avg_duration_sec: float = 0.0
    # Pass@k
    pass_at_k: float = 0.0
    k: int = 0
    # Raw counts
    correct_detections: int = 0
    correct_classifications: int = 0


@dataclass
class ModelMetrics:
    """Aggregated metrics for a single model across all scenarios."""
    model_id: str
    # Confusion matrix (aggregated)
    confusion: ConfusionMatrix = field(default_factory=ConfusionMatrix)
    # Aggregated scores
    overall_accuracy: float = 0.0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1: float = 0.0
    overall_fpr: float = 0.0
    # Classification
    classification_accuracy: float = 0.0
    # TTP
    avg_ttp_coverage: float = 0.0
    # Confidence
    avg_confidence: float = 0.0
    # Time
    avg_ttd_sec: float = 0.0
    # Per-scenario breakdown
    scenario_metrics: Dict[str, ScenarioMetrics] = field(default_factory=dict)
    # Total runs
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0


@dataclass
class EvaluationReport:
    """Complete evaluation report across all models and scenarios."""
    eval_id: str = ""
    timestamp: str = ""
    # Per-model metrics
    model_metrics: Dict[str, ModelMetrics] = field(default_factory=dict)
    # Rankings
    rankings: Dict[str, List[str]] = field(default_factory=dict)
    # Summary
    best_model: str = ""
    best_f1: float = 0.0
    worst_fpr: float = 0.0
    scenarios_evaluated: int = 0
    models_evaluated: int = 0
    total_runs: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Evaluator
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsEvaluator:
    """
    Computes evaluation metrics from scenario run results.

    Supports:
    - Loading results from individual run JSON files
    - Loading from a full evaluation JSON
    - Computing per-model and per-scenario metrics
    - Cross-model comparison and ranking
    """

    def __init__(self):
        self.runs: List[Dict[str, Any]] = []
        self.models: set = set()
        self.scenarios: set = set()

    # ── Data Loading ────────────────────────────────────────────────────────

    def load_results_dir(self, results_dir: str):
        """Load all run result JSON files from a directory."""
        results_path = Path(results_dir)
        if not results_path.exists():
            logger.warning(f"Results directory not found: {results_dir}")
            return

        for json_file in sorted(results_path.glob("*.json")):
            if json_file.stem.startswith("eval_"):
                # Full evaluation file — load all runs from it
                self._load_evaluation_file(json_file)
            elif json_file.stem == "evaluation_summary":
                continue  # Skip summary files
            else:
                self._load_run_file(json_file)

        logger.info(
            f"Loaded {len(self.runs)} runs across "
            f"{len(self.models)} models and {len(self.scenarios)} scenarios"
        )

    def _load_run_file(self, filepath: Path):
        """Load a single run result JSON."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "run_id" in data and "scenario_id" in data:
                self.runs.append(data)
                self.models.add(data.get("model_id", "unknown"))
                self.scenarios.add(data["scenario_id"])
        except Exception as e:
            logger.warning(f"Failed to load {filepath.name}: {e}")

    def _load_evaluation_file(self, filepath: Path):
        """Load runs from a full evaluation JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data.get("results", {})
            for model_id, model_results in results.items():
                for scenario_id, pak_data in model_results.items():
                    for run_data in pak_data.get("runs", []):
                        self.runs.append(run_data)
                        self.models.add(model_id)
                        self.scenarios.add(scenario_id)
        except Exception as e:
            logger.warning(f"Failed to load evaluation file {filepath.name}: {e}")

    def load_runs(self, runs: List[Dict[str, Any]]):
        """Load runs from a list of dicts (in-memory)."""
        for run in runs:
            self.runs.append(run)
            self.models.add(run.get("model_id", "unknown"))
            self.scenarios.add(run.get("scenario_id", "unknown"))

    # ── Metric Computation ──────────────────────────────────────────────────

    def compute_all(self) -> EvaluationReport:
        """Compute all metrics and return a complete evaluation report."""
        report = EvaluationReport(
            eval_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            scenarios_evaluated=len(self.scenarios),
            models_evaluated=len(self.models),
            total_runs=len(self.runs),
        )

        # Compute per-model metrics
        for model_id in sorted(self.models):
            model_runs = [r for r in self.runs if r.get("model_id") == model_id]
            mm = self._compute_model_metrics(model_id, model_runs)
            report.model_metrics[model_id] = mm

        # Compute rankings
        report.rankings = self._compute_rankings(report.model_metrics)

        # Summary
        if report.model_metrics:
            best = max(report.model_metrics.values(), key=lambda m: m.overall_f1)
            report.best_model = best.model_id
            report.best_f1 = best.overall_f1
            worst_fpr = max(report.model_metrics.values(), key=lambda m: m.overall_fpr)
            report.worst_fpr = worst_fpr.overall_fpr

        return report

    def _compute_model_metrics(
        self, model_id: str, runs: List[Dict[str, Any]]
    ) -> ModelMetrics:
        """Compute metrics for a single model."""
        mm = ModelMetrics(model_id=model_id)
        mm.total_runs = len(runs)
        mm.completed_runs = sum(1 for r in runs if r.get("status") == "completed")
        mm.failed_runs = sum(1 for r in runs if r.get("status") == "failed")

        completed_runs = [r for r in runs if r.get("status") == "completed"]
        if not completed_runs:
            return mm

        # Build confusion matrix from all runs
        for run in completed_runs:
            gt = run.get("ground_truth", {})
            gt_type = gt.get("attack_type", "none")
            has_attack = gt_type != "none"
            detected = run.get("attack_detected", False)

            if has_attack and detected:
                mm.confusion.tp += 1
            elif has_attack and not detected:
                mm.confusion.fn += 1
            elif not has_attack and detected:
                mm.confusion.fp += 1
            else:
                mm.confusion.tn += 1

        # Compute aggregated scores from confusion matrix
        mm.overall_accuracy = mm.confusion.accuracy
        mm.overall_precision = mm.confusion.precision
        mm.overall_recall = mm.confusion.recall
        mm.overall_f1 = mm.confusion.f1
        mm.overall_fpr = mm.confusion.fpr

        # Classification accuracy (among correct detections)
        correct_classifications = sum(
            1 for r in completed_runs if r.get("correct_classification", False)
        )
        mm.classification_accuracy = correct_classifications / len(completed_runs)

        # TTP coverage
        ttp_coverages = [r.get("ttp_coverage", 0.0) for r in completed_runs]
        mm.avg_ttp_coverage = sum(ttp_coverages) / len(ttp_coverages)

        # Confidence
        confidences = [r.get("confidence", 0.0) for r in completed_runs]
        mm.avg_confidence = sum(confidences) / len(confidences)

        # Time-to-detect
        durations = [r.get("duration_sec", 0.0) for r in completed_runs if r.get("duration_sec", 0) > 0]
        mm.avg_ttd_sec = sum(durations) / len(durations) if durations else 0.0

        # Per-scenario breakdown
        for scenario_id in sorted(self.scenarios):
            scenario_runs = [r for r in completed_runs if r.get("scenario_id") == scenario_id]
            if scenario_runs:
                sm = self._compute_scenario_metrics(scenario_id, scenario_runs)
                mm.scenario_metrics[scenario_id] = sm

        return mm

    def _compute_scenario_metrics(
        self, scenario_id: str, runs: List[Dict[str, Any]]
    ) -> ScenarioMetrics:
        """Compute metrics for a single scenario's runs."""
        sm = ScenarioMetrics(
            scenario_id=scenario_id,
            num_runs=len(runs),
            k=len(runs),
        )

        correct_det = sum(1 for r in runs if r.get("correct_detection", False))
        correct_cls = sum(1 for r in runs if r.get("correct_classification", False))

        sm.correct_detections = correct_det
        sm.correct_classifications = correct_cls
        sm.detection_rate = correct_det / len(runs) if runs else 0.0
        sm.classification_rate = correct_cls / len(runs) if runs else 0.0
        sm.pass_at_k = sm.detection_rate

        confidences = [r.get("confidence", 0.0) for r in runs]
        sm.avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        ttp_covs = [r.get("ttp_coverage", 0.0) for r in runs]
        sm.avg_ttp_coverage = sum(ttp_covs) / len(ttp_covs) if ttp_covs else 0.0

        durations = [r.get("duration_sec", 0.0) for r in runs if r.get("duration_sec", 0) > 0]
        sm.avg_duration_sec = sum(durations) / len(durations) if durations else 0.0

        return sm

    def _compute_rankings(
        self, model_metrics: Dict[str, ModelMetrics]
    ) -> Dict[str, List[str]]:
        """Rank models across multiple metrics."""
        if not model_metrics:
            return {}

        models = list(model_metrics.values())
        return {
            "by_f1": [m.model_id for m in sorted(models, key=lambda x: x.overall_f1, reverse=True)],
            "by_accuracy": [m.model_id for m in sorted(models, key=lambda x: x.overall_accuracy, reverse=True)],
            "by_recall": [m.model_id for m in sorted(models, key=lambda x: x.overall_recall, reverse=True)],
            "by_precision": [m.model_id for m in sorted(models, key=lambda x: x.overall_precision, reverse=True)],
            "by_fpr": [m.model_id for m in sorted(models, key=lambda x: x.overall_fpr)],   # Lower is better
            "by_ttp_coverage": [m.model_id for m in sorted(models, key=lambda x: x.avg_ttp_coverage, reverse=True)],
            "by_speed": [m.model_id for m in sorted(models, key=lambda x: x.avg_ttd_sec)],  # Lower is better
        }

    # ── Report Generation ───────────────────────────────────────────────────

    def generate_markdown_report(self, report: EvaluationReport, output_path: str = None) -> str:
        """Generate a Markdown evaluation report."""
        lines = []
        lines.append("# AI Cyber Arena — Evaluation Report\n")
        lines.append(f"**Generated:** {report.timestamp}")
        lines.append(f"**Models:** {report.models_evaluated} | "
                      f"**Scenarios:** {report.scenarios_evaluated} | "
                      f"**Total Runs:** {report.total_runs}\n")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Best Model (F1) | **{report.best_model}** ({report.best_f1:.2%}) |")
        lines.append(f"| Worst FPR | {report.worst_fpr:.2%} |")
        lines.append(f"| Models Evaluated | {report.models_evaluated} |")
        lines.append(f"| Scenarios | {report.scenarios_evaluated} |")
        lines.append(f"| Total Runs | {report.total_runs} |")
        lines.append("")

        # Model Comparison Table
        lines.append("## Model Comparison\n")
        lines.append("| Model | Accuracy | Precision | Recall | F1 | FPR | TTP Cov. | Avg Conf. | TTD (s) |")
        lines.append("|-------|----------|-----------|--------|-----|-----|----------|-----------|---------|")

        for model_id in sorted(report.model_metrics.keys()):
            mm = report.model_metrics[model_id]
            lines.append(
                f"| {model_id} | {mm.overall_accuracy:.2%} | "
                f"{mm.overall_precision:.2%} | {mm.overall_recall:.2%} | "
                f"**{mm.overall_f1:.2%}** | {mm.overall_fpr:.2%} | "
                f"{mm.avg_ttp_coverage:.2%} | {mm.avg_confidence:.1f}% | "
                f"{mm.avg_ttd_sec:.1f} |"
            )
        lines.append("")

        # Rankings
        if report.rankings:
            lines.append("## Rankings\n")
            for metric, ranked in report.rankings.items():
                medal = ["🥇", "🥈", "🥉"]
                ranked_str = " > ".join(
                    f"{medal[i] if i < 3 else ''} {m}" for i, m in enumerate(ranked)
                )
                lines.append(f"- **{metric.replace('by_', '').replace('_', ' ').title()}**: {ranked_str}")
            lines.append("")

        # Per-Model Scenario Breakdown
        for model_id, mm in sorted(report.model_metrics.items()):
            lines.append(f"## {model_id}\n")
            lines.append(f"**Confusion Matrix:** TP={mm.confusion.tp} FP={mm.confusion.fp} "
                          f"TN={mm.confusion.tn} FN={mm.confusion.fn}")
            lines.append("")

            if mm.scenario_metrics:
                lines.append("| Scenario | Detection | Classification | Confidence | TTP Cov. | Pass@k |")
                lines.append("|----------|-----------|----------------|------------|----------|--------|")
                for sid, sm in sorted(mm.scenario_metrics.items()):
                    lines.append(
                        f"| {sid} | {sm.detection_rate:.0%} | "
                        f"{sm.classification_rate:.0%} | "
                        f"{sm.avg_confidence:.1f}% | "
                        f"{sm.avg_ttp_coverage:.0%} | "
                        f"{sm.pass_at_k:.0%} ({sm.correct_detections}/{sm.num_runs}) |"
                    )
                lines.append("")

        md_content = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"Markdown report saved: {output_path}")

        return md_content

    def generate_html_report(self, report: EvaluationReport, output_path: str = None) -> str:
        """Generate a professional HTML evaluation report with Chart.js charts and graphs."""
        mm_list = sorted(report.model_metrics.values(), key=lambda x: x.overall_f1, reverse=True)

        # Find best values for highlighting
        best_f1 = max((m.overall_f1 for m in mm_list), default=0)
        best_recall = max((m.overall_recall for m in mm_list), default=0)
        best_precision = max((m.overall_precision for m in mm_list), default=0)
        lowest_fpr = min((m.overall_fpr for m in mm_list), default=1)

        # Build scenario heatmap data
        all_scenario_ids = sorted(self.scenarios)

        # ── Color palette for charts ──
        chart_colors = [
            "rgba(9, 132, 227, 0.85)",    # Blue
            "rgba(0, 184, 148, 0.85)",     # Green
            "rgba(108, 92, 231, 0.85)",    # Purple
            "rgba(253, 203, 110, 0.85)",   # Yellow
            "rgba(225, 112, 85, 0.85)",    # Coral
            "rgba(116, 185, 255, 0.85)",   # Light Blue
            "rgba(85, 239, 196, 0.85)",    # Mint
            "rgba(162, 155, 254, 0.85)",   # Lavender
        ]
        chart_borders = [c.replace("0.85", "1") for c in chart_colors]
        chart_bg_light = [c.replace("0.85", "0.15") for c in chart_colors]

        # ── Prepare chart data as JSON-safe structures ──
        model_labels = [mm.model_id for mm in mm_list]
        accuracy_data = [round(mm.overall_accuracy * 100, 1) for mm in mm_list]
        precision_data = [round(mm.overall_precision * 100, 1) for mm in mm_list]
        recall_data = [round(mm.overall_recall * 100, 1) for mm in mm_list]
        f1_data = [round(mm.overall_f1 * 100, 1) for mm in mm_list]
        fpr_data = [round(mm.overall_fpr * 100, 1) for mm in mm_list]
        ttp_data = [round(mm.avg_ttp_coverage * 100, 1) for mm in mm_list]
        confidence_data = [round(mm.avg_confidence, 1) for mm in mm_list]
        tp_data = [mm.confusion.tp for mm in mm_list]
        fp_data = [mm.confusion.fp for mm in mm_list]
        tn_data = [mm.confusion.tn for mm in mm_list]
        fn_data = [mm.confusion.fn for mm in mm_list]

        # Per-scenario confidence data (more informative than binary detection)
        scenario_confidence_data = {}
        for mm in mm_list:
            model_scenario_conf = []
            for sid in all_scenario_ids:
                sm = mm.scenario_metrics.get(sid)
                model_scenario_conf.append(round(sm.avg_confidence, 1) if sm else 0)
            scenario_confidence_data[mm.model_id] = model_scenario_conf

        # ── Build executive summary ──
        best_model_name = mm_list[0].model_id if mm_list else "N/A"
        worst_model_name = mm_list[-1].model_id if mm_list else "N/A"
        avg_f1 = sum(f1_data) / len(f1_data) if f1_data else 0
        perfect_models = sum(1 for f in f1_data if f >= 95)

        # Import json for chart data serialization
        import json as _json

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cyber Arena — Evaluation Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            line-height: 1.7;
            font-size: 14px;
        }}

        /* ── Header ── */
        .header {{
            background: linear-gradient(135deg, #0c1445 0%, #1a1a6e 40%, #0984e3 100%);
            color: white;
            padding: 48px 40px 40px;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }}
        .header .subtitle {{
            opacity: 0.7;
            font-size: 13px;
            font-weight: 400;
            letter-spacing: 0.3px;
        }}
        .header .report-meta {{
            display: flex;
            gap: 24px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .header .meta-chip {{
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
            backdrop-filter: blur(10px);
        }}
        .header .meta-chip strong {{ font-weight: 700; color: #74b9ff; }}

        /* ── Navigation ── */
        .nav-bar {{
            background: white;
            border-bottom: 1px solid #e1e4e8;
            padding: 0 40px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .nav-bar ul {{
            list-style: none;
            display: flex;
            gap: 0;
            max-width: 1280px;
            margin: 0 auto;
            overflow-x: auto;
        }}
        .nav-bar li a {{
            display: block;
            padding: 14px 18px;
            color: #636e72;
            text-decoration: none;
            font-size: 12.5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid transparent;
            white-space: nowrap;
            transition: all 0.2s ease;
        }}
        .nav-bar li a:hover {{
            color: #0984e3;
            border-bottom-color: #0984e3;
            background: #f8f9ff;
        }}

        /* ── Container ── */
        .container {{ max-width: 1280px; margin: 0 auto; padding: 32px 24px; }}

        /* ── Summary Cards ── */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .summary-card {{
            background: white;
            border-radius: 14px;
            padding: 24px 20px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03);
            border-left: 4px solid #0984e3;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .summary-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
        .summary-card.best {{ border-left-color: #00b894; }}
        .summary-card.warn {{ border-left-color: #e17055; }}
        .summary-card .value {{ font-size: 30px; font-weight: 800; color: #0984e3; letter-spacing: -1px; }}
        .summary-card.best .value {{ color: #00b894; }}
        .summary-card.warn .value {{ color: #e17055; }}
        .summary-card .label {{
            font-size: 11px;
            color: #636e72;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* ── Executive Summary ── */
        .executive-summary {{
            background: linear-gradient(135deg, #f8f9ff, #eef1ff);
            border: 1px solid #d5deff;
            border-radius: 14px;
            padding: 28px 32px;
            margin-bottom: 32px;
            font-size: 14.5px;
            line-height: 1.8;
            color: #2d3436;
        }}
        .executive-summary h2 {{ font-size: 17px; color: #0c1445; margin-bottom: 12px; font-weight: 700; }}
        .executive-summary strong {{ color: #0984e3; }}

        /* ── Sections ── */
        .section {{
            background: white;
            border-radius: 14px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03);
        }}
        .section h2 {{
            font-size: 17px;
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f2f5;
            font-weight: 700;
        }}

        /* ── Charts ── */
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }}
        .chart-card {{
            background: white;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03);
        }}
        .chart-card h3 {{
            font-size: 14px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 4px;
            letter-spacing: 0.2px;
        }}
        .chart-card h3 .fig-num {{
            color: #636e72;
            font-weight: 600;
            font-size: 12px;
        }}
        .chart-card .chart-subtitle {{
            font-size: 12px;
            color: #636e72;
            margin-bottom: 16px;
            font-weight: 400;
            font-style: italic;
        }}
        .chart-container {{
            position: relative;
            width: 100%;
        }}
        .chart-container canvas {{ max-height: 380px; }}
        .chart-card.full-width {{ grid-column: 1 / -1; }}

        /* ── Tables ── */
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{
            background: #f8f9fa;
            padding: 12px 14px;
            text-align: left;
            font-weight: 700;
            color: #636e72;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            border-bottom: 2px solid #e1e4e8;
        }}
        td {{ padding: 11px 14px; border-bottom: 1px solid #f0f2f5; }}
        tr:hover {{ background: #f8f9ff; }}
        .highlight {{ background: #e8f8f5 !important; }}
        .best-badge {{ background: linear-gradient(135deg, #00b894, #55efc4); color: white; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}

        /* ── Metric bars ── */
        .metric-bar {{ height: 5px; background: #ecf0f1; border-radius: 3px; overflow: hidden; margin-top: 6px; }}
        .metric-bar .fill {{ height: 100%; border-radius: 3px; }}
        .fill-green {{ background: linear-gradient(90deg, #00b894, #55efc4); }}
        .fill-blue {{ background: linear-gradient(90deg, #0984e3, #74b9ff); }}
        .fill-orange {{ background: linear-gradient(90deg, #fdcb6e, #ffeaa7); }}
        .fill-red {{ background: linear-gradient(90deg, #d63031, #ff7675); }}

        /* ── Heatmap (confidence-based) ── */
        .heatmap {{ overflow-x: auto; }}
        .heatmap td {{ text-align: center; font-weight: 700; min-width: 56px; font-size: 11.5px; padding: 8px 5px; }}
        .heat-high {{ background: #00b894; color: white; }}
        .heat-good {{ background: #55efc4; color: #1a1a2e; }}
        .heat-mid {{ background: #ffeaa7; color: #1a1a2e; }}
        .heat-low {{ background: #fab1a0; color: #1a1a2e; }}
        .heat-fail {{ background: #d63031; color: white; }}

        /* ── Confusion Matrix ── */
        .confusion-grid {{ display: inline-grid; grid-template-columns: auto auto auto; gap: 3px; font-size: 13px; border-radius: 8px; overflow: hidden; }}
        .confusion-grid .cell {{ padding: 10px 18px; text-align: center; font-weight: 700; }}
        .confusion-grid .tp {{ background: #e8f8f5; color: #00b894; }}
        .confusion-grid .fp {{ background: #fff3e0; color: #e17055; }}
        .confusion-grid .fn {{ background: #fce4ec; color: #d63031; }}
        .confusion-grid .tn {{ background: #ecf0f1; color: #636e72; }}
        .confusion-grid .label-cell {{ background: #f8f9fa; font-weight: 500; font-size: 11px; color: #636e72; }}

        /* ── Footer ── */
        .footer {{
            text-align: center;
            padding: 32px;
            color: #b2bec3;
            font-size: 12px;
            border-top: 1px solid #e1e4e8;
            margin-top: 16px;
        }}
        .footer strong {{ color: #636e72; }}

        /* ── Print styles ── */
        @media print {{
            .nav-bar {{ display: none; }}
            .header {{ padding: 24px; }}
            .chart-grid {{ break-inside: avoid; }}
            .section {{ break-inside: avoid; box-shadow: none; border: 1px solid #e1e4e8; }}
            body {{ background: white; }}
        }}
        @media (max-width: 768px) {{
            .chart-grid {{ grid-template-columns: 1fr; }}
            .header .report-meta {{ flex-direction: column; gap: 8px; }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>🛡️ AI Cyber Arena — Evaluation Report</h1>
        <div class="subtitle">Comprehensive Model Performance Analysis</div>
        <div class="report-meta">
            <div class="meta-chip">📅 <strong>{report.timestamp[:10] if report.timestamp else 'N/A'}</strong></div>
            <div class="meta-chip">🤖 <strong>{report.models_evaluated}</strong> Models</div>
            <div class="meta-chip">🎯 <strong>{report.scenarios_evaluated}</strong> Scenarios</div>
            <div class="meta-chip">🔄 <strong>{report.total_runs}</strong> Total Runs</div>
            <div class="meta-chip">🏆 Best: <strong>{report.best_model}</strong> (F1 {report.best_f1:.1%})</div>
        </div>
    </div>

    <!-- Navigation -->
    <div class="nav-bar">
        <ul>
            <li><a href="#summary">Summary</a></li>
            <li><a href="#charts">Charts</a></li>
            <li><a href="#comparison">Comparison</a></li>
            <li><a href="#heatmap">Heatmap</a></li>
            <li><a href="#models">Model Details</a></li>
        </ul>
    </div>

    <div class="container">
"""

        # ── Summary Cards ──
        html += '        <div id="summary"></div>\n'
        html += '        <div class="summary-grid">\n'
        html += f'            <div class="summary-card best"><div class="value">{report.best_model or "–"}</div><div class="label">Best Model (F1)</div></div>\n'
        html += f'            <div class="summary-card best"><div class="value">{report.best_f1:.1%}</div><div class="label">Best F1 Score</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.models_evaluated}</div><div class="label">Models Evaluated</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.scenarios_evaluated}</div><div class="label">Scenarios</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.total_runs}</div><div class="label">Total Runs</div></div>\n'
        fpr_class = "warn" if report.worst_fpr > 0.1 else ""
        html += f'            <div class="summary-card {fpr_class}"><div class="value">{report.worst_fpr:.1%}</div><div class="label">Worst FPR</div></div>\n'
        html += '        </div>\n'

        # ── Executive Summary ──
        html += f"""
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>
                This evaluation benchmarked <strong>{report.models_evaluated} AI models</strong> across
                <strong>{report.scenarios_evaluated} cybersecurity scenarios</strong> ({report.total_runs} total runs),
                covering DDoS attacks (S-series), malware threats (M-series), and complex/coordinated attacks (C-series).
            </p>
            <p>
                <strong>{best_model_name}</strong> achieved the highest F1 score of <strong>{report.best_f1:.1%}</strong>,
                while the average F1 across all models was <strong>{avg_f1:.1f}%</strong>.
                {"<strong>" + str(perfect_models) + " model(s)</strong> achieved near-perfect F1 scores (≥95%)." if perfect_models > 0 else ""}
                The lowest-performing model was <strong>{worst_model_name}</strong> with an F1 of <strong>{f1_data[-1] if f1_data else 0:.1f}%</strong>.
            </p>
        </div>
"""

        # ══════════════════════════════════════════════════════════════
        #  CHARTS SECTION
        # ══════════════════════════════════════════════════════════════
        html += '        <div id="charts"></div>\n'
        html += '        <div class="chart-grid">\n'

        # ── Chart 1: Radar — Multi-metric Model Comparison ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 1.</span> Model Performance Radar</h3>
                <p class="chart-subtitle">Multi-dimensional comparison of Accuracy, Precision, Recall, F1, TTP Coverage and Confidence across all evaluated models</p>
                <div class="chart-container"><canvas id="radarChart"></canvas></div>
            </div>
"""

        # ── Chart 2: Grouped Bar — Core Metrics Comparison ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 2.</span> Core Metrics Comparison</h3>
                <p class="chart-subtitle">Accuracy, Precision, Recall and F1 Score for each model (higher is better)</p>
                <div class="chart-container"><canvas id="metricsBarChart"></canvas></div>
            </div>
"""

        # ── Chart 3: Stacked Bar — Confusion Matrix Breakdown ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 3.</span> Confusion Matrix Breakdown</h3>
                <p class="chart-subtitle">Distribution of True Positives, True Negatives, False Positives, and False Negatives per model</p>
                <div class="chart-container"><canvas id="confusionBarChart"></canvas></div>
            </div>
"""

        # ── Chart 4: Horizontal Bar — Average Confidence ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 4.</span> Average Confidence Score</h3>
                <p class="chart-subtitle">Mean prediction confidence level across all scenarios for each model</p>
                <div class="chart-container"><canvas id="confidenceChart"></canvas></div>
            </div>
"""

        # ── Chart 5: Scenario Confidence (full width) ──
        html += """
            <div class="chart-card full-width">
                <h3><span class="fig-num">Figure 5.</span> Per-Scenario Confidence Scores</h3>
                <p class="chart-subtitle">Confidence score (%) for each model across all 16 attack scenarios — higher values indicate stronger detection certainty</p>
                <div class="chart-container"><canvas id="scenarioChart"></canvas></div>
            </div>
"""

        # ── Chart 6: Doughnut — F1 Score Distribution ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 6.</span> F1 Score Distribution</h3>
                <p class="chart-subtitle">Proportional F1 score comparison across all evaluated models</p>
                <div class="chart-container"><canvas id="f1DoughnutChart"></canvas></div>
            </div>
"""

        # ── Chart 7: FPR Bar ──
        html += """
            <div class="chart-card">
                <h3><span class="fig-num">Figure 7.</span> False Positive Rate Comparison</h3>
                <p class="chart-subtitle">False positive rate per model — lower values indicate fewer false alarms</p>
                <div class="chart-container"><canvas id="fprChart"></canvas></div>
            </div>
"""

        html += '        </div><!-- /chart-grid -->\n'

        # ══════════════════════════════════════════════════════════════
        #  MODEL COMPARISON TABLE
        # ══════════════════════════════════════════════════════════════
        html += '        <div id="comparison"></div>\n'
        html += '        <div class="section">\n'
        html += '            <h2>Table 1: Model Performance Comparison</h2>\n'
        html += '            <table>\n'
        html += '                <tr><th>Rank</th><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>FPR</th><th>TTP Cov.</th><th>Avg Conf.</th><th>TTD</th></tr>\n'

        medals = ["🥇", "🥈", "🥉"]
        for rank, mm in enumerate(mm_list, 1):
            is_best = (rank == 1) and len(mm_list) > 1
            row_class = ' class="highlight"' if is_best else ""
            badge = ' <span class="best-badge">BEST</span>' if is_best else ""
            medal = medals[rank - 1] if rank <= 3 else f"#{rank}"

            html += f'                <tr{row_class}>\n'
            html += f'                    <td>{medal}</td>\n'
            html += f'                    <td><strong>{mm.model_id}</strong>{badge}</td>\n'
            html += f'                    <td>{mm.overall_accuracy:.1%}<div class="metric-bar"><div class="fill fill-blue" style="width:{mm.overall_accuracy*100:.0f}%"></div></div></td>\n'
            html += f'                    <td>{mm.overall_precision:.1%}</td>\n'
            html += f'                    <td>{mm.overall_recall:.1%}</td>\n'

            f1_color = "fill-green" if mm.overall_f1 >= 0.8 else ("fill-orange" if mm.overall_f1 >= 0.5 else "fill-red")
            html += f'                    <td><strong>{mm.overall_f1:.1%}</strong><div class="metric-bar"><div class="fill {f1_color}" style="width:{mm.overall_f1*100:.0f}%"></div></div></td>\n'

            fpr_color = "fill-green" if mm.overall_fpr <= 0.05 else ("fill-orange" if mm.overall_fpr <= 0.15 else "fill-red")
            html += f'                    <td>{mm.overall_fpr:.1%}<div class="metric-bar"><div class="fill {fpr_color}" style="width:{mm.overall_fpr*100:.0f}%"></div></div></td>\n'
            html += f'                    <td>{mm.avg_ttp_coverage:.0%}</td>\n'
            html += f'                    <td>{mm.avg_confidence:.1f}%</td>\n'
            html += f'                    <td>{mm.avg_ttd_sec:.1f}s</td>\n'
            html += '                </tr>\n'

        html += '            </table>\n'
        html += '        </div>\n'

        # ══════════════════════════════════════════════════════════════
        #  CONFIDENCE HEATMAP (replaces binary detection heatmap)
        # ══════════════════════════════════════════════════════════════
        html += '        <div id="heatmap"></div>\n'
        if all_scenario_ids and mm_list:
            html += '        <div class="section">\n'
            html += '            <h2>Table 2: Per-Scenario Confidence Heatmap</h2>\n'
            html += '            <p style="font-size:12.5px;color:#636e72;margin-bottom:16px;font-style:italic;">Confidence score (%) for each model–scenario combination. Higher scores (green) indicate stronger detection certainty; lower scores (red) indicate weaker or missed detections.</p>\n'
            html += '            <div class="heatmap"><table>\n'
            html += f'                <tr><th>Model</th>'
            for sid in all_scenario_ids:
                html += f'<th>{sid}</th>'
            html += '<th>Avg</th></tr>\n'

            for mm in mm_list:
                html += f'                <tr><td><strong>{mm.model_id}</strong></td>'
                conf_values = []
                for sid in all_scenario_ids:
                    sm = mm.scenario_metrics.get(sid)
                    if sm:
                        conf = sm.avg_confidence
                        conf_values.append(conf)
                        # Confidence-based heat coloring (continuous scale)
                        heat = "heat-high" if conf >= 80 else ("heat-good" if conf >= 60 else ("heat-mid" if conf >= 40 else ("heat-low" if conf >= 20 else "heat-fail")))
                        html += f'<td class="{heat}">{conf:.0f}%</td>'
                    else:
                        html += '<td>—</td>'
                avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0
                avg_heat = "heat-high" if avg_conf >= 80 else ("heat-good" if avg_conf >= 60 else ("heat-mid" if avg_conf >= 40 else ("heat-low" if avg_conf >= 20 else "heat-fail")))
                html += f'<td class="{avg_heat}" style="border-left:2px solid #636e72"><strong>{avg_conf:.0f}%</strong></td>'
                html += '</tr>\n'

            html += '            </table></div>\n'
            html += '        </div>\n'

        # ══════════════════════════════════════════════════════════════
        #  PER-MODEL DETAIL CARDS
        # ══════════════════════════════════════════════════════════════
        html += '        <div id="models"></div>\n'
        for idx, mm in enumerate(mm_list):
            medal_str = medals[idx] + " " if idx < 3 else ""
            html += f'        <div class="section">\n'
            html += f'            <h2>{medal_str}{mm.model_id} — Detailed Results</h2>\n'

            # Key metrics inline
            html += f'            <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:16px;">\n'
            html += f'                <div><strong style="color:#0984e3">Accuracy:</strong> {mm.overall_accuracy:.1%}</div>\n'
            html += f'                <div><strong style="color:#6c5ce7">Precision:</strong> {mm.overall_precision:.1%}</div>\n'
            html += f'                <div><strong style="color:#00b894">Recall:</strong> {mm.overall_recall:.1%}</div>\n'
            html += f'                <div><strong style="color:#e17055">F1:</strong> {mm.overall_f1:.1%}</div>\n'
            html += f'                <div><strong style="color:#636e72">FPR:</strong> {mm.overall_fpr:.1%}</div>\n'
            html += f'            </div>\n'

            # Confusion matrix
            html += '            <div class="confusion-grid">\n'
            html += '                <div class="label-cell"></div><div class="label-cell">Predicted +</div><div class="label-cell">Predicted −</div>\n'
            html += f'                <div class="label-cell">Actual +</div><div class="cell tp">TP: {mm.confusion.tp}</div><div class="cell fn">FN: {mm.confusion.fn}</div>\n'
            html += f'                <div class="label-cell">Actual −</div><div class="cell fp">FP: {mm.confusion.fp}</div><div class="cell tn">TN: {mm.confusion.tn}</div>\n'
            html += '            </div>\n'

            # Scenario table
            if mm.scenario_metrics:
                html += '            <table style="margin-top:20px">\n'
                html += '                <tr><th>Scenario</th><th>Detection</th><th>Classification</th><th>Confidence</th><th>TTP Coverage</th><th>Pass@k</th></tr>\n'
                for sid, sm in sorted(mm.scenario_metrics.items()):
                    det_icon = "✅" if sm.detection_rate >= 1.0 else ("⚠️" if sm.detection_rate > 0 else "❌")
                    html += f'                <tr><td>{det_icon} {sid}</td><td>{sm.detection_rate:.0%}</td><td>{sm.classification_rate:.0%}</td><td>{sm.avg_confidence:.1f}%</td><td>{sm.avg_ttp_coverage:.0%}</td><td>{sm.pass_at_k:.0%} ({sm.correct_detections}/{sm.num_runs})</td></tr>\n'
                html += '            </table>\n'

            html += '        </div>\n'

        # ══════════════════════════════════════════════════════════════
        #  FOOTER
        # ══════════════════════════════════════════════════════════════
        html += f"""
        <div class="footer">
            <strong>AI Cyber Arena — Evaluation Framework v1.0</strong><br>
            NIST SP 800-61r3 compliant · MITRE ATT&CK for ICS aligned<br>
            Report generated: {report.timestamp}
        </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!--  Chart.js Scripts                                         -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <script>
        const modelLabels = {_json.dumps(model_labels)};
        const chartColors = {_json.dumps(chart_colors)};
        const chartBorders = {_json.dumps(chart_borders)};
        const chartBgLight = {_json.dumps(chart_bg_light)};

        // Shared defaults
        Chart.defaults.font.family = "'Inter', 'Segoe UI', system-ui, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#636e72';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
        Chart.defaults.plugins.legend.labels.padding = 16;

        // ── 1. Radar Chart ──
        new Chart(document.getElementById('radarChart'), {{
            type: 'radar',
            data: {{
                labels: ['Accuracy (%)', 'Precision (%)', 'Recall (%)', 'F1 Score (%)', 'TTP Coverage (%)', 'Avg Confidence (%)'],
                datasets: modelLabels.map((label, i) => ({{
                    label: label,
                    data: [
                        {_json.dumps(accuracy_data)}[i],
                        {_json.dumps(precision_data)}[i],
                        {_json.dumps(recall_data)}[i],
                        {_json.dumps(f1_data)}[i],
                        {_json.dumps(ttp_data)}[i],
                        {_json.dumps(confidence_data)}[i]
                    ],
                    borderColor: chartBorders[i],
                    backgroundColor: chartBgLight[i],
                    borderWidth: 2.5,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: chartBorders[i],
                }}))
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{ stepSize: 20, font: {{ size: 10 }}, backdropColor: 'transparent' }},
                        grid: {{ color: 'rgba(0,0,0,0.08)' }},
                        angleLines: {{ color: 'rgba(0,0,0,0.06)' }},
                        pointLabels: {{ font: {{ size: 11.5, weight: '600' }}, color: '#2d3436' }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 20 }} }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + ctx.parsed.r + '%' }} }}
                }}
        }});

        // ── 2. Core Metrics Bar Chart ──
        new Chart(document.getElementById('metricsBarChart'), {{
            type: 'bar',
            data: {{
                labels: modelLabels,
                datasets: [
                    {{ label: 'Accuracy', data: {_json.dumps(accuracy_data)}, backgroundColor: 'rgba(9, 132, 227, 0.75)', borderColor: 'rgba(9, 132, 227, 1)', borderWidth: 1, borderRadius: 4 }},
                    {{ label: 'Precision', data: {_json.dumps(precision_data)}, backgroundColor: 'rgba(108, 92, 231, 0.75)', borderColor: 'rgba(108, 92, 231, 1)', borderWidth: 1, borderRadius: 4 }},
                    {{ label: 'Recall', data: {_json.dumps(recall_data)}, backgroundColor: 'rgba(0, 184, 148, 0.75)', borderColor: 'rgba(0, 184, 148, 1)', borderWidth: 1, borderRadius: 4 }},
                    {{ label: 'F1 Score', data: {_json.dumps(f1_data)}, backgroundColor: 'rgba(253, 203, 110, 0.85)', borderColor: 'rgba(253, 203, 110, 1)', borderWidth: 1, borderRadius: 4 }},
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 105, title: {{ display: true, text: 'Score (%)', font: {{ size: 12, weight: '600' }} }}, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(0,0,0,0.04)' }} }},
                    x: {{ title: {{ display: true, text: 'Model', font: {{ size: 12, weight: '600' }} }}, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ padding: 20 }} }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + '%' }} }}
                }}
            }}
        }});

        // ── 3. Confusion Matrix Stacked Bar ──
        new Chart(document.getElementById('confusionBarChart'), {{
            type: 'bar',
            data: {{
                labels: modelLabels,
                datasets: [
                    {{ label: 'True Positives', data: {_json.dumps(tp_data)}, backgroundColor: 'rgba(0, 184, 148, 0.8)', borderRadius: 2 }},
                    {{ label: 'True Negatives', data: {_json.dumps(tn_data)}, backgroundColor: 'rgba(178, 190, 195, 0.7)', borderRadius: 2 }},
                    {{ label: 'False Positives', data: {_json.dumps(fp_data)}, backgroundColor: 'rgba(253, 203, 110, 0.85)', borderRadius: 2 }},
                    {{ label: 'False Negatives', data: {_json.dumps(fn_data)}, backgroundColor: 'rgba(214, 48, 49, 0.75)', borderRadius: 2 }},
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{ stacked: true, beginAtZero: true, title: {{ display: true, text: 'Number of Predictions', font: {{ size: 12, weight: '600' }} }}, grid: {{ color: 'rgba(0,0,0,0.04)' }} }},
                    x: {{ stacked: true, title: {{ display: true, text: 'Model', font: {{ size: 12, weight: '600' }} }}, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ padding: 20 }} }}
                }}
            }}
        }});

        // ── 4. Confidence Horizontal Bar ──
        new Chart(document.getElementById('confidenceChart'), {{
            type: 'bar',
            data: {{
                labels: modelLabels,
                datasets: [{{
                    label: 'Avg Confidence %',
                    data: {_json.dumps(confidence_data)},
                    backgroundColor: chartColors.slice(0, modelLabels.length),
                    borderColor: chartBorders.slice(0, modelLabels.length),
                    borderWidth: 1,
                    borderRadius: 6,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Confidence Score (%)', font: {{ size: 12, weight: '600' }} }}, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(0,0,0,0.04)' }} }},
                    y: {{ title: {{ display: true, text: 'Model', font: {{ size: 12, weight: '600' }} }}, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: ctx => 'Avg Confidence: ' + ctx.parsed.x + '%' }} }}
                }}
            }}
        }});

        // ── 5. Per-Scenario Confidence Scores ──
        const scenarioLabels = {_json.dumps(all_scenario_ids)};
        const scenarioDatasets = modelLabels.map((model, i) => ({{
            label: model,
            data: {_json.dumps(scenario_confidence_data)}[model],
            backgroundColor: chartColors[i],
            borderColor: chartBorders[i],
            borderWidth: 1,
            borderRadius: 3,
        }}));
        new Chart(document.getElementById('scenarioChart'), {{
            type: 'bar',
            data: {{ labels: scenarioLabels, datasets: scenarioDatasets }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 105, title: {{ display: true, text: 'Confidence Score (%)', font: {{ size: 12, weight: '600' }} }}, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(0,0,0,0.04)' }} }},
                    x: {{ title: {{ display: true, text: 'Attack Scenario', font: {{ size: 12, weight: '600' }} }}, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ padding: 16 }} }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + '% confidence' }} }}
                }}
            }}
        }});

        // ── 6. F1 Doughnut Chart ──
        new Chart(document.getElementById('f1DoughnutChart'), {{
            type: 'doughnut',
            data: {{
                labels: modelLabels,
                datasets: [{{
                    data: {_json.dumps(f1_data)},
                    backgroundColor: chartColors.slice(0, modelLabels.length),
                    borderColor: 'white',
                    borderWidth: 3,
                    hoverOffset: 8,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                cutout: '55%',
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
                    tooltip: {{ callbacks: {{ label: ctx => ctx.label + ': ' + ctx.parsed + '% F1' }} }}
                }}
            }}
        }});

        // ── 7. FPR Bar Chart ──
        new Chart(document.getElementById('fprChart'), {{
            type: 'bar',
            data: {{
                labels: modelLabels,
                datasets: [{{
                    label: 'False Positive Rate %',
                    data: {_json.dumps(fpr_data)},
                    backgroundColor: {_json.dumps(fpr_data)}.map(v =>
                        v <= 5 ? 'rgba(0, 184, 148, 0.75)' :
                        v <= 15 ? 'rgba(253, 203, 110, 0.85)' :
                        'rgba(214, 48, 49, 0.75)'
                    ),
                    borderRadius: 6,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{ beginAtZero: true, title: {{ display: true, text: 'False Positive Rate (%)', font: {{ size: 12, weight: '600' }} }}, ticks: {{ callback: v => v + '%' }}, grid: {{ color: 'rgba(0,0,0,0.04)' }} }},
                    x: {{ title: {{ display: true, text: 'Model', font: {{ size: 12, weight: '600' }} }}, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ callbacks: {{ label: ctx => 'FPR: ' + ctx.parsed.y + '%' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"HTML report saved: {output_path}")

        return html


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Cyber Arena — Metrics Evaluator")
    parser.add_argument("--results-dir", default="results/",
                        help="Directory containing run result JSON files")
    parser.add_argument("--output-html", default=None,
                        help="Output HTML report path")
    parser.add_argument("--output-md", default=None,
                        help="Output Markdown report path")
    parser.add_argument("--json", action="store_true",
                        help="Print metrics as JSON to stdout")
    args = parser.parse_args()

    evaluator = MetricsEvaluator()
    evaluator.load_results_dir(args.results_dir)

    if not evaluator.runs:
        print("No runs found. Run scenarios first with: python -m arena.scenario_runner --scenario all")
        return

    report = evaluator.compute_all()

    # Output
    if args.output_html:
        evaluator.generate_html_report(report, args.output_html)
        print(f"HTML report: {args.output_html}")

    if args.output_md:
        evaluator.generate_markdown_report(report, args.output_md)
        print(f"MD report: {args.output_md}")

    if args.json:
        # Serialize report
        report_dict = asdict(report)
        print(json.dumps(report_dict, indent=2, default=str))
    elif not args.output_html and not args.output_md:
        # Print summary to console
        print(f"\n{'═'*60}")
        print(f"  EVALUATION SUMMARY")
        print(f"  Models: {report.models_evaluated} | Scenarios: {report.scenarios_evaluated}")
        print(f"  Total Runs: {report.total_runs}")
        print(f"  Best Model: {report.best_model} (F1={report.best_f1:.2%})")
        print(f"{'═'*60}\n")

        for model_id, mm in sorted(report.model_metrics.items()):
            print(f"  {model_id}:")
            print(f"    Accuracy={mm.overall_accuracy:.2%} Precision={mm.overall_precision:.2%} "
                  f"Recall={mm.overall_recall:.2%} F1={mm.overall_f1:.2%}")
            print(f"    FPR={mm.overall_fpr:.2%} TTP={mm.avg_ttp_coverage:.0%} "
                  f"Conf={mm.avg_confidence:.1f}% TTD={mm.avg_ttd_sec:.1f}s")
            print()


if __name__ == "__main__":
    main()
