from flask import Flask, jsonify, send_from_directory, request, Response, stream_with_context
import time
import os
from lib import terminal
from lib.ticker import Ticker

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

def generate_chart_stream(path_chart, timeout=120, check_interval=0.5):
    elapsed_time = 0

    # Wait until the chart is ready or timeout
    while elapsed_time < timeout:
        if os.path.exists(path_chart):
            with open(path_chart, 'rb') as f:
                yield f.read()  # Stream the file content
            return

        time.sleep(check_interval)
        elapsed_time += check_interval

    # If timeout, yield an empty PNG or error imagehel
    yield b''

@app.route("/api/charts/<chart_name>/<symbol>", methods=["GET"])
def get_chart(symbol, chart_name):
    ticker = Ticker.get(symbol)
    if not ticker:
        return jsonify(f"Invalid symbol: {symbol}"), 400

    path_chart = ticker.get_chart(chart_name)
    if not path_chart:
        return jsonify(f"Chart path not found for {symbol}"), 404

    # Stream the response with proper headers
    return Response(
        stream_with_context(generate_chart_stream(path_chart)),
        mimetype='image/png',
        headers={
            "Cache-Control": "public, max-age=604800",
            "Transfer-Encoding": "chunked",
            "Content-Type": "image/png"
        }
    )

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
    app.run(debug=True,  host="0.0.0.0", port=5000, use_reloader=False, threaded=True)
