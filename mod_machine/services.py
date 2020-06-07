import logging
import paramiko
import re

from mod_machine.utils.constants import REMOTE_FILE_NAME, LOCAL_FILE_PATH

TASK_LABEL = ['PID', 'USER', 'PR', 'NI', 'VIRT', 'RES', 'SHR', 'S', 'CPU', 'MEM', 'TIME', 'COMMAND']
MEN_LABEL = ['total', 'free', 'used', 'buff/cache']
DISC_LABEL = ['total', 'usage', 'free', 'usage_per_cent']
NUMBER_PATTERN = '([0-9])'

logging.basicConfig(level=logging.INFO)


def write_file_and_return_all_lines(value):
    file = open('text.txt', 'w+')
    file.write(value)
    file.close()
    file = open('text.txt', 'r')
    return file.readlines()


class SSHClient:
    def __init__(self, ip, port, username, password):
        try:
            logging.info('Start connection...')
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(ip, port, username, password)
            self.client = client
            self.connect = True
            logging.info('Successful connect!')
        except Exception as e:
            self.connect = False
            logging.error('Error try connecting ssh: ', e)

    def run(self, command='ls'):
        stdin, stdout, stderr = self.client.exec_command(command)
        if stderr.channel.recv_exit_status() != 0:
            return stderr.read()
        else:
            return stdout.read()

    def get_remote_current_path(self):
        stdin, stdout, stderr = self.client.exec_command('pwd')
        return str(stdout.read())[2: -3]

    def get_file_with_sftp(self, remote_path):
        ftp_client = self.client.open_sftp()
        ftp_client.get(remote_path, LOCAL_FILE_PATH)
        ftp_client.close()
        self.client.exec_command(f'rm -rf {remote_path}')

    def get_swap_statistics(self):
        self.client.exec_command(f'vmstat > {REMOTE_FILE_NAME}')
        pwd = self.get_remote_current_path()
        remote_path = f'{pwd}/{REMOTE_FILE_NAME}'
        self.get_file_with_sftp(remote_path)
        return LOCAL_FILE_PATH

    @staticmethod
    def get_men_usage(line):
        men_dic = {}
        men = [int(x) for x in line.split(' ') if (re.match(NUMBER_PATTERN, x))]
        for k, value in enumerate(men):
            men_dic[MEN_LABEL[k]] = value / 994538
        return men_dic

    @staticmethod
    def get_cpu_usage(line):
        cpu = [x for x in line.split(' ') if x.strip() if (re.match(NUMBER_PATTERN, x))][0]
        if cpu.count(',') > 0:
            return float(cpu.replace(',', '.'))
        return 0

    @staticmethod
    def get_task(line):
        task = {}
        data = [x.replace('\n', '') for x in line.split(' ') if x.strip() != '']

        if data[11] == 'top' or data[11] == 'sshd':
            return None

        if len(data) == 13:
            task_name = data[11] + ' ' + data[12]
            del data[11: 13]
            data.append(task_name)

        for j, value in enumerate(data):
            task[TASK_LABEL[j]] = value
        return task

    def get_task_men_cpu(self):
        tasks = self.run('top -n 1 -b').decode("utf-8")
        lines = write_file_and_return_all_lines(tasks)
        men_dic = {}
        cpu_usage = 0
        task_list = []
        for i, line in enumerate(lines):
            if i == 2:
                cpu_usage = self.get_cpu_usage(line)
            if i == 3:
                men_dic = self.get_men_usage(line)
            if i > 6:
                task = self.get_task(line)
                if task is not None:
                    task_list.append(task)

        return task_list, men_dic, cpu_usage

    def kill_task(self, pid):
        return self.run(f'kill {pid}')

    def get_disc_usage(self):
        disc_usage = self.run('df').decode("utf-8")
        lines = write_file_and_return_all_lines(disc_usage)
        arr = [0, 0, 0, 0]
        dic = {}
        for i, value in enumerate(lines):
            if i > 0:
                s = [int(x.replace('%', '')) for x in value.split(' ') if x.strip() != '' and (re.match(NUMBER_PATTERN, x))]
                for j, v in enumerate(s):
                    arr[j] += v
        for k, x in enumerate(arr):
            if not DISC_LABEL[k] == DISC_LABEL[3]:
                dic[DISC_LABEL[k]] = x / 1000000
            else:
                dic[DISC_LABEL[k]] = x
        return dic

    def is_connected(self):
        if self.connect:
            if self.client.get_transport() is not None:
                return self.client.get_transport().is_active()
            else:
                return False
        return False

    def disconnect(self):
        self.client.close()
