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
        """Generate an HTML evaluation report with the light-theme battery-report style."""
        mm_list = sorted(report.model_metrics.values(), key=lambda x: x.overall_f1, reverse=True)

        # Find best values for highlighting
        best_f1 = max((m.overall_f1 for m in mm_list), default=0)
        best_recall = max((m.overall_recall for m in mm_list), default=0)
        best_precision = max((m.overall_precision for m in mm_list), default=0)
        lowest_fpr = min((m.overall_fpr for m in mm_list), default=1)

        # Build scenario heatmap data
        all_scenario_ids = sorted(self.scenarios)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cyber Arena — Evaluation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f6fa;
            color: #2d3436;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #0984e3, #6c5ce7);
            color: white;
            padding: 32px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 24px; font-weight: 600; }}
        .header .subtitle {{ opacity: 0.85; font-size: 14px; margin-top: 4px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}

        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            border-top: 3px solid #0984e3;
        }}
        .summary-card.best {{ border-top-color: #00b894; }}
        .summary-card.warn {{ border-top-color: #fdcb6e; }}
        .summary-card .value {{ font-size: 28px; font-weight: 700; color: #0984e3; }}
        .summary-card.best .value {{ color: #00b894; }}
        .summary-card .label {{ font-size: 12px; color: #636e72; text-transform: uppercase; letter-spacing: 0.5px; }}

        /* Tables */
        .section {{ background: white; border-radius: 12px; padding: 24px; margin: 24px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size: 18px; color: #2d3436; margin-bottom: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th {{ background: #f8f9fa; padding: 10px 12px; text-align: left; font-weight: 600; color: #636e72; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }}
        tr:hover {{ background: #f8f9fa; }}
        .highlight {{ background: #e8f8f5 !important; font-weight: 600; }}
        .best-badge {{ background: #00b894; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}

        /* Metric bars */
        .metric-bar {{
            height: 6px;
            background: #ecf0f1;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 4px;
        }}
        .metric-bar .fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        .fill-green {{ background: linear-gradient(90deg, #00b894, #55efc4); }}
        .fill-blue {{ background: linear-gradient(90deg, #0984e3, #74b9ff); }}
        .fill-orange {{ background: linear-gradient(90deg, #fdcb6e, #ffeaa7); }}
        .fill-red {{ background: linear-gradient(90deg, #d63031, #ff7675); }}

        /* Heatmap */
        .heatmap {{ overflow-x: auto; }}
        .heatmap td {{ text-align: center; font-weight: 600; min-width: 60px; }}
        .heat-100 {{ background: #00b894; color: white; }}
        .heat-75 {{ background: #55efc4; color: #2d3436; }}
        .heat-50 {{ background: #ffeaa7; color: #2d3436; }}
        .heat-25 {{ background: #fab1a0; color: #2d3436; }}
        .heat-0 {{ background: #d63031; color: white; }}

        /* Footer */
        .footer {{ text-align: center; padding: 24px; color: #b2bec3; font-size: 12px; }}

        /* Confusion Matrix */
        .confusion {{ display: inline-grid; grid-template-columns: auto auto auto; gap: 2px; font-size: 13px; }}
        .confusion .cell {{ padding: 8px 16px; text-align: center; font-weight: 600; }}
        .confusion .tp {{ background: #e8f8f5; color: #00b894; }}
        .confusion .fp {{ background: #ffeaa7; color: #e17055; }}
        .confusion .fn {{ background: #fab1a0; color: #d63031; }}
        .confusion .tn {{ background: #dfe6e9; color: #636e72; }}
        .confusion .label-cell {{ background: #f8f9fa; font-weight: 400; font-size: 11px; color: #636e72; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ AI Cyber Arena — Evaluation Report</h1>
        <div class="subtitle">Generated: {report.timestamp} | {report.models_evaluated} models × {report.scenarios_evaluated} scenarios × {report.total_runs} runs</div>
    </div>
    <div class="container">
"""

        # Summary Cards
        html += '        <div class="summary-grid">\n'
        html += f'            <div class="summary-card best"><div class="value">{report.best_model or "–"}</div><div class="label">Best Model (F1)</div></div>\n'
        html += f'            <div class="summary-card best"><div class="value">{report.best_f1:.1%}</div><div class="label">Best F1 Score</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.models_evaluated}</div><div class="label">Models Evaluated</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.scenarios_evaluated}</div><div class="label">Scenarios</div></div>\n'
        html += f'            <div class="summary-card"><div class="value">{report.total_runs}</div><div class="label">Total Runs</div></div>\n'
        fpr_class = "warn" if report.worst_fpr > 0.1 else ""
        html += f'            <div class="summary-card {fpr_class}"><div class="value">{report.worst_fpr:.1%}</div><div class="label">Worst FPR</div></div>\n'
        html += '        </div>\n'

        # Model Comparison Table
        html += '        <div class="section">\n'
        html += '            <h2>📊 Model Comparison</h2>\n'
        html += '            <table>\n'
        html += '                <tr><th>Rank</th><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>FPR</th><th>TTP Cov.</th><th>Avg Conf.</th><th>TTD</th></tr>\n'

        for rank, mm in enumerate(mm_list, 1):
            is_best = mm.overall_f1 == best_f1 and len(mm_list) > 1
            row_class = ' class="highlight"' if is_best else ""
            badge = ' <span class="best-badge">BEST</span>' if is_best else ""

            html += f'                <tr{row_class}>\n'
            html += f'                    <td>#{rank}</td>\n'
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

        # Scenario Heatmap
        if all_scenario_ids and mm_list:
            html += '        <div class="section">\n'
            html += '            <h2>🔥 Per-Scenario Detection Heatmap</h2>\n'
            html += '            <div class="heatmap"><table>\n'
            html += f'                <tr><th>Model</th>'
            for sid in all_scenario_ids:
                html += f'<th>{sid}</th>'
            html += '</tr>\n'

            for mm in mm_list:
                html += f'                <tr><td><strong>{mm.model_id}</strong></td>'
                for sid in all_scenario_ids:
                    sm = mm.scenario_metrics.get(sid)
                    if sm:
                        rate = sm.detection_rate
                        heat = "heat-100" if rate >= 1.0 else ("heat-75" if rate >= 0.75 else ("heat-50" if rate >= 0.5 else ("heat-25" if rate > 0 else "heat-0")))
                        html += f'<td class="{heat}">{rate:.0%}</td>'
                    else:
                        html += '<td>—</td>'
                html += '</tr>\n'

            html += '            </table></div>\n'
            html += '        </div>\n'

        # Per-model cards
        for mm in mm_list:
            html += f'        <div class="section">\n'
            html += f'            <h2>🤖 {mm.model_id}</h2>\n'

            # Confusion matrix
            html += '            <div class="confusion">\n'
            html += '                <div class="label-cell"></div><div class="label-cell">Predicted +</div><div class="label-cell">Predicted −</div>\n'
            html += f'                <div class="label-cell">Actual +</div><div class="cell tp">TP: {mm.confusion.tp}</div><div class="cell fn">FN: {mm.confusion.fn}</div>\n'
            html += f'                <div class="label-cell">Actual −</div><div class="cell fp">FP: {mm.confusion.fp}</div><div class="cell tn">TN: {mm.confusion.tn}</div>\n'
            html += '            </div>\n'

            # Scenario table
            if mm.scenario_metrics:
                html += '            <table style="margin-top:16px">\n'
                html += '                <tr><th>Scenario</th><th>Detection</th><th>Classification</th><th>Confidence</th><th>TTP Coverage</th><th>Pass@k</th></tr>\n'
                for sid, sm in sorted(mm.scenario_metrics.items()):
                    html += f'                <tr><td>{sid}</td><td>{sm.detection_rate:.0%}</td><td>{sm.classification_rate:.0%}</td><td>{sm.avg_confidence:.1f}%</td><td>{sm.avg_ttp_coverage:.0%}</td><td>{sm.pass_at_k:.0%} ({sm.correct_detections}/{sm.num_runs})</td></tr>\n'
                html += '            </table>\n'

            html += '        </div>\n'

        # Footer
        html += f"""
        <div class="footer">
            AI Cyber Arena — Evaluation Framework v1.0<br>
            NIST SP 800-61r3 compliant | MITRE ATT&CK for ICS aligned<br>
            Report generated: {report.timestamp}
        </div>
    </div>
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
