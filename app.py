import logging
import time
from datetime import datetime

from flask import Flask, request, jsonify
from flask import render_template
from flask_cors import CORS
from flask_mail import Mail
from flask_mail import Message
from flask_socketio import SocketIO, send

from config import mail_settings, sql_setting
from mod_machine.dto import MailDTO
from mod_machine.models import Machine
from mod_machine.models import db, Config
from mod_machine.services import SSHClient

app = Flask(__name__, template_folder='templates')
app.config.update(mail_settings)
app.config.update(sql_setting)
db.init_app(app)
mail = Mail(app)
CORS(app)
socket_io = SocketIO(app, cors_allowed_origins="*")
logging.basicConfig(level=logging.INFO)


@app.route('/')
def index():
    return 'Hello, World!'


@app.route('/tasks', methods=['DELETE'])
def delete_task():
    pid = request.args['pid']
    machine_id = request.args['machineId']
    machine = Machine.query.get(machine_id)
    ssh = SSHClient(machine.serialize['ip'], machine.serialize['port'],
                    machine.serialize['hostname'], machine.serialize['password'])
    ssh.kill_task(pid)
    ssh.disconnect()
    return jsonify(), 204


@socket_io.on('tasks')
def socket_tasks(machine_id):
    machine = Machine.query.get(machine_id)
    if machine_id is not None and machine:
        ssh = SSHClient(machine.ip, machine.port, machine.hostname, machine.password)
        if ssh.is_connected():
            while True:
                disk_usage = ssh.get_disc_usage()
                task_list, men_dic, cpu_usage = ssh.get_task_men_cpu()
                sorted(task_list, key=lambda i: i['PID'])
                response = {
                    'tasks': task_list,
                    'men': men_dic,
                    'diskUsage': disk_usage,
                    'cpuUsage': cpu_usage
                }
                send(response)
                time.sleep(15)
        else:
            response = {
                'error': f'Cant not connect to the server {machine.ip}',
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


@app.route('/api/machines', methods=['POST'])
def create_machine():
    machine = request.get_json()
    new_machine = Machine(
        ip=machine['ip'],
        hostname=machine['hostname'],
        password=machine['password'],
        port=machine['port'],
        system=machine['system']
    )
    try:
        db.session.add(new_machine)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e, 'status': 500}), 500

    new_config = Config(
        maxMenInPercent=machine['config']['maxMenInPercent'],
        maxDiscInPercent=machine['config']['maxDiscInPercent'],
        maxCPUInPercent=machine['config']['maxCPUInPercent'],
        email=machine['config']['email'],
        machine_id=new_machine.id
    )
    try:
        db.session.add(new_config)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e, 'status': 500}), 500

    response = Machine.query.get(new_machine.id)
    return jsonify(response.serialize), 201


@app.route('/api/machines', methods=['GET'])
def find_all_machine():
    tasks = Machine.query.all()
    return jsonify([i.serialize for i in tasks]), 200


@app.route('/api/machines/<int:id>', methods=['GET'])
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


@app.route('/api/machines/<int:id>', methods=['DELETE'])
def delete_machine(id):
    machine = Machine.query.get_or_404(id)
    try:
        db.session.delete(machine)
        db.session.commit()
        return jsonify(), 204
    except Exception as e:
        return jsonify({'error': e.__cause__, 'status': 500}), 500


@app.route('/api/machines', methods=['PUT'])
def update_machine():
    machine_update = request.get_json()
    machine = Machine.query.get(int(machine_update['id']))
    machine.ip = machine_update['ip']
    machine.hostname = machine_update['hostname']
    machine.port = machine_update['port']
    machine.system = machine_update['system']
    machine.password = machine_update['password']
    config = Config.query.get(machine_update['config']['id'])
    config.email = machine_update['config']['email']
    config.max_disc_in_percent = machine_update['config']['maxDiscInPercent']
    config.max_men_in_percent = machine_update['config']['maxMenInPercent']
    config.max_cpu_in_percent = machine_update['config']['maxCPUInPercent']
    db.session.commit()
    return jsonify(machine.serialize), 200


@app.route('/trigger', methods=['GET'])
def verify_machine_usage():
    machines = Machine.query.all()
    for machine in machines:
        ssh = SSHClient(machine.ip, machine.port, machine.hostname, machine.password)
        if ssh.is_connected():
            task, men, cpu = ssh.get_task_men_cpu()
            disc = ssh.get_disc_usage()
            ssh.disconnect()

            max_cpu = machine.config.maxCPUInPercent
            max_men = machine.config.maxMenInPercent
            max_disc = machine.config.maxDiscInPercent

            current_men = int((men['free'] * 100) / men['total'])
            current_cpu = int(cpu)
            current_disc = int(disc['usage_per_cent'])

            if current_disc > max_disc or current_men > max_men or current_cpu > max_cpu:
                dto = MailDTO(max_cpu, max_men, max_disc, current_men, current_cpu, current_disc)
                send_mail_from_template(
                    f'A máquina {machine.ip} ultrapassou os limites de uso de CPU, memória ou disco estabelecidos!',
                    machine.config.email,
                    'machine.html',
                    dto=dto,
                    machine=machine
                )
    return '', 200


def send_mail_from_template(subject, recipient, template, **kwargs):
    with app.app_context():
        print('\n', 'send email...', '\n')
        logging.info('Send e-mail to: {}', recipient)
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        msg.html = render_template(
            template,
            data=kwargs.get('dto'),
            machine=kwargs.get('machine'),
            date=datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        )
        mail.send(msg)


if __name__ == '__main__':
    socket_io.run(app, debug=True)
