from bottle import Bottle, jinja2_template as template, redirect, TEMPLATE_PATH, static_file, get, request
from .logic import logic
import yaml
from app.params import OUTPUT_DIR
import os.path as op

web_server = Bottle()
TEMPLATE_PATH.insert(0, 'templates')



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
    elif logic.web_status == 'setup' or logic.web_status == 'local_outlier_removal' or logic.web_status == 'global_outlier_removal':
        return redirect("/result")
    elif logic.web_status == 'final':
        return redirect('/shutdown')
    else:
        print('Default')
        return template('loading.html')



@web_server.route('/setup', methods=['GET'])
def setup():
    print("Set up web view")
    if logic.web_status == 'start' or logic.web_status == 'init_algorithm':
        try:
            return template("start_coordinator.html", title='Coordinator', is_coordinator=logic.coordinator)
        except:
            return template("init.html")
    else:
        return template('loading.html')


# @web_server.route('/result', methods=['GET'])
# def result():
#     print("VISUALIZE results")
#     try:
#         projections = rget('projections')
#         print("[WEB] visualise results")
#
#         x = projections[:, 0:1].flatten().tolist()
#         print(x)
#         y = projections[:, 1:2].flatten().tolist()
#         print(y)
#         if rexists('client_indices_as_vector'):
#             colors = rget('client_indices_as_vector')
#             colors = color_picker(colors)
#         else:
#             colors = ['1']*len(y)
#             colors = color_picker(colors)
#         point_ids = rget('unique_projection_ids')
#         calculate_button_enabled = button_enabled()
#         return template("result.html", x={'x': x }, y={'y': y }, color={'color':colors}, point_ids={'point_ids': point_ids},
#                                is_coordinator =rget('is_coordinator'), pcs=rget("pcs"),
#                                allow_rerun={'allow_rerun': calculate_button_enabled})
#     except:
#         return template("result.html")
#
# def color_picker(clients):
#     colors = ['#d73027', '#f46d43', '#fdae61', '#fee090', '#ffffbf', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4']
#     i = 0
#     j = 0
#     client_color = []
#     c1 = clients[i]
#     while i < len(clients):
#         if clients[i] != c1:
#             c1 = clients[i]
#             if j < len(colors):
#                 j = j+1
#             else:
#                 j = 0
#         client_color.append(colors[j])
#         i = i+1
#     return client_color
#
# def button_enabled():
#     if rget('outlier_removal') == 'no_removal':
#         enabled = False
#     elif rget('logic.web_status') == 'local_outlier_removal':
#         enabled= True
#     elif rget('logic.web_status') == 'global_outlier_removal' and rget('is_coordinator'):
#         enabled = True
#     else:
#         enabled = False
#     return enabled
#
#
# @web_server.route('/rerun', methods=['POST'])
# def rerun():
#     print("[WEB] Outliers selected")
#     selected = request.json['selected']
#     print(selected)
#     if rexists('outlier'):
#         rset('outlier', rget('outlier') + selected)
#     else:
#         rset('outlier', selected)
#     tasks.enqueue(continue_after_user_interaction)
#     return template('loading.html')
#
#
# @web_server.route('/rerun_client', methods=['GET'])
# def rerun_client():
#     if rexists('rerun'):
#         return jsonify(rerun=rget('rerun'))
#     else:
#         return jsonify(rerun=False)
#
#
# @web_server.route('/redirect_visualize', methods=['GET'])
# def redirect_visualize():
#     print('trying to redirect')
#     if rget('finished'):
#         return jsonify(redir=True)
#     else:
#         return jsonify(redir=False)
#
#
# def set_boolean(name):
#     if request.form.get(name) is not None:
#         rset(name, True)
#     else:
#         rset(name, False)
#
# def store_parameters_in_redis():
#     # Number of principal components
#     rset('pcs', request.form.get('pcs'))
#
#     # Boolean values from form , if checkbox unticked,
#     set_boolean('allow_rerun')
#     set_boolean('transmit_projections')
#
#     # String for 'global' / 'local'  outlier removal
#     rset('outlier_removal', request.form.get('outlierremoval'))
#
#
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