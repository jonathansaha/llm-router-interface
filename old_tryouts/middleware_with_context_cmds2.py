from flask import Flask, request, jsonify
import paramiko
import requests
import logging

app = Flask(__name__)

# Load CLI documentation from cleaned_cmds.txt
def load_cli_context(file_path='cleaned_cmds.txt'):
    with open(file_path, 'r') as file:
        return file.read()

CLI_CONTEXT = load_cli_context()[:3000]  # Adjust the limit as needed (token limit)

# Your Ollama/Open WebUI LLM endpoint
DEESEEK_API_URL = "http://172.18.0.2:11434/api/generate"
DEESEEK_MODEL = "deepseek-r1:7b"

# SSH config (map hostnames to IPs)
ROUTER_HOSTS = {
    "node1": {"host": "172.30.0.3", "username": "admin", "password": "NokiaSrl1!"},
    "node2": {"host": "172.30.0.2", "username": "admin", "password": "NokiaSrl1!"},
}

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
    try:
        response = requests.post(DEESEEK_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error with DeepSeek API request: {e}")
        return ""

def execute_ssh_command(router_name, command):
    router = ROUTER_HOSTS.get(router_name)
    if not router:
        return "Unknown router"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(router["host"], username=router["username"], password=router["password"])

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        ssh.close()

        if not output:
            return "No output from command execution"
        return output
    except paramiko.SSHException as e:
        logging.error(f"SSH error for {router_name}: {e}")
        return f"Error connecting to {router_name}: {e}"

@app.route("/query", methods=["POST"])
def query_router():
    data = request.get_json()
    router = data.get("router")
    question = data.get("question")

    if not router or not question:
        return jsonify({"error": "Missing 'router' or 'question'"}), 400

    prompt = generate_prompt(question)
    logging.debug(f"Generated prompt: {prompt}")

    # Call DeepSeek API to get the command
    command = ask_deepseek(prompt)
    if not command:
        return jsonify({"error": "Failed to generate a valid command from DeepSeek"}), 500

    # Clean the command from any unwanted newlines
    command = command.replace("\n", " ").strip()
    logging.debug(f"Command from DeepSeek: {command}")

    # Execute the command via SSH on the router
    output = execute_ssh_command(router, command)

    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

