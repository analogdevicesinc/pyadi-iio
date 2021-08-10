import plotly.express as px

plotlycdn = '<script src="https://cdn.plot.ly/plotly-2.0.0.js"></script>'


def gen_line_plot_html(x, y, xlabel, ylabel, title):
    fig = px.line(x=x, y=y)
    fig.update_layout(
        title=title, xaxis_title=xlabel, yaxis_title=ylabel,
    )
    html = fig.to_html(include_plotlyjs=False)
    return plotlycdn + "<div>" + html + "</div>"
