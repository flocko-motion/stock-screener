from flask import Flask, jsonify, send_from_directory, request
import os
from lib import terminal

app = Flask(__name__, static_folder='static')

@app.route("/api/terminal", methods=["POST"])
def query_terminal():
    try:
        variables = terminal.Variables()
        persistence = terminal.Persistence()
        cmd = request.data.decode('utf-8')
        res = terminal.shell(cmd, variables, persistence)
        if res is not None:
            if isinstance(res, terminal.JsonSerializable):
                return jsonify(res.to_dict()), 200
            return jsonify(res), 200
        else:
            return jsonify("[no result]"), 200
    except Exception as e:
        return jsonify(f"{type(e).__name__}: {e}"), 500

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    """Serve static files for non-API routes."""
    if not os.path.exists(os.path.join(app.static_folder, path)):
        path = "index.html"  # Default to index.html if file not found
    return send_from_directory(app.static_folder, path)

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True,  host="0.0.0.0", port=5000, use_reloader=False)
