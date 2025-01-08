from flask import Flask, jsonify, send_from_directory
from lib import financialmodelingprep as api
import os

app = Flask(__name__, static_folder='static')

@app.route("/api/etf_holder/<string:etf>", methods=["GET"])
def get_etf_holder(etf):
    try:
        res = api.etf_holder(etf)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search/<string:query>", methods=["GET"])
def search(query):
    try:
        res = api.search(query)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    """Serve static files for non-API routes."""
    if not os.path.exists(os.path.join(app.static_folder, path)):
        path = "index.html"  # Default to index.html if file not found
    return send_from_directory(app.static_folder, path)

@app.route("/", methods=["GET"])
def serve_index():
    """Serve the default index.html for the root route."""
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
