# import plotly.express as px
# # from test.test_triton import all_tone_peak_values, all_sfdr_values
# import pytest
# from docutils import nodes
# import pytest_html
# from py.xml import html
# # from pytest_html import html
# from pytest_metadata.plugin import metadata_key
# # from pytest_html import html
# import pytest



# def pytest_html_report_title(report):
#     report.title = f'ADXBAND16EBZ Test Report, SN:0004'

# def pytest_html_results_summary(prefix, summary, postfix):

#     # Add html paragraph to prefix
#     # prefix.extend([html.p("This is a custom report summary")])

#     # Add line break to prefix
#     prefix.extend([html.br()])

#     # Add image to prefix, must be relative to the html output (not absolute path)
#     # image_loc = f'Loopback_Sweep_SN{serial_number}.png'
#     # image2_loc = f'Filter_Test_1_SN{serial_number}.png'
#     # image3_loc = f'Filter_Test_2_SN{serial_number}.png'
#     # image4_loc = f'DSA_Test_SN{serial_number}.png'
#     # image5_loc = f'SFDR_Test_SN{serial_number}.png'
#     # if len(all_tone_peak_values) == 96:
#     #     image = html.img(src=image_loc, style="width: 300px;")
#     #     image2 = html.img(src=image2_loc, style="width: 300px;")
#     #     image3 = html.img(src=image3_loc, style="width: 300px;")
#     #     image4 = html.img(src=image4_loc, style="width: 300px;")
#     #     prefix.extend([image])
#     #     prefix.extend([image2])
#     #     prefix.extend([image3])
#     #     prefix.extend([image4])
#     # if len(all_sfdr_values) == 16:
#     #     image5 = html.img(src=image5_loc, style="width: 300px;")
#     #     prefix.extend([image5])
 
    

#     print(summary)
#     # summary.extend([r'<div>random_test</div>'])
#     # summary.append(html.html("<img src='/home/snuc/ADI/pyadi/testfig.png'>"))
#     # summary.append(html.html("<img src='/home/snuc/ADI/pyadi/testfig2.png'>"))
#     # summary.append(html.html("<img src='/home/snuc/ADI/pyadi/testfig3.png'>"))
#     # summary.append(html.html("<img src='/home/snuc/ADI/pyadi/testfig4.png'>"))
#     # summary.append(html.html("<img src='/home/snuc/ADI/pyadi/testfig5.png'>"))

#     for item in summary:
#         print(type(item))

# def pytest_html_results_summary(prefix, summary, postfix):

#     # Add html paragraph to prefix
#     prefix.extend([html.p("This is a custom report summary")])
 
#     # Add line break to prefix
#     prefix.extend([html.br()])
 
#     print(summary)

#     for item in summary:
#         print(type(item))



# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     outcome = yield
#     report = outcome.get_result()
#     if report.when == "call":
#         extra = getattr(report, "extra", [])
#         log_path = "test.log"  # Make sure this matches your pytest.ini log file

#         try:
#             with open(log_path, "r") as log_file:
#                 log_content = log_file.read()
#                 extra.append(pytest_html.extras.html(f'<pre>{log_content}</pre>'))
#         except FileNotFoundError:
#             extra.append(pytest_html.extras.html("<pre>Log file not found.</pre>"))

#         report.extra = extra

# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     outcome = yield
#     report = outcome.get_result()
#     if report.when == "call":
#         extra = getattr(report, "extra", [])
        
#         # Add FFT plot if available
#         if hasattr(pytest, "data_log") and "html" in pytest.data_log:
#             extra.append(pytest_html.extras.html(pytest.data_log["html"]))
            

#         report.extra = extra


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