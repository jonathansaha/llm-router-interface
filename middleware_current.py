from flask import Flask, request, jsonify
import paramiko
import requests
import logging
import re
import os
from flask_cors import CORS # Import CORS

app = Flask(__name__)
CORS(app) # Enable CORS for all routes (for development)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Changed to INFO for clearer console output

# Load CLI documentation from cleaned_cmds.txt
def load_cli_context(file_path='formatted_cli_commands.txt'):
    logging.info(f"Attempting to load CLI context from {file_path}")
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            logging.info(f"CLI context loaded successfully from {file_path}")
            return content
    except FileNotFoundError:
        logging.error(f"CLI context file not found: {file_path}")
        return ""
    except Exception as e:
        logging.error(f"Error loading CLI context from {file_path}: {e}")
        return ""

CLI_CONTEXT = load_cli_context()[:100000] # Adjust the limit as needed
if not CLI_CONTEXT:
    logging.critical("CLI Context is empty! AI might not function correctly.")


# Function to load API configuration from a file
def load_api_config(file_path='api.key'):
    logging.info(f"Attempting to load API config from {file_path}")
    config = {}
    if not os.path.exists(file_path):
        logging.error(f"API config file not found: {file_path}")
        return config
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                    else:
                        logging.warning(f"Skipping malformed line in api.key (no '=' found): {line}")
        logging.info(f"API config loaded successfully from {file_path}")
    except Exception as e:
        logging.error(f"Error loading API config from {file_path}: {e}")
    return config

API_CONFIG = load_api_config()

# Gemini API config
GEMINI_API_KEY = API_CONFIG.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = API_CONFIG.get("GEMINI_API_URL", "")
GEMINI_API_URL = f"{GEMINI_BASE_URL}?key={GEMINI_API_KEY}" if GEMINI_BASE_URL and GEMINI_API_KEY else ""

if not GEMINI_API_KEY:
    logging.critical("GEMINI_API_KEY is not configured. API calls will fail.")
if not GEMINI_API_URL:
    logging.critical("GEMINI_API_URL is not fully configured. API calls will fail.")

# Function to load router hosts from a file
def load_router_hosts(file_path='devices.list'):
    logging.info(f"Attempting to load router hosts from {file_path}")
    router_hosts = {}
    if not os.path.exists(file_path):
        logging.error(f"Devices list file not found: {file_path}")
        return router_hosts
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) == 4:
                        name, host, username, password = parts
                        router_hosts[name] = {"host": host, "username": username, "password": password}
                    else:
                        logging.warning(f"Skipping malformed line in devices.list: {line}")
        logging.info(f"Router hosts loaded successfully from {file_path}. Loaded {len(router_hosts)} devices.")
    except Exception as e:
        logging.error(f"Error loading router hosts from {file_path}: {e}")
    return router_hosts

ROUTER_HOSTS = load_router_hosts()
if not ROUTER_HOSTS:
    logging.warning("No routers loaded from devices.list. SSH commands will fail.")


def generate_prompt(question):
    logging.debug(f"Generating prompt for question: {question}")
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
    logging.info("Sending request to LLM (Gemini API)...")
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

    if not GEMINI_API_KEY:
        logging.error("GEMINI_API_KEY is not configured. Cannot send request to Gemini.")
        return ""
    if not GEMINI_API_URL:
        logging.error("GEMINI_API_URL is not configured. Cannot send request to Gemini.")
        return ""

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30) # Added timeout
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if candidates:
            raw_text = candidates[0]["content"]["parts"][0]["text"]
            logging.info("LLM replied successfully.")
            logging.debug(f"Gemini raw response: {raw_text}")
            command = clean_command_response(raw_text)
            logging.debug(f"Extracted CLI command: {command}")
            return command
        else:
            logging.warning("No candidates returned from Gemini.")
            return ""
    except requests.exceptions.Timeout:
        logging.error("Gemini API request timed out.")
        return ""
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling Gemini API: {e}")
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred during Gemini API call: {e}")
        return ""

def execute_ssh_command(router_name, command):
    logging.info(f"Attempting to execute command on router: {router_name}")
    router = ROUTER_HOSTS.get(router_name)
    if not router:
        logging.error(f"Router '{router_name}' not found in ROUTER_HOSTS. Cannot execute SSH command.")
        return "Unknown router or router not configured"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(router["host"], username=router["username"], password=router["password"], timeout=10) # Added timeout
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        ssh.close()
        logging.info(f"Command executed successfully on {router_name}.")
        return output
    except paramiko.AuthenticationException:
        logging.error(f"Authentication failed for router {router_name}")
        return "Authentication failed"
    except paramiko.SSHException as e:
        logging.error(f"SSH error for router {router_name}: {e}")
        return f"SSH connection error: {e}"
    except Exception as e:
        logging.error(f"An unexpected error occurred for router {router_name}: {e}")
        return f"An unexpected error occurred: {e}"


# NEW ENDPOINT: To get the list of routers for the frontend dropdown
@app.route("/get_routers", methods=["GET"])
def get_routers():
    logging.info("Request received at /get_routers endpoint.")
    router_names = list(ROUTER_HOSTS.keys())
    return jsonify(router_names)


@app.route("/query", methods=["POST"])
def query_router():
    logging.info("Request received at /query endpoint.")
    data = request.get_json()
    router = data.get("router")
    question = data.get("question")

    if not router or not question:
        logging.warning("Missing 'router' or 'question' in request.")
        return jsonify({"error": "Missing 'router' or 'question'", "status": "Request validation failed"}), 400

    if not CLI_CONTEXT:
        return jsonify({"error": "CLI context not loaded", "status": "Initialization error"}), 500
    if not API_CONFIG:
        return jsonify({"error": "API config not loaded", "status": "Initialization error"}), 500
    if not ROUTER_HOSTS:
        return jsonify({"error": "Router list not loaded", "status": "Initialization error"}), 500


    if router not in ROUTER_HOSTS:
        logging.warning(f"Router '{router}' not found in configured devices.")
        return jsonify({"error": f"Router '{router}' is not configured in devices.list", "status": "Router not found"}), 404

    prompt = generate_prompt(question)
    logging.info("Prompt generated for LLM.")

    command = ask_gemini(prompt)

    if not command:
        logging.error("Failed to generate a valid command from LLM.")
        return jsonify({"error": "Failed to generate a valid command", "status": "LLM command generation failed"}), 500

    output = execute_ssh_command(router, command)

    # Add a success status to the response
    logging.info("Query processing complete. Sending response.")
    return jsonify({
        "router": router,
        "question": question,
        "command": command,
        "output": output,
        "status": "Success"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
