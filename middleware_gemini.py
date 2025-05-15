from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyAgCgB0wGpU_c8tsm6fE3R8lkT_EcNFQFg"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def ask_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(GEMINI_URL, headers=headers, json=body)

    if response.status_code == 200:
        content = response.json()
        try:
            return content["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            return "Could not parse Gemini response"
    else:
        return f"Gemini API error: {response.status_code} - {response.text}"

@app.route("/gemini-command", methods=["POST"])
def get_command():
    data = request.json
    question = data.get("question")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    prompt = (
        f"You are a Nokia SR Linux CLI expert. "
        f"Given the user request: '{question}', respond with only the correct CLI command. "
        f"No explanation, just the command."
    )

    command = ask_gemini(prompt)
    return jsonify({
        "question": question,
        "command": command
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)

