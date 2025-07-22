#!/usr/bin/env python3
"""
Tests for context_analytics module
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from click.testing import CliRunner

from src.analytics.context_analytics import AnalyticsReport, ContextAnalytics, analyze, cli, export


class TestAnalyticsReport:
    """Tests for AnalyticsReport dataclass"""

    def test_analytics_report_creation(self) -> None:
        """Test creating an AnalyticsReport"""
        now = datetime.utcnow()
        report = AnalyticsReport(
            report_type="test",
            period_start=now - timedelta(days=7),
            period_end=now,
            metrics={"test_metric": 100},
            insights=["Test insight"],
            recommendations=["Test recommendation"],
        )

        assert report.report_type == "test"
        assert report.period_end == now
        assert report.metrics["test_metric"] == 100
        assert len(report.insights) == 1
        assert len(report.recommendations) == 1


class TestContextAnalytics:
    """Tests for ContextAnalytics class"""

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.mock_config = {
            "duckdb": {"database_path": ":memory:"},
            "system": {"project_name": "test_project"},
        }

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_init(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test ContextAnalytics initialization"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        assert analytics.report_cache == {}
        assert analytics.config == self.mock_config

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_document_lifecycle_no_connection(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_document_lifecycle when connection fails"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        # Mock ensure_connected to return False
        analytics.ensure_connected = Mock(return_value=False)  # type: ignore[method-assign]

        report = analytics.analyze_document_lifecycle()

        assert report.report_type == "error"
        assert report.metrics == {}
        assert report.insights == []
        assert report.recommendations == []

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_document_lifecycle_with_data(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_document_lifecycle with successful data retrieval"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock query results
        mock_results = [
            {
                "document_type": "design",
                "created": 10,
                "updated": 5,
                "archived": 2,
                "accessed": 100,
                "avg_age_days": 15.5,
                "active_documents": 20,
            },
            {
                "document_type": "decision",
                "created": 8,
                "updated": 3,
                "archived": 1,
                "accessed": 50,
                "avg_age_days": 20.0,
                "active_documents": 15,
            },
        ]
        analytics.query_metrics = Mock(return_value=mock_results)  # type: ignore[method-assign]

        report = analytics.analyze_document_lifecycle(days=30)

        assert report.report_type == "document_lifecycle"
        assert report.metrics["total_active"] == 35  # 20 + 15 active documents
        assert "avg_daily_created" in report.metrics
        assert "avg_daily_updated" in report.metrics
        assert "churn_rate" in report.metrics
        assert "update_frequency" in report.metrics
        assert len(report.insights) >= 0

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_document_lifecycle_exception(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_document_lifecycle with exception"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]
        analytics.query_metrics = Mock(  # type: ignore[method-assign]
            side_effect=Exception("Database error")
        )

        report = analytics.analyze_document_lifecycle()

        assert report.report_type == "error"
        # When an exception occurs, insights list is empty
        assert len(report.insights) == 0

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_agent_performance_with_data(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_agent_performance with successful data retrieval"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock query results
        mock_results = [
            {
                "agent_id": "cleanup_agent",
                "total_actions": 100,
                "successes": 90,
                "failures": 10,
                "avg_duration": 5.5,
                "last_active": datetime.utcnow().isoformat(),
            },
            {
                "agent_id": "update_agent",
                "total_actions": 50,
                "successes": 35,
                "failures": 15,
                "avg_duration": 45.0,  # High duration
                "last_active": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            },
        ]
        analytics.query_metrics = Mock(return_value=mock_results)  # type: ignore[method-assign]

        report = analytics.analyze_agent_performance(days=7)

        assert report.report_type == "agent_performance"
        assert report.metrics["total_agents"] == 2
        assert report.metrics["total_actions"] == 150
        assert report.metrics["overall_success_rate"] == 0.8333333333333334

        # Check agent-specific metrics
        assert "cleanup_agent" in report.metrics["agent_metrics"]
        assert report.metrics["agent_metrics"]["cleanup_agent"]["success_rate"] == 0.9

        # Check insights
        assert any("low success rate" in insight for insight in report.insights)
        assert any("high average duration" in insight for insight in report.insights)
        assert any("inactive for" in insight for insight in report.insights)

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_agent_performance_no_data(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_agent_performance with no data"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]
        analytics.query_metrics = Mock(return_value=[])  # type: ignore[method-assign]

        report = analytics.analyze_agent_performance()

        assert report.metrics["total_agents"] == 0
        assert "No agent activity recorded" in report.insights
        assert "Ensure agents are properly instrumented" in report.recommendations

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_analyze_system_health_with_data(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test analyze_system_health with successful data retrieval"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock various query results
        # System metrics
        analytics.query_metrics = Mock(  # type: ignore[method-assign]
            side_effect=[
                [  # System metrics query
                    {
                        "metric_name": "system.cpu",
                        "avg_value": 45.0,
                        "min_value": 10.0,
                        "max_value": 85.0,
                        "count": 100,
                    },
                    {
                        "metric_name": "system.memory",
                        "avg_value": 60.0,
                        "min_value": 40.0,
                        "max_value": 90.0,
                        "count": 100,
                    },
                ],
                [{"error_count": 5, "warning_count": 10}],  # Error query
            ]
        )

        report = analytics.analyze_system_health()  # No hours parameter

        assert report.report_type == "system_health"
        assert report.metrics["error_count"] == 5
        assert report.metrics["warning_count"] == 10
        assert "system_metrics" in report.metrics
        assert "system.cpu" in report.metrics["system_metrics"]
        assert "system.memory" in report.metrics["system_metrics"]

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_generate_executive_summary(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test generate_executive_summary"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()

        # Create mock reports
        doc_report = AnalyticsReport(
            report_type="document_lifecycle",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            metrics={"total_documents": 100, "total_updates": 50},
            insights=["High document activity"],
            recommendations=["Consider archiving old documents"],
        )

        agent_report = AnalyticsReport(
            report_type="agent_performance",
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            metrics={"total_agents": 5, "overall_success_rate": 0.85},
            insights=["Agent performance is good"],
            recommendations=["Monitor failing agents"],
        )

        health_report = AnalyticsReport(
            report_type="system_health",
            period_start=datetime.utcnow() - timedelta(hours=24),
            period_end=datetime.utcnow(),
            metrics={"health_score": 85, "total_errors": 10},
            insights=["System is healthy"],
            recommendations=["Reduce error rate"],
        )

        # Mock the analysis methods
        analytics.analyze_document_lifecycle = Mock(  # type: ignore[method-assign]
            return_value=doc_report
        )
        analytics.analyze_agent_performance = Mock(  # type: ignore[method-assign]
            return_value=agent_report
        )
        analytics.analyze_system_health = Mock(  # type: ignore[method-assign]
            return_value=health_report
        )

        summary = analytics.generate_executive_summary()

        assert isinstance(summary, dict)
        assert "key_metrics" in summary
        assert "top_insights" in summary
        assert "priority_actions" in summary
        assert len(summary["top_insights"]) > 0
        assert len(summary["priority_actions"]) > 0

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_export_analytics_data_parquet(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test export_analytics_data in parquet format"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock connection and execute
        mock_conn = Mock()
        analytics.conn = mock_conn

        result = analytics.export_analytics_data("/tmp/export", format="parquet")

        assert result is True
        assert mock_conn.execute.called
        # Check that COPY commands were executed
        calls = mock_conn.execute.call_args_list
        assert any("metrics.parquet" in str(call) for call in calls)
        assert any("summaries.parquet" in str(call) for call in calls)

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_export_analytics_data_csv(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test export_analytics_data in CSV format"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock connection and execute
        mock_conn = Mock()
        analytics.conn = mock_conn

        result = analytics.export_analytics_data("/tmp/export", format="csv")

        assert result is True
        assert mock_conn.execute.called
        # Check that COPY commands were executed
        calls = mock_conn.execute.call_args_list
        assert any("metrics.csv" in str(call) for call in calls)
        assert any("summaries.csv" in str(call) for call in calls)

    @patch("src.analytics.context_analytics.Path.exists")
    @patch("builtins.open", create=True)
    @patch("yaml.safe_load")
    def test_export_analytics_data_invalid_format(self, mock_yaml_load, mock_open, mock_exists) -> None:
        """Test export_analytics_data with invalid format"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.mock_config

        analytics = ContextAnalytics()
        analytics.ensure_connected = Mock(return_value=True)  # type: ignore[method-assign]

        # Mock connection
        mock_conn = Mock()
        analytics.conn = mock_conn

        result = analytics.export_analytics_data("/tmp/export", format="invalid")

        assert result is False
        # The execute method should not have been called for invalid format
        assert not mock_conn.execute.called


