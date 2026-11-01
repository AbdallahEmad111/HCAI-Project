import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from google import genai

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL})


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please send a non-empty 'message'."}), 400
    try:
        response = client.models.generate_content(model=MODEL, contents=message)
        return jsonify({"reply": response.text})
    except Exception as e:
        app.logger.error("Gemini call failed: %s", e)
        return jsonify({"error": "The model is unavailable right now. Please try again."}), 502


if __name__ == "__main__":
    app.run(debug=True)