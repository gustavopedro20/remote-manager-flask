from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room, emit, Namespace
import time

from services.ssh_client import SSHClient
from util.constants import convert_txt_vmstat_to_dict

APP = Flask(__name__)
CORS(APP)
socketio = SocketIO(APP, cors_allowed_origins="*")


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
    tasks, men_statistics = ssh.get_all_tasks_and_men_statistics()
    ssh.disconnect()
    return jsonify({'tasks': tasks, 'men': men_statistics}), 200


@APP.route('/tasks', methods=['DELETE'])
def delete_task():
    pid = request.args['pid']
    ssh = SSHClient()
    ssh.kill_task(pid)
    ssh.disconnect()
    return jsonify(), 204


@APP.route('/disk-usage', methods=['GET'])
def get_disk_usage():
    ssh = SSHClient()
    v = ssh.get_disc_usage()
    ssh.disconnect()
    return jsonify(v), 200


@socketio.on('create')
def on_create(data):
    # join_room(1)
    try:
        ssh = SSHClient()
        # task_list, men_dic = ssh.get_all_tasks_and_men_statistics()
        # emit('join_room', {'tasks': task_list, 'men': men_dic}, broadcast=True)
        while True:
            task_list, men_dic = ssh.get_all_tasks_and_men_statistics()
            disk_usage = ssh.get_disc_usage()
            response = {
                'tasks': task_list,
                'men': men_dic,
                'diskUsage': disk_usage
            }
            emit('join_room', response, broadcast=True)
            time.sleep(15)
    except Exception as e:
        emit("join_room", {'error': f"Cant't connect to the server: {e.__cause__}"}, broadcast=True)


if __name__ == '__main__':
    socketio.run(APP, debug=True)