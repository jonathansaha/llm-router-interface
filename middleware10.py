from flask import Flask, request, jsonify
import paramiko
import requests
import logging
import re

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Load CLI documentation from cleaned_cmds.txt
def load_cli_context(file_path='formatted_cli_commands.txt'):
    with open(file_path, 'r') as file:
        return file.read()

CLI_CONTEXT = load_cli_context()[:30000]  # Adjust the limit as needed

# Gemini API config
GEMINI_API_KEY = "AIzazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzREzgAA4"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

ROUTER_HOSTS = {
    "node1": {"host": "172.30.0.3", "username": "admin", "password": "NokiaSrl1!"},
    "node2": {"host": "172.30.0.2", "username": "admin", "password": "NokiaSrl1!"},
}

def generate_prompt(question):
    return f"""
You are a Nokia SR Linux CLI assistant.

Your task: Respond ONLY with the exact CLI command needed to answer the user's question.
Do not include explanations, markdown, or any extra text.
Return only the CLI command inside double quotes, like this: "show interface"
Whatever command you give will be forwarded to a router, so it's important you only respond with the CLI command.

Here is part of the official CLI command reference for context:
{CLI_CONTEXT}

User question: {question}
Command:
"""

def clean_command_response(response_text):
    """Extract CLI command from double quotes"""
    match = re.search(r'"([^"]+)"', response_text)
    if match:
        return match.group(1).strip()
    return ""

def ask_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if candidates:
            raw_text = candidates[0]["content"]["parts"][0]["text"]
            logging.debug(f"Gemini raw response: {raw_text}")
            command = clean_command_response(raw_text)
            logging.debug(f"Extracted CLI command: {command}")
            return command
        else:
            logging.warning("No candidates returned from Gemini.")
            return ""
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling Gemini API: {e}")
        return ""

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
    command = ask_gemini(prompt)

    if not command:
        return jsonify({"error": "Failed to generate a valid command"}), 500

    output = execute_ssh_command(router, command)

    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

