from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

command_state = {"command": "None"}


@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    soil_moisture = data.get("soil_moisture")

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "soil_moisture": soil_moisture
    }

    try:
        with open("soil_data.json", "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(log_entry)

    with open("soil_data.json", "w") as file:
        json.dump(existing_data, file, indent=4)

    print(f"Logged data: {log_entry}")
    return jsonify({"message": "Data received and logged successfully!"})

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open("soil_data.json", "r") as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify([])


@app.route('/command', methods=['GET'])
def send_command():
    print(f'Sending command: {command_state}')
    return jsonify(command_state)

@app.route('/update-command', methods=['POST'])
def update_command():
    global command_state
    command = request.json.get("command")
    command_state["command"] = command
    print("Updated command:", command)
    return jsonify({"message": "Command updated successfully!"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)