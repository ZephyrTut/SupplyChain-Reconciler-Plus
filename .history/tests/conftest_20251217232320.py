import pytest


@pytest.fixture
def runner():
    """Provide a TestRunner instance for test_template_standalone.py when executed under pytest."""
    from tests.test_template_standalone import TestRunner

    return TestRunner()
