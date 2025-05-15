from flask import Flask, request, jsonify
import paramiko

app = Flask(__name__)

# SSH credentials (you can improve this to load from env or config)
ROUTER_CREDENTIALS = {
    "node1": {"host": "clab-test_1-node1", "username": "admin", "password": "NokiaSrl1!"},
    "node2": {"host": "clab-test_1-node2", "username": "admin", "password": "NokiaSrl1!"},
}

# Simple SSH helper
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
    router = data.get("router")  # e.g. node1
    command = data.get("command")  # for now: manually supply

    if not router or not command:
        return jsonify({"error": "Missing router or command"}), 400

    creds = ROUTER_CREDENTIALS.get(router)
    if not creds:
        return jsonify({"error": f"Unknown router {router}"}), 404

    output, error = ssh_and_run_command(
        creds["host"], creds["username"], creds["password"], command
    )

    return jsonify({
        "router": router,
        "command": command,
        "output": output,
        "error": error
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)

