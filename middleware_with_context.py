from flask import Flask, request, jsonify
import paramiko
import requests

app = Flask(__name__)

# Load CLI documentation once
from pdf_utils import extract_text_from_pdfs
CLI_CONTEXT = extract_text_from_pdfs()[:3000]  # adjust limit if needed
# Use only first ~3000 chars for token limit

# Your Ollama/Open WebUI LLM endpoint
DEESEEK_API_URL = "http://localhost:11434/api/generate"
DEESEEK_MODEL = "deepseek-r1:7b"

# SSH config (you can later map hostnames to IPs from a config file)
ROUTER_HOSTS = {
    "node1": {"host": "172.30.0.3", "username": "admin", "password": "NokiaSrl1!"},
    "node2": {"host": "172.30.0.2", "username": "admin", "password": "NokiaSrl1!"},
}

def generate_prompt(question):
    return f"""
You are a Nokia SR Linux CLI assistant.

Here is part of the official CLI command reference:
{CLI_CONTEXT}

Now answer this user request by returning the exact CLI command only.
User request: '{question}'
CLI Command:
"""

def ask_deepseek(prompt):
    payload = {
        "model": DEESEEK_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(DEESEEK_API_URL, json=payload)
    return response.json()["response"].strip()

def execute_ssh_command(router_name, command):
    router = ROUTER_HOSTS.get(router_name)
    if not router:
        return "Unknown router"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router["host"], username=router["username"], password=router["password"])

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode() + stderr.read().decode()
    ssh.close()
    return output

@app.route("/query", methods=["POST"])
def query_router():
    data = request.get_json()
    router = data.get("router")
    question = data.get("question")

    if not router or not question:
        return jsonify({"error": "Missing 'router' or 'question'"}), 400

    prompt = generate_prompt(question)
    command = ask_deepseek(prompt)
    output = execute_ssh_command(router, command)

    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

