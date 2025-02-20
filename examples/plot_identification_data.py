import numpy as np
import matplotlib.pyplot as plt
import random
from dash import Dash, html, dcc, dash_table
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import pandas as pd
import scipy.io
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.metrics import roc_curve, roc_auc_score

app = Dash(__name__)

# Data
labels = ['16QAM', '64QAM', '8PSK', 'BPSK', 'CPFSK', 'GFSK', 'PAM4', 'QPSK']
modulation_map = {
    "0": "16QAM",
    "1": "64QAM",
    "2": "8PSK",
    "3": "8PSK",
    "4": "BPSK",
    "5": "CPFSK",
    "6": "8PSK",
    "7": "GFSK",
    "8": "PAM4",
    "9": "QPSK"
}
# Plot confusion matrix

def update_modulated_data():
    global modulated_data
    global time
    global df
    mod_file = scipy.io.loadmat(f'modulated_data/mod_{modulation_map[str(truth)]}.mat')
    modulated_data = mod_file['rx']
    modulated_data_re =np.real(modulated_data.flatten())
    time = np.arange(0, len(modulated_data))

    df = pd.DataFrame(dict(
     x = time,
     y = modulated_data_re
    ))

# Plot the modulated data
def plot_modulated_data():
    fig = px.line(df, x="x", y="y", title=f"Modulated signal - Truth: {modulation_map[str(truth)]}", line_shape='linear')
    fig.update_traces(line=dict(color='#009FBD'))
    fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='gray'), yaxis=dict(showgrid=True, gridcolor='gray'))
    return fig

confusion_matrix = np.zeros((len(labels), len(labels)))
iteration=0

def update_confusion_matrix():
    global confusion_matrix
    global truth
    global iteration
    for _ in range(100):
        truth = random.randint(0, len(labels)-1)
        estimated = random.randint(0, len(labels)-1)
        confusion_matrix[truth][estimated] += 1
    iteration +=1
    if iteration == 50:
        confusion_matrix = np.zeros((len(labels), len(labels)))
        iteration=0

def plot_confusion_matrix():
    fig = go.Figure(data=go.Heatmap(
        z=confusion_matrix,
        x=labels,
        y=labels,
        colorscale='Blues'
    ))
    fig.update_layout(
        title='Confusion Matrix for the Modulation Identification',
        xaxis=dict(title='Estimated Modulation'),
        yaxis=dict(title='True Modulation')
    )
    return fig

table_data = [{}]

def update_table():
    global table_data
    n= random.randint(0, 100)
    y_true = [random.randint(1, 9) for _ in range(100)]
    y_pred = [random.randint(1, 9) for _ in range(100)]
    y_pred_proba = [random.randint(1, 9) for _ in range(100)]

    # Assuming y_true are the true labels and y_pred are the predicted labels
    accuracy             = accuracy_score(y_true, y_pred)
    precision            = precision_score(y_true, y_pred, average='weighted')
    recall               = recall_score(y_true, y_pred, average='weighted')
    f1                   = f1_score(y_true, y_pred, average='weighted')
    mse                  = mean_squared_error(y_true, y_pred)
    r2                   = r2_score(y_true, y_pred)

    table_data = [
        {'column-1': 'Value' ,
         'column-2':  f' {accuracy}',
         'column-3':  f' {precision}',
         'column-4':  f' {recall}',
         'column-5':  f' {f1}',
         'column-6':  f' {mse}',
         'column-7':  f' {r2}'
         },
    ]

app.layout = html.Div([
    html.H1(" High-Performance Analog Meets AI ", style={'textAlign': 'center', 'backgroundColor': 'transparent'}),
    html.Div([
        html.Div(dcc.Graph(id='confusion-matrix'), style={'width': '45%', 'display': 'inline-block', 'margin-left': '5%'}),
        html.Div(dcc.Graph(id='modulated-data'), style={'width': '45%', 'display': 'inline-block', 'margin-right': '5%'})
    ], style={'width': '90%', 'margin-left': '5%', 'margin-bottom': '0.1%', 'backgroundColor': 'transparent', 'border': '1px solid #B7BBC3'}),
    html.Div(
    dash_table.DataTable(
        id='example-table',
        columns=[
            {'name': 'Parameter'   , 'id': 'column-1'},
            {'name': 'Accuracy'    , 'id': 'column-2'},
            {'name': 'Precision'   , 'id': 'column-3'},
            {'name': 'Recall'      , 'id': 'column-4'},
            {'name': 'F1 rate'     , 'id': 'column-5'},
            {'name': 'MSE rate'    , 'id': 'column-6'},
            {'name': 'R2 rate'     , 'id': 'column-7'}
        ],
        data=table_data,
        style_table={'width': '90%', 'margin-left': '5%'},
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': '#1E4056', 'color': 'white'},
        style_data_conditional=[
            {
                'if': {'column_id': 'column-1'},
                'backgroundColor': '#1E4056',
                'color': 'white'
            }
        ]
        )
    ),
    dcc.Interval(
     id='interval-component',
     interval=1*1000,  # in milliseconds
     n_intervals=0
    )
])
@app.callback(
    [dash.dependencies.Output('confusion-matrix', 'figure'),
     dash.dependencies.Output('modulated-data', 'figure'),
     dash.dependencies.Output('example-table', 'data')],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    update_confusion_matrix()
    update_modulated_data()
    update_table()
    return plot_confusion_matrix(), plot_modulated_data(), table_data

if __name__ == '__main__':
    app.run_server(debug=True)