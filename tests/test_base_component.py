#!/usr/bin/env python3
"""
Tests for BaseComponent and DatabaseComponent classes
"""

import os
import tempfile
from unittest.mock import Mock, patch

import yaml

from src.core.base_component import BaseComponent, DatabaseComponent


class TestBaseComponent:
    """Test BaseComponent functionality"""

    def test_init_with_valid_config(self):
        """Test BaseComponent initialization with valid config file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"test": "value"}, f)
            config_path = f.name

        try:
            # Create concrete implementation for testing
            class TestComponent(BaseComponent):
                def connect(self, **kwargs):
                    return True

            component = TestComponent(config_path=config_path)
            assert component.config_path == config_path
            assert component.config == {"test": "value"}
            assert component.verbose is False
            assert component.logger is not None
        finally:
            os.unlink(config_path)

    def test_init_with_missing_config(self):
        """Test BaseComponent initialization with missing config file"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent(config_path="/nonexistent/path.yaml")
        assert component.config == {}
        assert component.config_path == "/nonexistent/path.yaml"

    def test_init_with_invalid_yaml(self):
        """Test BaseComponent initialization with invalid YAML"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name

        try:

            class TestComponent(BaseComponent):
                def connect(self, **kwargs):
                    return True

            component = TestComponent(config_path=config_path)
            assert component.config == {}
        finally:
            os.unlink(config_path)

    def test_verbose_logging(self):
        """Test verbose logging configuration"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent(verbose=True)
        assert component.verbose is True
        assert component.logger.level == 10  # DEBUG level

    def test_log_error_basic(self):
        """Test basic error logging"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        with patch.object(component.logger, "error") as mock_error:
            component.log_error("Test error message")
            mock_error.assert_called_once()

    def test_log_error_with_exception(self):
        """Test error logging with exception"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        test_exception = Exception("Test exception")

        with patch.object(component.logger, "error") as mock_error:
            component.log_error("Test error", exception=test_exception)
            mock_error.assert_called_once()

    def test_log_warning(self):
        """Test warning logging"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        with patch.object(component.logger, "warning") as mock_warning:
            component.log_warning("Test warning")
            mock_warning.assert_called_once_with("Test warning")

    def test_log_info(self):
        """Test info logging"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        with patch.object(component.logger, "info") as mock_info:
            component.log_info("Test info")
            mock_info.assert_called_once_with("Test info")

    def test_log_success(self):
        """Test success logging"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        with patch.object(component.logger, "info") as mock_info:
            component.log_success("Test success")
            mock_info.assert_called_once_with("Success: Test success")

    def test_context_manager_success(self):
        """Test context manager successful execution"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        with component as c:
            assert c == component

    def test_context_manager_with_exception(self):
        """Test context manager with exception during cleanup"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

            def close(self):
                raise Exception("Cleanup error")

        component = TestComponent()
        with patch.object(component, "log_error") as mock_log_error:
            with component:
                pass
            mock_log_error.assert_called_once()

    @patch("src.core.base_component.get_environment")
    def test_production_config_validation(self, mock_get_env):
        """Test production configuration validation"""
        mock_get_env.return_value = "production"

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

            def _validate_production_config(self):
                return False

        with patch.object(TestComponent, "_setup_logger") as mock_setup:
            mock_logger = Mock()
            mock_setup.return_value = mock_logger

            TestComponent()
            mock_logger.warning.assert_called_once_with(
                "Running in production without proper security configuration"
            )

    def test_close_method(self):
        """Test close method (default implementation)"""

        class TestComponent(BaseComponent):
            def connect(self, **kwargs):
                return True

        component = TestComponent()
        # Should not raise any exception
        component.close()


class TestDatabaseComponent:
    """Test DatabaseComponent functionality"""

    def test_init(self):
        """Test DatabaseComponent initialization"""

        class TestDBComponent(DatabaseComponent):
            def connect(self, **kwargs):
                return True

            def _get_service_name(self):
                return "test_db"

        component = TestDBComponent()
        assert component.connection is None
        assert component.is_connected is False

    def test_validate_production_config_ssl_disabled(self):
        """Test production config validation with SSL disabled"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"test_db": {"host": "localhost", "ssl": False}}, f)
            config_path = f.name

        try:

            class TestDBComponent(DatabaseComponent):
                def connect(self, **kwargs):
                    return True

                def _get_service_name(self):
                    return "test_db"

            with patch("src.core.base_component.get_environment") as mock_env:
                mock_env.return_value = "production"
                component = TestDBComponent(config_path=config_path)

                with patch.object(component, "log_warning") as mock_warning:
                    result = component._validate_production_config()
                    assert result is False
                    mock_warning.assert_called_once()
        finally:
            os.unlink(config_path)

    def test_validate_production_config_ssl_enabled(self):
        """Test production config validation with SSL enabled"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"test_db": {"host": "localhost", "ssl": True}}, f)
            config_path = f.name

        try:

            class TestDBComponent(DatabaseComponent):
                def connect(self, **kwargs):
                    return True

                def _get_service_name(self):
                    return "test_db"

            component = TestDBComponent(config_path=config_path)
            result = component._validate_production_config()
            assert result is True
        finally:
            os.unlink(config_path)

    def test_ensure_connected_when_connected(self):
        """Test ensure_connected when already connected"""

        class TestDBComponent(DatabaseComponent):
            def connect(self, **kwargs):
                return True

            def _get_service_name(self):
                return "test_db"

        component = TestDBComponent()
        component.is_connected = True
        assert component.ensure_connected() is True

    def test_ensure_connected_when_not_connected(self):
        """Test ensure_connected when not connected"""

        class TestDBComponent(DatabaseComponent):
            def connect(self, **kwargs):
                return True

            def _get_service_name(self):
                return "test_db"

        component = TestDBComponent()
        component.is_connected = False

        with patch.object(component, "log_error") as mock_log_error:
            result = component.ensure_connected()
            assert result is False
            mock_log_error.assert_called_once_with("Not connected to database")

    def test_validate_production_config_no_service_name(self):
        """Test production config validation when service name is None"""

        class TestDBComponent(DatabaseComponent):
            def connect(self, **kwargs):
                return True

            def _get_service_name(self):
                return None

        component = TestDBComponent()
        result = component._validate_production_config()
        assert result is True

    def test_validate_production_config_service_not_in_config(self):
        """Test production config validation when service is not in config"""

        class TestDBComponent(DatabaseComponent):
            def connect(self, **kwargs):
                return True

            def _get_service_name(self):
                return "nonexistent_service"

        component = TestDBComponent()
        with patch.object(component, "log_warning") as mock_warning:
            result = component._validate_production_config()
            assert result is False
            mock_warning.assert_called_once()
