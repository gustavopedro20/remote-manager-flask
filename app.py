from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, send
import time

from mod_machine.models import db, Machine
from mod_machine.services import SSHClient
from mod_machine.utils.constants import convert_txt_vmstat_to_dict

APP = Flask(__name__)
CORS(APP)
db.init_app(APP)
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///machine.db'
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


@socketio.on('tasks')
def socket_tasks(machine_id):
    if machine_id is not None:
        machine = Machine.query.get(machine_id)
        if machine:
            try:
                ssh = SSHClient(machine.ip, machine.port, machine.username, machine.password)
                while True:
                    task_list, men_dic = ssh.get_all_tasks_and_men_statistics()
                    disk_usage = ssh.get_disc_usage()
                    response = {
                        'tasks': task_list,
                        'men': men_dic,
                        'diskUsage': disk_usage
                    }
                    # emit('join_room', response, broadcast=True)
                    send(response)
                    time.sleep(15)
            except Exception as e:
                response = {
                    'error': f'Cant not connect to the server: {e.__cause__}',
                    'status': 500
                }
                send(response)
        else:
            response = {
                'message': 'not found',
                'status': 404,
                'details': 'machine not found'
            }
            send(response)
    else:
        response = {
            'error': 'machine id not found',
            'status': 404
        }
        send(response)


@APP.route('/api/machines', methods=['POST'])
def create_machine():
    data = request.get_json()
    new_machine = Machine(ip=data['ip'],
                          hostname=data['hostname'],
                          password=data['password'],
                          port=data['port'],
                          system=data['system'])
    try:
        db.session.add(new_machine)
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
        return jsonify({'error': e.__cause__, 'status': 500}), 500


@APP.route('/api/machines', methods=['GET'])
def find_all_machine():
    tasks = Machine.query.all()
    return jsonify([i.serialize for i in tasks])


@APP.route('/api/machines/<int:id>', methods=['GET'])
def find_one_machine(id):
    machine = Machine.query.get(id)
    if machine:
        return jsonify(machine.serialize), 200
    else:
        response = {
            'message': 'not found',
            'status': 404,
            'details': 'machine not found'
        }
        return jsonify(response), 404


@APP.route('/api/machines/<int:id>', methods=['DELETE'])
def delete_machine(id):
    machine = Machine.query.get_or_404(id)
    try:
        db.session.delete(machine)
        db.session.commit()
        return jsonify(), 204
    except Exception as e:
        return jsonify({'error': e.__cause__, 'status': 500}), 500


@APP.route('/api/machines', methods=['PUT'])
def update_machine():
    machine = Machine.query.get(request.json.get('id'))
    machine.ip = request.json.get('ip')
    machine.hostname = request.json.get('hostname')
    machine.port = request.json.get('port')
    machine.system = request.json.get('system')
    machine.password = request.json.get('password')
    db.session.commit()
    response = Machine.query.get(machine.id)
    return jsonify(response.serialize), 200


if __name__ == '__main__':
    socketio.run(APP, debug=True)
