import requests
from flask import Flask, request, jsonify
import paramiko

app = Flask(__name__)

# SSH credentials (update these for your environment)
ROUTER_CREDENTIALS = {
    "node1": {"host": "172.30.0.3", "username": "admin", "password": "NokiaSrl1!"},
    "node2": {"host": "172.30.0.2", "username": "admin", "password": "NokiaSrl1!"},
}

# Correct DeepSeek API URL based on your setup
DEEPSEEK_API_URL = "http://172.18.0.2:11434/api/generate"
DEEPSEEK_MODEL = "deepseek-r1:7b"

def get_deepseek_command(question):
    prompt = (
        f"You are a Nokia SR Linux assistant. "
        f"Only return the exact CLI command to run for this user question: '{question}'. "
        f"Do not explain, just the CLI command."
    )

    payload = {
        "model": DEEPSEEK_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            print("DeepSeek API error:", response.text)
            return None
    except Exception as e:
        print("Failed to connect to DeepSeek:", str(e))
        return None

def ssh_and_run_command(host, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password, look_for_keys=False)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return "", str(e)

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.json
    question = data.get("question")
    router = data.get("router")

    if not router or not question:
        return jsonify({"error": "Missing router or question"}), 400

    command = get_deepseek_command(question)
    if not command:
        return jsonify({"error": "Failed to get command from DeepSeek"}), 500

    creds = ROUTER_CREDENTIALS.get(router)
    if not creds:
        return jsonify({"error": f"Unknown router {router}"}), 404

    output, error = ssh_and_run_command(
        creds["host"], creds["username"], creds["password"], command
    )

    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output,
        "error": error
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