class TestCLI:
    """Tests for CLI commands"""

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.runner = CliRunner()

    @patch("src.analytics.context_analytics.ContextAnalytics")
    def test_cli_main(self, mock_analytics_class) -> None:
        """Test main CLI command"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Context Analytics Commands" in result.output

    @patch("src.analytics.context_analytics.ContextAnalytics")
    def test_cli_analyze_all(self, mock_analytics_class) -> None:
        """Test analyze command with all reports"""
        mock_analytics = mock_analytics_class.return_value
        mock_analytics.connect.return_value = True

        # Mock the report methods
        mock_report = Mock()
        mock_report.report_type = "test"
        mock_report.metrics = {"test": 100}
        mock_report.insights = ["Test insight"]
        mock_report.recommendations = ["Test recommendation"]

        mock_analytics.analyze_document_lifecycle.return_value = mock_report
        mock_analytics.analyze_agent_performance.return_value = mock_report
        mock_analytics.analyze_system_health.return_value = mock_report
        mock_analytics.generate_executive_summary.return_value = {
            "key_metrics": {"health_score": 85},
            "top_insights": ["System is healthy"],
            "priority_actions": ["Continue monitoring"],
        }

        result = self.runner.invoke(analyze, ["--report-type", "all"])

        assert result.exit_code == 0

    @patch("src.analytics.context_analytics.ContextAnalytics")
    def test_cli_analyze_document(self, mock_analytics_class) -> None:
        """Test analyze command with document report"""
        mock_analytics = mock_analytics_class.return_value
        mock_analytics.connect.return_value = True

        mock_report = Mock()
        mock_report.report_type = "document_lifecycle"
        mock_report.metrics = {"total_documents": 100}
        mock_report.insights = ["High document count"]
        mock_report.recommendations = []

        mock_analytics.analyze_document_lifecycle.return_value = mock_report

        result = self.runner.invoke(analyze, ["--report-type", "document", "--days", "30"])

        assert result.exit_code == 0

    @patch("src.analytics.context_analytics.ContextAnalytics")
    def test_cli_analyze_connection_error(self, mock_analytics_class) -> None:
        """Test analyze command with connection error"""
        mock_analytics = mock_analytics_class.return_value
        mock_analytics.connect.return_value = False

        result = self.runner.invoke(analyze, ["--report-type", "all"])

        assert result.exit_code == 0  # The command doesn't exit with error code
        assert "Failed to connect" in result.output

    @patch("src.analytics.context_analytics.ContextAnalytics")
    @patch("src.analytics.context_analytics.Path")
    def test_cli_export(self, mock_path, mock_analytics_class) -> None:
        """Test export command"""
        mock_analytics = mock_analytics_class.return_value
        mock_analytics.connect.return_value = True
        mock_analytics.export_analytics_data.return_value = True

        result = self.runner.invoke(export, ["--output-dir", "/tmp/export", "--format", "parquet"])

        assert result.exit_code == 0
        assert "Analytics data exported to /tmp/export" in result.output

    @patch("src.analytics.context_analytics.ContextAnalytics")
    def test_cli_export_connection_error(self, mock_analytics_class) -> None:
        """Test export command with connection error"""
        mock_analytics = mock_analytics_class.return_value
        mock_analytics.connect.return_value = False

        result = self.runner.invoke(export, ["--output-dir", "/tmp/export", "--format", "csv"])

        assert result.exit_code == 0
        assert "Failed to connect" in result.output
