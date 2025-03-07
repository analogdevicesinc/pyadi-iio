import numpy as np
import random
from dash import Dash, html, dcc, dash_table
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import scipy.io
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.metrics import roc_curve, roc_auc_score
import os
import time
import adi
import scipy.io

app = Dash(__name__, update_title=None)

# Data
labels = ['16QAM', '64QAM', '8PSK', 'BPSK', 'CPFSK', 'GFSK', 'PAM4', 'QPSK']
modulation_map = {
    "1": "16QAM",
    "2": "64QAM",
    "3": "8PSK",
    "5": "BPSK",
    "6": "CPFSK",
    "8": "GFSK",
    "9": "PAM4",
    "10": "QPSK"
}

# Plot the modulated data
def plot_modulated_data():

    estimated_labels = [modulation_map[str(label)] for label in estimated_ch1_vector]
    fig = px.histogram(
        x=probability_ch1_vector, color=estimated_labels, nbins=50,
        labels=dict(color='True Labels', x='Score')
    )
    return fig

# Plot the modulated data
def plot_modulated_data1():

    estimated_labels1 = [modulation_map[str(label)] for label in estimated_ch5_vector]
    fig = px.histogram(
        x=probability_ch5_vector, color=estimated_labels1, nbins=50,
        labels=dict(color='True Labels', x='Score')
    )
    return fig

confusion_matrix = np.zeros((len(labels), len(labels)))
confusion_matrix1 = np.zeros((len(labels), len(labels)))
iteration=0

last_timestamp = ""
last_timestamp1 = ""

estimated_ch1 = 0
estimated_ch2 = 0
estimated_ch3 = 0
estimated_ch4 = 0
estimated_ch5 = 0
estimated_ch6 = 0
estimated_ch7 = 0
estimated_ch8 = 0

file_path = '/home/analog/Workspace/holohub/build/matlab_classify_modulator/applications/matlab_classify_modulator/cpp/modulation_results.txt'
file_path1 = '/home/analog/Workspace/holohub/build/matlab_classify_modulator/applications/matlab_classify_modulator/cpp/modulation_results1.txt'

truth = 0
truth1 = 0
estimated_ch1_vector = []
estimated_ch2_vector = []
estimated_ch3_vector = []
estimated_ch4_vector = []
estimated_ch5_vector = []
estimated_ch6_vector = []
estimated_ch7_vector = []
estimated_ch8_vector = []

probability_ch1_vector = []
probability_ch2_vector = []
probability_ch3_vector = []
probability_ch4_vector = []
probability_ch5_vector = []
probability_ch6_vector = []
probability_ch7_vector = []
probability_ch8_vector = []
truth_vector = []
truth_vector1 = []

def get_timestamp(file_name):
    global last_timestamp
    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, 'r') as file:
            lines = file.readlines()
            if lines:
                timestamp = lines[0].strip()
                if timestamp > last_timestamp:
                    last_timestamp = timestamp
                    return True
    return False

def get_timestamp1(file_name):
    global last_timestamp1
    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, 'r') as file:
            lines = file.readlines()
            if lines:
                timestamp = lines[0].strip()
                if timestamp > last_timestamp1:
                    last_timestamp1 = timestamp
                    return True
    return False

