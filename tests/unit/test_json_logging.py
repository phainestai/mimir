"""
Unit tests for JSON logging configuration.

Tests that prod settings use JSON formatter for CloudWatch compatibility.
"""

import pytest
import json
import logging
from io import StringIO


class TestJSONLoggingConfiguration:
    """Test JSON logging formatter in prod settings."""

    def test_prod_settings_has_json_formatter(self):
        """Prod settings should configure JSON formatter."""
        import os
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv('DJANGO_SECRET_KEY', 'test-key-for-import')
            from mimir.settings import prod
            
            assert 'json' in prod.LOGGING['formatters']
            json_formatter = prod.LOGGING['formatters']['json']
            assert '()' in json_formatter
            assert 'JsonFormatter' in json_formatter['()']

    def test_prod_settings_console_handler_uses_json(self):
        """Prod console handler should use JSON formatter."""
        import os
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv('DJANGO_SECRET_KEY', 'test-key-for-import')
            from mimir.settings import prod
            
            console_handler = prod.LOGGING['handlers']['console']
            assert console_handler['formatter'] == 'json'

    def test_json_formatter_produces_valid_json(self):
        """JSON formatter should produce parseable JSON output."""
        from pythonjsonlogger import jsonlogger
        
        # Create a logger with JSON formatter
        logger = logging.getLogger('test_json_logger')
        logger.setLevel(logging.INFO)
        
        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log a message
        logger.info("Test message", extra={'request_id': 'test-123'})
        
        # Parse output as JSON
        output = stream.getvalue().strip()
        parsed = json.loads(output)
        
        assert parsed['levelname'] == 'INFO'
        assert parsed['name'] == 'test_json_logger'
        assert parsed['message'] == 'Test message'
        assert 'asctime' in parsed

    def test_dev_settings_does_not_use_json_formatter(self):
        """Dev settings should use human-readable formatter."""
        from mimir.settings import dev
        
        # Dev should have 'verbose' and 'simple' formatters, not 'json'
        assert 'verbose' in dev.LOGGING['formatters']
        assert 'simple' in dev.LOGGING['formatters']
        assert 'json' not in dev.LOGGING['formatters']

    def test_test_settings_minimal_logging(self):
        """Test settings should have minimal logging."""
        from mimir.settings import test
        
        # Test should use NullHandler
        assert 'null' in test.LOGGING['handlers']
        assert test.LOGGING['handlers']['null']['class'] == 'logging.NullHandler'
