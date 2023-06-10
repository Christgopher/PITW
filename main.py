from functions import map_master
from flask import Flask, render_template_string
import folium

app = Flask(__name__)

@app.route("/")
def fullscreen():
    """Simple example of a fullscreen map."""
    m = map_master()
    return m.get_root().render()

if __name__ == "__main__":
    app.run(debug=True)