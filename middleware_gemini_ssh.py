from flask import Flask, request, jsonify
import requests
import paramiko

app = Flask(__name__)

# === CONFIG ===
GEMINI_API_KEY = "AIzaSzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzEcNFQFg"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

ROUTERS = {
    "node1": {
        "host": "172.30.0.3",  # change this to your container IP
        "port": 22,
        "username": "admin",
        "password": "NokiaSrl1!"
    }
}

# === GEMINI COMMAND ===
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
            return "ERROR: Failed to parse Gemini response"
    else:
        return f"ERROR: Gemini API - {response.status_code}"

# === SSH EXECUTION ===
def ssh_execute(host, port, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output.strip() if output else error.strip()
    except Exception as e:
        return f"SSH error: {str(e)}"

# === FLASK ROUTE ===
@app.route("/gemini-router", methods=["POST"])
def handle_query():
    data = request.json
    question = data.get("question")
    router = data.get("router")

    if not question or not router:
        return jsonify({"error": "Missing question or router"}), 400

    router_info = ROUTERS.get(router)
    if not router_info:
        return jsonify({"error": f"Unknown router '{router}'"}), 400

    # Prompt for Gemini
    prompt = (
        f"You are a Nokia SR Linux CLI expert. "
        f"Given the user request: '{question}', respond with only the exact CLI command, no explanation."
    )
    command = ask_gemini(prompt)

    if command.startswith("ERROR"):
        return jsonify({
            "router": router,
            "question": question,
            "error": command
        })

    output = ssh_execute(
        host=router_info["host"],
        port=router_info["port"],
        username=router_info["username"],
        password=router_info["password"],
        command=command
    )

    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

