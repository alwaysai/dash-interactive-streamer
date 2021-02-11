import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html 
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from flask import Flask
from flask import render_template, request, Response
import edgeiq
import cv2
import time


# edgeIQ
camera = edgeiq.WebcamVideoStream(cam=0)
obj_detect = edgeiq.ObjectDetection("alwaysai/mobilenet_ssd")
obj_detect.load(engine=edgeiq.Engine.DNN)

# Flask routes (how client sends data to server)
def gen_video_feed(camera):
    while True:
        frame = camera.read()
        frame = perform_object_detection(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Data
data = pd.DataFrame()
START_TIME = time.time()

def perform_object_detection(frame):
    frame = edgeiq.resize(frame, width=800, height=300)
    results = obj_detect.detect_objects(frame, confidence_level=.5)
    frame = edgeiq.markup_image(
            frame, results.predictions, colors=obj_detect.colors)
    frame = cv2.imencode('.jpg', frame)[1].tobytes()

    # update data for table 
    objects = {
        'timestamp': str(round((time.time() - START_TIME), 0)),
        'labels': ", ".join([p.label for p in results.predictions])
    }

    global data
    if data is None:
        data = pd.DataFrame({k: [v] for k, v in objects.items()})
    else:
        data = data.append(pd.DataFrame({k: [v] for k, v in objects.items()}))
    
    data = data.drop_duplicates()

    return frame


# Flask app
app = Flask(__name__, instance_relative_config=False)

@app.route('/video_feed')
def video_feed():
    return Response(gen_video_feed(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def home():
    return render_template("index.html")

# if using as a server, send data and process
@app.route("/event", methods=["POST"])
def event():
    body = request.json
    return Response("{'success': 'event tracked'}", status=200, mimetype='application/json')

# Dash
dash_app = dash.Dash(
    __name__,
    server=app, # associate Flask
    assets_folder="./static",
    url_base_pathname='/dash/',
    external_stylesheets=[dbc.themes.LUX]
)

dash_app.layout = dbc.Container(fluid=True, children=[
    # body
    dbc.Row([
        dbc.Col(
            # streamer content
            html.Img(
                    src="/video_feed", 
                    style={'position': 'center', 'width': 600, 'height': 350}
                )
        ),     
    ]),
    dash_table.DataTable(
        id="logs",
        data=[],
        columns=[],
        style_as_list_view=False,
        page_action="native",
        page_size= 10,
        export_format="csv",
        style_header={
            'backgroundColor': 'rgba(0,0,0,0.2)',
            'border': '1px solid white',
            'font-family': 'Nunito Sans'
        },
        style_cell={
            'backgroundColor': 'rgba(0,0,0,0.2)',
            'color': 'black',
            'text-align': 'left',
            'font-size': '14px',
            'font-family': 'Nunito Sans'
        },
        style_data={
            'border': '1px solid white'
        },
        sort_by={
            'column_id': 'timestamp',
            'direction': 'desc'
        })
    ,
    # automatically update periodically
    dcc.Interval(
        id='interval-component',
        interval=1*5000, # in milliseconds
        n_intervals=0
    )
])

# Dash callbacks
@dash_app.callback(
    output=[Output("logs", "data"), Output("logs", "columns")],
    inputs=[Input('interval-component', 'n_intervals')])
def render_log_table(n_intervals):
    df = data
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]


if __name__ == "__main__":
    camera.start()
    try:
        app.run(host='localhost', port=5001, debug=False)
    except Exception as e:
        print(e)
    finally:
        camera.stop()