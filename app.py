from functions import map_master, data_master
from flask import Flask, render_template
import pandas 

app = Flask(__name__)

@app.route("/")
def fullscreen():
    """Simple example of a fullscreen map."""
    list = map_master()

    m = list[0]
    data = list[1]
    data_master(data).to_html('templates/table.html')
    m.save('templates/map.html')

    return render_template('index.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/table')
def table():
    return render_template('table.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')