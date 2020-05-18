from flask_cors import CORS
from flask import Flask, request, jsonify, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

from services.ssh_client import SSHClient
from util.constants import convert_txt_vmstat_to_dict

APP = Flask(__name__)
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///machine.db'
db = SQLAlchemy(APP)

CORS(APP)

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(200), nullable=False)
    hostname = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    port = db.Column(db.String(200), nullable=False)
    system = db.Column(db.String(200), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'id'         : self.id,
           'ip'         : self.ip,
           'hostname'   : self.hostname,
           'port'       : self.port,
           'password'   : self.password
       }

    def __repr__(self):
        return '<Machine %r' %self.id

@APP.route('/api/machines', methods=['POST'])
def create_machine():
    data = request.get_json()
    print(" oi eu sou seu cu",data)
    new_machine = Machine(ip = data['ip'],
                            hostname = data['hostname'],
                            password = data['password'],
                            port = data['port'],
                            system = data['system'])
    try:
        db.session.add(new_machine)
        db.session.commit()
        return jsonify()
    except:
        return 'Teve algum erro ao criar'

@APP.route('/api/machines', methods = ['GET'])
def list_machines():
    tasks = Machine.query.all()
    return jsonify([i.serialize for i in tasks])


@APP.route('/api/machines/<int:id>', methods=['DELETE'])
def delete(id):
    task_to_delete = Machine.query.get_or_404(id)

    try: 
        db.session.delete(task_to_delete)
        db.session.commit()
        return jsonify()
    except:
        return 'Tivemos problema para excluir essa task'


@APP.route('/api/machines', methods=['PUT'])
def update():
    machine = Machine.query.get(request.json.get('id', machine.id))
    machine.ip = request.json.get('ip', machine.ip)
    machine.hostname = request.json.get('hostname', machine.hostname)
    machine.port = request.json.get('port', machine.port)
    machine.system = request.json.get('system', machine.system)
    machine.password = request.json.get('password', machine.password)

    db.session.commit()

    return jsonify()
    

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


if __name__ == "__main__":
    APP.run(debug=True, host='0.0.0.0', port=5000)
