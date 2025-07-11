#!/usr/bin/env python3
"""
context_analytics.py: Advanced analytics for the Agent-First Context System

This component provides:
1. Time-series analysis of context metrics
2. Agent performance tracking
3. Document lifecycle analytics
4. System health monitoring
"""

import click
import yaml
import json
import duckdb
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from context_kv import DuckDBAnalytics, MetricEvent


@dataclass
class AnalyticsReport:
    """Represents an analytics report"""

    report_type: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]


class ContextAnalytics(DuckDBAnalytics):
    """Extended analytics for context system"""

    def __init__(self, config_path: str = ".ctxrc.yaml", verbose: bool = False):
        super().__init__(config_path, verbose)
        self.report_cache: Dict[str, AnalyticsReport] = {}

    def analyze_document_lifecycle(self, days: int = 30) -> AnalyticsReport:
        """Analyze document lifecycle patterns"""
        if not self.ensure_connected():
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        try:
            # Get document metrics
            query = """
                SELECT 
                    DATE_TRUNC('day', timestamp) as day,
                    COUNT(DISTINCT document_id) as active_documents,
                    COUNT(CASE WHEN metric_name = 'document.created' THEN 1 END) as created,
                    COUNT(CASE WHEN metric_name = 'document.updated' THEN 1 END) as updated,
                    COUNT(CASE WHEN metric_name = 'document.archived' THEN 1 END) as archived,
                    COUNT(CASE WHEN metric_name = 'document.accessed' THEN 1 END) as accessed
                FROM context_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                    AND document_id IS NOT NULL
                GROUP BY day
                ORDER BY day
            """

            results = self.query_metrics(query, [start_date, end_date])

            # Calculate trends
            if results:
                # Limit results to prevent memory issues
                max_rows = 10000
                if len(results) > max_rows:
                    self.log_warning(f"Truncating results from {len(results)} to {max_rows} rows")
                    results = results[:max_rows]

                df = pd.DataFrame(results)

                metrics = {
                    "total_active": int(df["active_documents"].sum()),
                    "avg_daily_created": float(df["created"].mean()),
                    "avg_daily_updated": float(df["updated"].mean()),
                    "avg_daily_accessed": float(df["accessed"].mean()),
                    "churn_rate": float(
                        df["archived"].sum() / max(df["active_documents"].sum(), 1)
                    ),
                    "update_frequency": float(
                        df["updated"].sum() / max(df["active_documents"].sum(), 1)
                    ),
                }

                # Generate insights
                insights = []
                if metrics["churn_rate"] > 0.2:
                    insights.append(
                        f"High document churn rate ({metrics['churn_rate']:.1%}) indicates frequent archiving"
                    )

                if metrics["update_frequency"] < 0.1:
                    insights.append("Low update frequency suggests documents may be stale")

                if metrics["avg_daily_accessed"] < metrics["avg_daily_created"]:
                    insights.append("More documents created than accessed - consider cleanup")

                # Recommendations
                recommendations = []
                if metrics["churn_rate"] > 0.2:
                    recommendations.append("Review document retention policies")

                if metrics["avg_daily_accessed"] < 1:
                    recommendations.append("Implement document discovery features")

            else:
                metrics = {}
                insights = ["No document activity in the specified period"]
                recommendations = ["Start tracking document metrics"]

            return AnalyticsReport(
                report_type="document_lifecycle",
                period_start=start_date,
                period_end=end_date,
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
            )

        except Exception as e:
            self.log_error("Failed to analyze document lifecycle", e)
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

    def analyze_agent_performance(self, days: int = 7) -> AnalyticsReport:
        """Analyze agent performance metrics"""
        if not self.ensure_connected():
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        try:
            # Get agent metrics
            query = """
                SELECT 
                    agent_id,
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN metric_name LIKE 'agent.%.success' THEN 1 END) as successes,
                    COUNT(CASE WHEN metric_name LIKE 'agent.%.failure' THEN 1 END) as failures,
                    AVG(CASE WHEN metric_name LIKE 'agent.%.duration' THEN value END) as avg_duration,
                    MAX(timestamp) as last_active
                FROM context_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                    AND agent_id IS NOT NULL
                GROUP BY agent_id
            """

            results = self.query_metrics(query, [start_date, end_date])

            metrics = {
                "total_agents": len(results),
                "total_actions": sum(r["total_actions"] for r in results),
                "overall_success_rate": 0,
                "agent_metrics": {},
            }

            insights = []
            recommendations = []

            if results:
                # Calculate per-agent metrics
                for agent in results:
                    success_rate = agent["successes"] / max(
                        agent["successes"] + agent["failures"], 1
                    )

                    metrics["agent_metrics"][agent["agent_id"]] = {
                        "actions": agent["total_actions"],
                        "success_rate": success_rate,
                        "avg_duration": agent["avg_duration"] or 0,
                        "last_active": agent["last_active"],
                    }

                    # Agent-specific insights
                    if success_rate < 0.8:
                        insights.append(
                            f"Agent {agent['agent_id']} has low success rate ({success_rate:.1%})"
                        )

                    if agent["avg_duration"] and agent["avg_duration"] > 30:
                        insights.append(
                            f"Agent {agent['agent_id']} has high average duration ({agent['avg_duration']:.1f}s)"
                        )

                # Overall metrics
                total_successes = sum(r["successes"] for r in results)
                total_failures = sum(r["failures"] for r in results)
                metrics["overall_success_rate"] = total_successes / max(
                    total_successes + total_failures, 1
                )

                if metrics["overall_success_rate"] < 0.9:
                    recommendations.append("Investigate and fix failing agent operations")

                # Check for inactive agents
                now = datetime.utcnow()
                for agent_id, agent_data in metrics["agent_metrics"].items():
                    last_active = datetime.fromisoformat(agent_data["last_active"])
                    if (now - last_active).days > 1:
                        insights.append(
                            f"Agent {agent_id} has been inactive for {(now - last_active).days} days"
                        )

            else:
                insights.append("No agent activity recorded")
                recommendations.append("Ensure agents are properly instrumented")

            return AnalyticsReport(
                report_type="agent_performance",
                period_start=start_date,
                period_end=end_date,
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
            )

        except Exception as e:
            self.log_error("Failed to analyze agent performance", e)
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

    def analyze_system_health(self) -> AnalyticsReport:
        """Analyze overall system health"""
        if not self.ensure_connected():
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        try:
            # Get system metrics
            metrics_query = """
                SELECT 
                    metric_name,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as count
                FROM context_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                    AND metric_name LIKE 'system.%'
                GROUP BY metric_name
            """

            results = self.query_metrics(metrics_query, [start_date, end_date])

            # Get error counts
            error_query = """
                SELECT 
                    COUNT(CASE WHEN metric_name LIKE '%.error' THEN 1 END) as error_count,
                    COUNT(CASE WHEN metric_name LIKE '%.warning' THEN 1 END) as warning_count
                FROM context_metrics
                WHERE timestamp >= ? AND timestamp <= ?
            """

            error_results = self.query_metrics(error_query, [start_date, end_date])

            metrics = {
                "period_hours": 24,
                "system_metrics": {r["metric_name"]: r for r in results},
                "error_count": error_results[0]["error_count"] if error_results else 0,
                "warning_count": error_results[0]["warning_count"] if error_results else 0,
            }

            insights = []
            recommendations = []

            # Check for high error rates
            if metrics["error_count"] > 100:
                insights.append(f"High error count ({metrics['error_count']}) in last 24 hours")
                recommendations.append("Review error logs and address root causes")

            # Check system metrics
            for metric_name, metric_data in metrics["system_metrics"].items():
                if "cpu" in metric_name and metric_data["max_value"] > 80:
                    insights.append(
                        f"High CPU usage detected (max: {metric_data['max_value']:.1f}%)"
                    )
                    recommendations.append("Consider scaling resources or optimizing performance")

                if "memory" in metric_name and metric_data["max_value"] > 90:
                    insights.append(
                        f"High memory usage detected (max: {metric_data['max_value']:.1f}%)"
                    )
                    recommendations.append("Review memory usage patterns and optimize")

                if "latency" in metric_name and metric_data["avg_value"] > 1000:
                    insights.append(
                        f"High latency detected (avg: {metric_data['avg_value']:.0f}ms)"
                    )
                    recommendations.append("Investigate slow operations and optimize queries")

            # Overall health score (0-100)
            health_score = 100
            health_score -= min(metrics["error_count"] / 10, 30)  # Max 30 point penalty for errors
            health_score -= min(
                metrics["warning_count"] / 50, 20
            )  # Max 20 point penalty for warnings

            # Deduct for missing metrics
            expected_metrics = ["system.cpu", "system.memory", "system.disk"]
            for metric in expected_metrics:
                if metric not in metrics["system_metrics"]:
                    health_score -= 10
                    insights.append(f"Missing metric: {metric}")

            metrics["health_score"] = max(health_score, 0)

            if metrics["health_score"] < 70:
                insights.insert(0, f"System health is degraded (score: {metrics['health_score']})")
                recommendations.insert(0, "Immediate attention required for system health")

            return AnalyticsReport(
                report_type="system_health",
                period_start=start_date,
                period_end=end_date,
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
            )

        except Exception as e:
            self.log_error("Failed to analyze system health", e)
            return AnalyticsReport(
                report_type="error",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                insights=[],
                recommendations=[],
            )

    def generate_executive_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generate executive summary of all analytics"""
        reports = {
            "document_lifecycle": self.analyze_document_lifecycle(days),
            "agent_performance": self.analyze_agent_performance(days),
            "system_health": self.analyze_system_health(),
        }

        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "key_metrics": {},
            "top_insights": [],
            "priority_actions": [],
        }

        # Extract key metrics
        if reports["document_lifecycle"]:
            summary["key_metrics"]["active_documents"] = reports["document_lifecycle"].metrics.get(
                "total_active", 0
            )
            summary["key_metrics"]["document_churn"] = reports["document_lifecycle"].metrics.get(
                "churn_rate", 0
            )

        if reports["agent_performance"]:
            summary["key_metrics"]["agent_success_rate"] = reports["agent_performance"].metrics.get(
                "overall_success_rate", 0
            )
            summary["key_metrics"]["total_agent_actions"] = reports[
                "agent_performance"
            ].metrics.get("total_actions", 0)

        if reports["system_health"]:
            summary["key_metrics"]["system_health_score"] = reports["system_health"].metrics.get(
                "health_score", 0
            )
            summary["key_metrics"]["error_count_24h"] = reports["system_health"].metrics.get(
                "error_count", 0
            )

        # Compile top insights
        for report_name, report in reports.items():
            if report and report.insights:
                summary["top_insights"].extend(
                    [f"[{report_name}] {insight}" for insight in report.insights[:2]]
                )

        # Compile priority actions
        priority_order = {"system_health": 1, "agent_performance": 2, "document_lifecycle": 3}

        all_recommendations = []
        for report_name, report in reports.items():
            if report and report.recommendations:
                for rec in report.recommendations:
                    all_recommendations.append((priority_order.get(report_name, 99), rec))

        all_recommendations.sort(key=lambda x: x[0])
        summary["priority_actions"] = [rec[1] for rec in all_recommendations[:5]]

        return summary

    def export_analytics_data(self, output_path: str, format: str = "parquet") -> bool:
        """Export analytics data for external analysis"""
        if not self.ensure_connected():
            return False

        try:
            # Export metrics data
            query = """
                SELECT * FROM context_metrics
                WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY timestamp
            """

            if format == "parquet":
                self.conn.execute(
                    f"""
                    COPY ({query}) TO '{output_path}/metrics.parquet' (FORMAT PARQUET)
                """
                )
            elif format == "csv":
                self.conn.execute(
                    f"""
                    COPY ({query}) TO '{output_path}/metrics.csv' (FORMAT CSV, HEADER)
                """
                )
            else:
                self.log_error(f"Unsupported export format: {format}")
                return False

            # Export summaries
            summaries_query = "SELECT * FROM context_summaries ORDER BY summary_date"

            if format == "parquet":
                self.conn.execute(
                    f"""
                    COPY ({summaries_query}) TO '{output_path}/summaries.parquet' (FORMAT PARQUET)
                """
                )
            elif format == "csv":
                self.conn.execute(
                    f"""
                    COPY ({summaries_query}) TO '{output_path}/summaries.csv' (FORMAT CSV, HEADER)
                """
                )

            self.log_success(f"Exported analytics data to {output_path}")
            return True

        except Exception as e:
            self.log_error("Failed to export analytics data", e)
            return False


@click.group()
def cli():
    """Context Analytics Commands"""
    pass


@cli.command()
@click.option("--days", default=30, help="Days to analyze")
@click.option(
    "--report-type",
    type=click.Choice(["document", "agent", "health", "all"]),
    default="all",
    help="Type of report to generate",
)
def analyze(days: int, report_type: str):
    """Generate analytics reports"""
    analytics = ContextAnalytics(verbose=True)

    if not analytics.connect():
        click.echo("Failed to connect to analytics database", err=True)
        return

    try:
        if report_type == "document" or report_type == "all":
            report = analytics.analyze_document_lifecycle(days)
            if report:
                click.echo("\n=== Document Lifecycle Analysis ===")
                click.echo(f"Period: {report.period_start.date()} to {report.period_end.date()}")
                click.echo("\nMetrics:")
                for key, value in report.metrics.items():
                    click.echo(f"  {key}: {value}")
                click.echo("\nInsights:")
                for insight in report.insights:
                    click.echo(f"  • {insight}")
                click.echo("\nRecommendations:")
                for rec in report.recommendations:
                    click.echo(f"  → {rec}")

        if report_type == "agent" or report_type == "all":
            report = analytics.analyze_agent_performance(days)
            if report:
                click.echo("\n=== Agent Performance Analysis ===")
                click.echo(f"Period: {report.period_start.date()} to {report.period_end.date()}")
                click.echo(
                    f"\nOverall Success Rate: {report.metrics.get('overall_success_rate', 0):.1%}"
                )
                click.echo(f"Total Actions: {report.metrics.get('total_actions', 0)}")

                if report.metrics.get("agent_metrics"):
                    click.echo("\nPer-Agent Metrics:")
                    for agent_id, metrics in report.metrics["agent_metrics"].items():
                        click.echo(f"  {agent_id}:")
                        click.echo(f"    Actions: {metrics['actions']}")
                        click.echo(f"    Success Rate: {metrics['success_rate']:.1%}")
                        click.echo(f"    Avg Duration: {metrics['avg_duration']:.1f}s")

                click.echo("\nInsights:")
                for insight in report.insights:
                    click.echo(f"  • {insight}")
                click.echo("\nRecommendations:")
                for rec in report.recommendations:
                    click.echo(f"  → {rec}")

        if report_type == "health" or report_type == "all":
            report = analytics.analyze_system_health()
            if report:
                click.echo("\n=== System Health Analysis ===")
                click.echo(f"Health Score: {report.metrics.get('health_score', 0)}/100")
                click.echo(f"Errors (24h): {report.metrics.get('error_count', 0)}")
                click.echo(f"Warnings (24h): {report.metrics.get('warning_count', 0)}")

                click.echo("\nInsights:")
                for insight in report.insights:
                    click.echo(f"  • {insight}")
                click.echo("\nRecommendations:")
                for rec in report.recommendations:
                    click.echo(f"  → {rec}")

        if report_type == "all":
            click.echo("\n=== Executive Summary ===")
            summary = analytics.generate_executive_summary(days)

            click.echo("\nKey Metrics:")
            for metric, value in summary["key_metrics"].items():
                if isinstance(value, float) and value < 1:
                    click.echo(f"  {metric}: {value:.1%}")
                else:
                    click.echo(f"  {metric}: {value}")

            click.echo("\nTop Insights:")
            for insight in summary["top_insights"]:
                click.echo(f"  • {insight}")

            click.echo("\nPriority Actions:")
            for i, action in enumerate(summary["priority_actions"], 1):
                click.echo(f"  {i}. {action}")

    finally:
        analytics.close()


@cli.command()
@click.option("--output-dir", required=True, help="Directory to export data")
@click.option(
    "--format", type=click.Choice(["parquet", "csv"]), default="parquet", help="Export format"
)
def export(output_dir: str, format: str):
    """Export analytics data"""
    analytics = ContextAnalytics(verbose=True)

    if not analytics.connect():
        click.echo("Failed to connect to analytics database", err=True)
        return

    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if analytics.export_analytics_data(output_dir, format):
            click.echo(f"✓ Analytics data exported to {output_dir}")
        else:
            click.echo("✗ Export failed", err=True)

    finally:
        analytics.close()


if __name__ == "__main__":
    cli()
