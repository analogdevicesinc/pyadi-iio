import plotly.express as px
import pytest
from docutils import nodes
import pytest_html
from py.xml import html


def pytest_html_report_title(report):
    report.title = "pyadi-iio Test Report"

def pytest_html_results_summary(prefix, summary, postfix):

    # Add html paragraph to prefix
    prefix.extend([html.p("This is a custom report summary")])
 
    # Add line break to prefix
    prefix.extend([html.br()])
 
    # Add image to prefix, must be relative to the html output (not absolute path)
    image_loc = "adjacent.png"
    image2_loc = "combined.png"
    image = html.img(src=image_loc, style="width: 300px;")
    image2 = html.img(src=image2_loc, style="width: 300px;")
    prefix.extend([image])
    prefix.extend([image2])


    print(summary)
    print('test123')
    summary.extend([r'<div>random_test</div>'])
    summary.append(html.html("<img src='C:/ADI/Triton/pyadi-iio/adjacent.png'>"))
    summary.append(html.html("<img src='C:/ADI/Triton/pyadi-iio/combined.png'>"))

    for item in summary:
        print(type(item))


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
        if hasattr(pytest, "data"):
            # extra.append(pytest_html.extras.html(pytest.data["html"]))
            extra.append(pytest_html.extras.html(f'<div>{pytest.data}</div>'))
            report.extra = extra

