# Dash Interactive Streamer
This application provides a base for an interactive streamer using Plotly Dash (https://dash.plotly.com). This app includes a video stream, which depicts object detection results, as well as a table that updates every 5 seconds with object detection results. You can create more complex applications by adding components.

## Setup
This app requires an alwaysAI account. Head to the [Sign up page](https://alwaysai.co/register) if you don't have an account yet. Follow the instructions to install the alwaysAI toolchain on your development machine.

Next, login to the website and navigate to your Dashboard. Create an empty project (choosing to start from scratch) to be used with this app. When you clone this repo, you can run `aai app configure` within the repo directory and your new project will appear in the list. Note, this application has been tested on Windows 10 and MacOS (using `local` option on configuration). This application will automatically detect a web camera.

## Usage
After you've configured your project, run `aai app install`, and `aai app start`. Navigate to `localhost:5001/dash/` (note that the regular Flask server's video stream will run on `localhost:5001/video`)

## Troubleshooting
alwaysAI Documentation: https://alwaysai.co  
Discord Community at: https://discord.gg/R2uM36U