def get_cnn_data():
    global truth
    global truth1

    global estimated_ch1
    global estimated_ch2
    global estimated_ch3
    global estimated_ch4
    global estimated_ch5
    global estimated_ch6
    global estimated_ch7
    global estimated_ch8

    global probability_ch1
    global probability_ch2
    global probability_ch3
    global probability_ch4
    global probability_ch5
    global probability_ch6
    global probability_ch7
    global probability_ch8

    global estimated_ch1_vector
    global estimated_ch2_vector
    global estimated_ch3_vector
    global estimated_ch4_vector
    global estimated_ch5_vector
    global estimated_ch6_vector
    global estimated_ch7_vector
    global estimated_ch8_vector

    global probability_ch1_vector
    global probability_ch2_vector
    global probability_ch3_vector
    global probability_ch4_vector
    global probability_ch5_vector
    global probability_ch6_vector
    global probability_ch7_vector
    global probability_ch8_vector

    global truth_vector
    global truth_vector1

    mod_8spk  = scipy.io.loadmat('modulated_data/mod_8PSK.mat')
    mod_16qam = scipy.io.loadmat('modulated_data/mod_16QAM.mat')
    mod_64qam = scipy.io.loadmat('modulated_data/mod_64QAM.mat')
    mod_bspk  = scipy.io.loadmat('modulated_data/mod_BPSK.mat')
    mod_cpfsk = scipy.io.loadmat('modulated_data/mod_CPFSK.mat')
    mod_gfsk  = scipy.io.loadmat('modulated_data/mod_GFSK.mat')
    mod_pam4  = scipy.io.loadmat('modulated_data/mod_PAM4.mat')
    mod_qpsk  = scipy.io.loadmat('modulated_data/mod_QPSK.mat')

    truth  = random.choice([1, 2, 3, 5, 6, 8,9,10])
    truth1 = truth
    modulation_type = modulation_map[str(truth)]
    match modulation_type:
        case "BPSK":
            data = mod_bspk['rx']
        case "QPSK":
            data = mod_qpsk['rx']
        case "8PSK":
            data = mod_8spk['rx']
        case "16QAM":
            data = mod_16qam['rx']
        case "64QAM":
            data = mod_64qam['rx']
        case "PAM4":
            data = mod_pam4['rx']
        case "GFSK":
            data = mod_gfsk['rx']
        case "CPFSK":
            data = mod_cpfsk['rx']

    data=data.flatten()
    iq_real = np.int16(np.real(data) * 2**12-1)
    iq_imag = np.int16(np.imag(data) * 2**12-1)
    iq = iq_real + 1j * iq_imag

    sdr.tx_destroy_buffer()
    sdr._tx2.tx_destroy_buffer()
    sdr.tx(iq)
    sdr._tx2.tx(iq)

    sdr1.tx_destroy_buffer()
    sdr1._tx2.tx_destroy_buffer()
    sdr1.tx(iq)
    sdr1._tx2.tx(iq)

    sdr2.tx_destroy_buffer()
    sdr2._tx2.tx_destroy_buffer()
    sdr2.tx(iq)
    sdr2._tx2.tx(iq)

    sdr3.tx_destroy_buffer()
    sdr3._tx2.tx_destroy_buffer()
    sdr3.tx(iq)
    sdr3._tx2.tx(iq)

    time.sleep(0.5)
    if get_timestamp(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            estimated_ch1 = int(lines[1].strip())
            estimated_ch2 = int(lines[2].strip())
            estimated_ch3 = int(lines[3].strip())
            estimated_ch4 = int(lines[4].strip())
            probability_ch1 = float(lines[5].strip())
            probability_ch2 = float(lines[6].strip())
            probability_ch3 = float(lines[7].strip())
            probability_ch4 = float(lines[8].strip())

        truth_vector.append(truth)
        estimated_ch1_vector.append(estimated_ch1)
        estimated_ch2_vector.append(estimated_ch2)
        estimated_ch3_vector.append(estimated_ch3)
        estimated_ch4_vector.append(estimated_ch4)

        probability_ch1_vector.append(probability_ch1)
        probability_ch2_vector.append(probability_ch2)
        probability_ch3_vector.append(probability_ch3)
        probability_ch4_vector.append(probability_ch4)

    if get_timestamp1(file_path1):

        with open(file_path1, 'r') as file:
            lines = file.readlines()
            estimated_ch5 = int(lines[1].strip())
            estimated_ch6 = int(lines[2].strip())
            estimated_ch7 = int(lines[3].strip())
            estimated_ch8 = int(lines[4].strip())
            probability_ch5 = float(lines[5].strip())
            probability_ch6 = float(lines[6].strip())
            probability_ch7 = float(lines[7].strip())
            probability_ch8 = float(lines[8].strip())
        truth_vector1.append(truth1)
        estimated_ch5_vector.append(estimated_ch5)
        estimated_ch6_vector.append(estimated_ch6)
        estimated_ch7_vector.append(estimated_ch7)
        estimated_ch8_vector.append(estimated_ch8)

        probability_ch5_vector.append(probability_ch5)
        probability_ch6_vector.append(probability_ch6)
        probability_ch7_vector.append(probability_ch7)
        probability_ch8_vector.append(probability_ch8)

    if len(estimated_ch1_vector) > 200:
        truth_vector = []
        estimated_ch1_vector = []
        estimated_ch2_vector = []
        estimated_ch3_vector = []
        estimated_ch4_vector = []
        estimated_ch5_vector = []
        estimated_ch6_vector = []
        estimated_ch7_vector = []
        estimated_ch8_vector = []
        probability_ch1_vector = []
        probability_ch2_vector = []
        probability_ch3_vector = []
        probability_ch4_vector = []
        probability_ch5_vector = []
        probability_ch6_vector = []
        probability_ch7_vector = []
        probability_ch8_vector = []

def update_confusion_matrix():
    global confusion_matrix
    global confusion_matrix1
    global iteration
    cnn_matrix_asociation = {
     1  : 0,
     2  : 1,
     3  : 2,
     5  : 3,
     6  : 4,
     8  : 5,
     9  : 6,
     10 : 7
    }

    confusion_matrix[cnn_matrix_asociation.get(truth)][cnn_matrix_asociation.get(estimated_ch1)] += 1
    confusion_matrix[cnn_matrix_asociation.get(truth)][cnn_matrix_asociation.get(estimated_ch2)] += 1
    confusion_matrix[cnn_matrix_asociation.get(truth)][cnn_matrix_asociation.get(estimated_ch3)] += 1
    confusion_matrix[cnn_matrix_asociation.get(truth)][cnn_matrix_asociation.get(estimated_ch4)] += 1

    confusion_matrix1[cnn_matrix_asociation.get(truth1)][cnn_matrix_asociation.get(estimated_ch5)] += 1
    confusion_matrix1[cnn_matrix_asociation.get(truth1)][cnn_matrix_asociation.get(estimated_ch6)] += 1
    confusion_matrix1[cnn_matrix_asociation.get(truth1)][cnn_matrix_asociation.get(estimated_ch7)] += 1
    confusion_matrix1[cnn_matrix_asociation.get(truth1)][cnn_matrix_asociation.get(estimated_ch8)] += 1
    iteration +=1
    if iteration == 200:
        confusion_matrix = np.zeros((len(labels), len(labels)))
        confusion_matrix1 = np.zeros((len(labels), len(labels)))
        iteration=0

def plot_confusion_matrix():
    fig = go.Figure(data=go.Heatmap(
        z=confusion_matrix,
        x=labels,
        y=labels,
        colorscale='Blues',
        linewidths=.5,
        annot=True
    ))
    fig.update_layout(
        xaxis=dict(title='Estimated Modulation'),
        yaxis=dict(title='True Modulation')
    )
    return fig

def plot_confusion_matrix1():
    fig = go.Figure(data=go.Heatmap(
        z=confusion_matrix1,
        x=labels,
        y=labels,
        colorscale='Blues',
        linewidths=.5,
        annot=True
    ))
    fig.update_layout(
        xaxis=dict(title='Estimated Modulation'),
        yaxis=dict(title='True Modulation')
    )
    return fig

table_data = pd.DataFrame(columns=['column-1', 'column-2', 'column-3', 'column-4', 'column-5', 'column-6'], dtype=np.float64).to_dict('records')
truth_table_data = pd.DataFrame(columns=['column-1', 'column-2', 'column-3'], dtype=pd.StringDtype()).to_dict('records')
truth_table_data1 = pd.DataFrame(columns=['column-1', 'column-2', 'column-3'], dtype=pd.StringDtype()).to_dict('records')

accuracy    = 0
precision   = 0
recall      = 0
f1          = 0
mse         = 0
r2          = 0

def update_table():
    global table_data
    global accuracy
    global precision
    global recall
    global f1
    global mse
    global r2
    y_true       = truth_vector
    y_pred       = estimated_ch1_vector
    y_pred_proba = probability_ch1_vector

    # Assuming y_true are the true labels and y_pred are the predicted labels
    if(len(y_true) > 2):
        accuracy             = accuracy_score(y_true, y_pred)
        precision            = precision_score(y_true, y_pred, average='weighted', zero_division=1)
        recall               = recall_score(y_true, y_pred, average='weighted', zero_division=1)
        f1                   = f1_score(y_true, y_pred, average='weighted')
        mse                  = mean_squared_error(y_true, y_pred)
        r2                   = r2_score(y_true, y_pred)

    table_data = [
        {'column-1':  f'{accuracy:.4f}',
         'column-2':  f'{precision:.4f}',
         'column-3':  f'{recall:.4f}',
         'column-4':  f'{f1:.4f}',
         'column-5':  f'{mse:.4f}',
         'column-6':  f'{r2:.4f}'
         },
    ]

def update_truth_table():
    global truth_table_data
    global truth_table_data1

    truth_table_data = [
        {'column-1': ' Channel 1 ', 'column-2': f' {modulation_map[str(truth)]}', 'column-3': f' {modulation_map[str(estimated_ch1)]}'},
        {'column-1': ' Channel 2 ', 'column-2': f' {modulation_map[str(truth)]}', 'column-3': f' {modulation_map[str(estimated_ch2)]}'},
        {'column-1': ' Channel 3 ', 'column-2': f' {modulation_map[str(truth)]}', 'column-3': f' {modulation_map[str(estimated_ch3)]}'},
        {'column-1': ' Channel 4 ', 'column-2': f' {modulation_map[str(truth)]}', 'column-3': f' {modulation_map[str(estimated_ch4)]}'},
    ]

    truth_table_data1 = [
        {'column-1': 'Channel 1', 'column-2': f'{modulation_map[str(truth1)]}', 'column-3': f'{modulation_map[str(estimated_ch5)]}'},
        {'column-1': 'Channel 2', 'column-2': f'{modulation_map[str(truth1)]}', 'column-3': f'{modulation_map[str(estimated_ch6)]}'},
        {'column-1': 'Channel 3', 'column-2': f'{modulation_map[str(truth1)]}', 'column-3': f'{modulation_map[str(estimated_ch7)]}'},
        {'column-1': 'Channel 4', 'column-2': f'{modulation_map[str(truth1)]}', 'column-3': f'{modulation_map[str(estimated_ch8)]}'},
    ]

app.layout = html.Div([
    html.Div([
        html.Img(src='/assets/ADI_logo.svg', style={'height': '45px', 'margin-right': '16px', 'vertical-align': 'middle'}),
        html.H1('High-Performance Analog Meets AI', style={'display': 'inline-block', 'vertical-align': 'middle', 'fontSize': '46px'})
    ], style={'width': '100%', 'text-align': 'left', 'padding': '5px', 'border-bottom': '1px solid #B7BBC3', 'backgroundColor': '#FFFFFF', 'font-family': 'Barlow', 'align-items': 'center'}),

    html.Div([
        html.H2('First ADRV9009ZU11eg', style={'text-align': 'center', 'font-family': 'Barlow','padding': '25px'}),
        html.Div([
                dcc.Graph(id='confusion-matrix', style={'width': '40%','height': '40%','display': 'inline-block'}),
                dash_table.DataTable(
                    id='truth-table',
                    columns=[
                        {'name': 'Channel'   , 'id': 'column-1'},
                        {'name': 'Truth'     , 'id': 'column-2'},
                        {'name': 'Estimated' , 'id': 'column-3'},
                    ],
                    data=truth_table_data,
                    style_cell={'textAlign': 'center', 'fontSize': '15px', 'font-family': 'Barlow','padding': '10px'},
                    style_header={'backgroundColor': '#1E4056', 'color': 'white', 'font-family': 'Barlow', 'fontSize': '15px'},
                    style_table={'width': '20%','height': '40%', 'display': 'inline-block','margin-top': '50%','vertical-align': 'middle'}
                ),
                dcc.Graph(id='modulated-data', style={'width': '40%' ,'height': '40%','display': 'inline-block'})
                ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%','height': '90%'})],
             style={'width': '98%', 'height': '55%', 'margin-left': '1%', 'backgroundColor': 'transparent', 'border-radius': '20px', 'box-shadow': '10px 10px 20px rgba(0, 0, 0, 0.2)', 'font-family': 'Barlow', 'fontSize': '20px'}),
    html.Div(
        dash_table.DataTable(
            id='example-table',
            columns=[
                {'name': 'Accuracy' , 'id': 'column-1'},
                {'name': 'Precision', 'id': 'column-2'},
                {'name': 'Recall'   , 'id': 'column-3'},
                {'name': 'F1 rate'  , 'id': 'column-4'},
                {'name': 'MSE rate' , 'id': 'column-5'},
                {'name': 'R2 rate'  , 'id': 'column-6'}
            ],
            data=table_data,
            style_table={'width': '90%', 'margin-left': '5%', 'margin-top': '2%', 'margin-bottom': '2%', 'border-radius': '50px', 'box-shadow': '10px 10px 20px rgba(0, 0, 0, 0.2)', 'font-family': 'Barlow'},
            style_cell={'textAlign': 'center', 'fontSize': '20px', 'font-family': 'Barlow'},
            style_header={'backgroundColor': '#1E4056', 'color': 'white', 'font-family': 'Barlow', 'fontSize': '20px','font-family': 'Barlow'}
        )
    ),
    html.Div([
        html.H2('Second ADRV9009ZU11eg', style={'text-align': 'center', 'font-family': 'Barlow','padding': '25px'}),
        html.Div([
                dcc.Graph(id='confusion-matrix1', style={'width': '40%','height': '40%','display': 'inline-block'}),
                dash_table.DataTable(
                    id='truth-table1',
                    columns=[
                        {'name': 'Channel   '     , 'id': 'column-1'},
                        {'name': 'Truth     '     , 'id': 'column-2'},
                        {'name': 'Estimated '     , 'id': 'column-3'},
                    ],
                    data=truth_table_data1,
                    style_cell={'textAlign': 'center', 'fontSize': '15px', 'font-family': 'Barlow','padding': '10px'},
                    style_header={'backgroundColor': '#1E4056', 'color': 'white', 'font-family': 'Barlow', 'fontSize': '15px'},
                    style_table={'width': '100%', 'height': '40%','display': 'inline-block','margin-top': '50%','vertical-align': 'middle','font-family': 'Barlow'}
                ),
                dcc.Graph(id='modulated-data1', style={'width': '40%','height': '40%','display': 'inline-block'})
                ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%','height': '90%'})],
             style={'width': '98%', 'height': '55%', 'margin-left': '1%', 'backgroundColor': 'transparent', 'border-radius': '20px', 'box-shadow': '10px 10px 20px rgba(0, 0, 0, 0.2)', 'font-family': 'Barlow', 'fontSize': '20px'}),
    dcc.Interval(
        id='interval-component',
        interval=3*1000,  # in milliseconds
        n_intervals=0
    )
], style={'font-family': 'Barlow'})

@app.callback(
    [dash.dependencies.Output('confusion-matrix', 'figure'),
     dash.dependencies.Output('modulated-data', 'figure'),
     dash.dependencies.Output('example-table', 'data'),
     dash.dependencies.Output('truth-table', 'data'),
    dash.dependencies.Output('truth-table1', 'data'),
     dash.dependencies.Output('confusion-matrix1', 'figure'),
     dash.dependencies.Output('modulated-data1', 'figure')],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    get_cnn_data()
    update_confusion_matrix()
    update_table()
    update_truth_table()
    return plot_confusion_matrix(), plot_modulated_data(), table_data, truth_table_data , truth_table_data1, plot_confusion_matrix1(), plot_modulated_data1()

if __name__ == '__main__':

    # Code to be executed just once
    sdr  = adi.adrv9002(uri="ip:10.48.65.222")
    sdr.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

    sdr.tx0_port_en = "spi"
    sdr.tx1_port_en = "spi"
    sdr.tx_ensm_mode_chan0 = "rf_enabled"
    sdr.tx_ensm_mode_chan1 = "rf_enabled"
    sdr.tx_cyclic_buffer = True
    sdr.tx2_cyclic_buffer = True
    sdr.tx0_lo = 2400000000
    sdr.tx1_lo = 2400000000
    sdr.tx_hardwaregain_chan0 = -10
    sdr.tx_hardwaregain_chan1 = -10


    sdr1 = adi.adrv9002(uri="ip:10.48.65.187")
    sdr1.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

    sdr1.tx0_port_en = "spi"
    sdr1.tx1_port_en = "spi"
    sdr1.tx_ensm_mode_chan0 = "rf_enabled"
    sdr1.tx_ensm_mode_chan1 = "rf_enabled"
    sdr1.tx_cyclic_buffer = True
    sdr1.tx2_cyclic_buffer = True
    sdr1.tx0_lo = 2400000000
    sdr1.tx1_lo = 2400000000
    sdr1.tx_hardwaregain_chan0 = -10
    sdr1.tx_hardwaregain_chan1 = -10

    sdr2 = adi.adrv9002(uri="ip:10.48.65.226")
    sdr2.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

    sdr2.tx0_port_en = "spi"
    sdr2.tx1_port_en = "spi"
    sdr2.tx_ensm_mode_chan0 = "rf_enabled"
    sdr2.tx_ensm_mode_chan1 = "rf_enabled"
    sdr2.tx_cyclic_buffer = True
    sdr2.tx2_cyclic_buffer = True
    sdr2.tx0_lo = 2400000000
    sdr2.tx1_lo = 2400000000
    sdr2.tx_hardwaregain_chan0 = -10
    sdr2.tx_hardwaregain_chan1 = -10


    sdr3 = adi.adrv9002(uri="ip:10.48.65.203")
    sdr3.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

    sdr3.tx0_port_en = "spi"
    sdr3.tx1_port_en = "spi"
    sdr3.tx_ensm_mode_chan0 = "rf_enabled"
    sdr3.tx_ensm_mode_chan1 = "rf_enabled"
    sdr3.tx_cyclic_buffer = True
    sdr3.tx2_cyclic_buffer = True
    sdr3.tx0_lo = 2400000000
    sdr3.tx1_lo = 2400000000
    sdr3.tx_hardwaregain_chan0 = -10
    sdr3.tx_hardwaregain_chan1 = -10

    sdr.tx0_en  = 1
    sdr.tx1_en  = 1
    sdr1.tx0_en = 1
    sdr1.tx1_en = 1
    sdr2.tx0_en = 1
    sdr2.tx1_en = 1
    sdr3.tx0_en = 1
    sdr3.tx1_en = 1








    app.run_server(debug=True)
