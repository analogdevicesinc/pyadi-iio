import plotly.express as px
import pytest


def pytest_html_report_title(report):
    report.title = "pyadi-iio Test Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    pytest_html = item.config.pluginmanager.getplugin("html")
    report = outcome.get_result()
    if report.when == "call":
        extra = getattr(report, "extra", [])
        report.description = str(item.function.__doc__)
        if hasattr(pytest, "data_log") and "html" in pytest.data_log.keys():
            extra.append(pytest_html.extras.html(pytest.data_log["html"]))
            report.extra = extra
