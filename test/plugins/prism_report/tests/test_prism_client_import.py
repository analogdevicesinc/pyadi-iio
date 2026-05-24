"""Smoke test: vendored _prism_client.py imports and instantiates."""
from test.plugins.prism_report._prism_client import PrismClient


def test_can_instantiate():
    c = PrismClient("http://example.invalid")
    assert c.base_url == "http://example.invalid"
