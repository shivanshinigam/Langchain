# mcp_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/ingest/sample", methods=["POST"])
def ingest_sample():
    # Simulate storing and returning a simple acknowledgement
    payload = request.get_json(force=True)
    rows = payload.get("rows", [])
    # Return count and a fake job id
    return jsonify({"status": "ok", "received_rows": len(rows), "job_id": "job_12345"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    print("Starting MCP mock server on http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5000, debug=False)


