import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from flask import Flask
from flask import render_template, Response

import pandas as pd

import edgeiq
import cv2
import time

# edgeIQ
camera = edgeiq.WebcamVideoStream(cam=0)
obj_detect = edgeiq.ObjectDetection("alwaysai/ssd_mobilenet_v1_coco_2018_01_28")
obj_detect.load(engine=edgeiq.Engine.DNN)

# Data
data = pd.DataFrame()
START_TIME = time.time()


# functions for rendering frame and performing object detection
def gen_video_feed():
    while True:
        frame = camera.read()
        if frame is not None:
            frame = perform_object_detection(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


def perform_object_detection(frame):
    """Perform object detction on an image, update
    the table data, and returns a string.

    Args:
        frame (numpy array): The frame from the camera stream.

    Returns:
        string: The string representation of the image
    """
    if frame is not None:
        results = obj_detect.detect_objects(frame, confidence_level=.5)
        frame = edgeiq.markup_image(
                frame, results.predictions, colors=obj_detect.colors)
        frame = edgeiq.resize(frame, width=800, height=300)
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


# Flask routes (add as needed)
@app.route('/video_feed')
def video_feed():
    return Response(gen_video_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/")
def home():
    return render_template("index.html")


# Dash Setup
dash_app = dash.Dash(
    __name__,
    server=app,  # associate Flask
    assets_folder="./static",
    url_base_pathname='/dash/',
    external_stylesheets=[dbc.themes.LUX]
)

# Dash Layout
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
        page_size=10,
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
        }),
    # automatically update periodically
    dcc.Interval(
        id='interval-component',
        interval=1*5000,  # in milliseconds
        n_intervals=0
    )
])


# Dash Callbacks
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