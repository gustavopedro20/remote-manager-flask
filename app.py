from flask_cors import CORS
from flask import Flask, request, jsonify

from services.ssh_client import SSHClient
from util.constants import convert_txt_vmstat_to_dict

APP = Flask(__name__)
CORS(APP)


@APP.route('/')
def index():
    return 'Hello, World!'


@APP.route('/commands', methods=['GET'])
def commands():
    ssh = SSHClient()
    response = ssh.run(request.args['command'])
    ssh.disconnect()
    return jsonify(response.strip().decode()), 200


@APP.route('/swap/statistics', methods=['GET'])
def get_cpu_statistics():
    ssh = SSHClient()
    local_path = ssh.get_swap_statistics()
    ssh.disconnect()
    return jsonify(convert_txt_vmstat_to_dict(local_path)), 200


@APP.route('/tasks', methods=['GET'])
def get_all_tasks():
    ssh = SSHClient()
    tasks = ssh.get_all_tasks()
    ssh.disconnect()
    return jsonify(tasks), 200


@APP.route('/tasks', methods=['DELETE'])
def delete_task():
    pid = request.args['pid']
    ssh = SSHClient()
    ssh.kill_task(pid)
    ssh.disconnect()
    return 204


if __name__ == "__main__":
    APP.run(debug=True, host='0.0.0.0', port=5000)
