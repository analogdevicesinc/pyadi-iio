import pytest

# Enable rewriting of imports in test modules so asserts print comparison
# Reference: https://docs.pytest.org/en/stable/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("test.dma_tests")
pytest.register_assert_rewrite("test.attr_tests")
