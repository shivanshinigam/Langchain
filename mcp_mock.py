from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest/sample")
def ingest():
    data = request.json
    return {"received_rows": len(data.get("rows", []))}

if __name__ == "__main__":
    app.run(port=5001)
