from bottle import Bottle, jinja2_template as template, jinja2_view as view, redirect, TEMPLATE_PATH, static_file, get, request
from .logic import logic
import yaml
from app.params import OUTPUT_DIR
import os.path as op
import jsonpickle
web_server = Bottle()
TEMPLATE_PATH.insert(0, 'templates')
import plotly
import plotly.graph_objs as go
import pandas as pd
import json
import numpy as np
from app.Steps import Step

# CAREFUL: Do NOT perform any computation-related tasks inside these methods, nor inside functions called from them!
# Otherwise your app does not respond to calls made by the FeatureCloud system quickly enough
# Use the threaded loop in the app_flow function inside the file logic.py instead

@web_server.route('/static/<filepath:path>')
def server_static(filepath):
    print('Access static')
    return static_file(filepath, root='./static')

@web_server.route('/', methods=['GET'])
def root():
    """
    """
    if logic.web_status == 'setup_via_user_interface':
        return template('start_coordinator.html', is_coordinator=logic.coordinator)
    elif logic.web_status == 'final':
        return redirect('/shutdown')
    else:
        print('Default')
        return template('loading.html')

def create_plot():


    N = 40
    x = np.linspace(0, 1, N)
    y = np.random.randn(N)
    df = pd.DataFrame({'x': x, 'y': y}) # creating a sample dataframe


    data = [
        go.Bar(
            x=df['x'], # assign x as the dataframe column 'x'
            y=df['y']
        )
    ]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

@web_server.route('/setup', methods=['GET'])
def setup():
    if logic.web_status == 'setup_via_user_interface':
        try:
            return template("start_coordinator.html", title='Coordinator', is_coordinator=logic.coordinator)
        except:
            return template("init.html")
    else:
        return template('loading.html')

@web_server.route('/result', methods=['GET'])
def result():
    print("VISUALIZE results")
    try:
        if logic.svd.pca.projections is None:
            return template('loading.html')

        print("[WEB] visualise results")

        x = logic.svd.pca.projections[:, 0:1].flatten().tolist()
        y = logic.svd.pca.projections[:, 1:2].flatten().tolist()
        data = [
            go.Scatter(
                mode='markers',
                x=x,  # assign x as the dataframe column 'x'
                y=y
            )
        ]

        graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

        return template("result.html", plot = graphJSON)
    except:
        return template("result.html")

def color_picker(clients):
    colors = ['#d73027', '#f46d43', '#fdae61', '#fee090', '#ffffbf', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4']
    i = 0
    j = 0
    client_color = []
    c1 = clients[i]
    while i < len(clients):
        if clients[i] != c1:
            c1 = clients[i]
            if j < len(colors):
                j = j+1
            else:
                j = 0
        client_color.append(colors[j])
        i = i+1
    return client_color

def button_enabled():
    if logic.svd.outlier_removal == 'no_removal':
        enabled = False
    elif logic.svd.outlier_removal == 'local_outlier_removal':
        enabled = True
    elif logic.svd.outlier_removal == 'global_outlier_removal' and logic.coordinator:
        enabled = True
    else:
        enabled = False
    return enabled


@web_server.route('/shutdown', method='POST')
def shutdown():
    print("[WEB] Outliers selected")
    print(request.json)
    selected = request.json['selected']
    logic.svd.outliers = logic.svd.outliers + selected
    # advance the loop
    logic.step = Step.SAVE_OUTLIERS
    logic.svd.step_queue = logic.svd.step_queue + [Step.FINALIZE]
    return template('loading.html')

@web_server.route('/run', method='POST')
def run():
    parameter_list = {}
    parameter_list['input'] = {}
    parameter_list['input']['data'] = request.forms.get('file')
    parameter_list['output']={}
    parameter_list['output']['eigenvalues'] = 'eigenvalues.tsv'
    parameter_list['output']['left_eigenvectors'] = 'left_eigenvectors.tsv'
    parameter_list['output']['right_eigenvectors'] = 'right_eigenvectors.tsv'
    parameter_list['output']['projections'] = 'projections.tsv'
    parameter_list['output']['scaled_data'] = 'scaled_data.tsv'

    parameter_list['algorithm'] = {}
    parameter_list['algorithm']['pcs'] = int(request.forms.get('pcs'))
    parameter_list['algorithm']['algorithm'] = request.forms.get('algorithm')
    parameter_list['algorithm']['qr'] = 'centralised'
    parameter_list['algorithm']['max_iterations'] = int(request.forms.get('max_iterations'))
    parameter_list['algorithm']['epsilon'] = float(request.forms.get('epsilon'))

    parameter_list['settings'] = {}
    parameter_list['settings']['rownames'] = bool(request.forms.get('rownames'))
    parameter_list['settings']['colnames'] = bool(request.forms.get('colnames'))
    parameter_list['settings']['delimiter'] = request.forms.get('sep')

    parameter_list['scaling'] = {}
    parameter_list['scaling']['center'] = request.forms.get('center')
    parameter_list['scaling']['scale_variance'] = request.forms.get('scale_variance')
    parameter_list['scaling']['transform'] = request.forms.get('transform')

    parameter_list['privacy'] = {}
    parameter_list['privacy']['allow_rerun'] = bool(request.forms.get('allow_rerun'))
    parameter_list['privacy']['allow_transmission'] = bool(request.forms.get('transmit_projections'))

    parameter_list['privacy']['outlier_removal'] = request.forms.get('outlierremoval')
    parameter_list['privacy']['encryption'] = False
    param_obj = {}
    param_obj['fc_pca'] = parameter_list
    with open(op.join(OUTPUT_DIR, 'config.yaml'), 'w') as handle:
        yaml.safe_dump(param_obj, handle)
    return template("loading.html")

#
@web_server.route('/loading', methods=['GET'])
def loading():
    return template("loading.html")

# @web_server.route('/shutdown')
# def shutdown():
#     is_coordinator=rget('is_coordinator')
#     return template("shutdown.html", is_coordinator=is_coordinator)
#
# @web_server.route('/shutdown_application', methods=['POST'])
# def shutdown_application():
#     tasks.enqueue(api_shutdown_application)
#     return template("shutdown.html", shutdown_triggered=True)

@web_server.route('/help')
def help():
    return template("help.html")

@web_server.route('/about')
def about():
    return template("about.html")