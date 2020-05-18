import logging
import paramiko
import re

from util.constants import REMOTE_FILE_NAME, LOCAL_FILE_PATH

IP = '192.168.87.130'
PORT = '22'
USERNAME = 'gustavo'
PASSWORD = '130896'
TASK_LABEL = ['PID', 'USER', 'PR', 'NI', 'VIRT', 'RES', 'SHR', 'S', 'CPU', 'MEM', 'TIME', 'COMMAND']
MEN_LABEL = ['total', 'free', 'used', 'buff/cache']
DISC_LABEL = ['total', 'usage', 'free', 'usage_per_cent']

logging.basicConfig(level=logging.INFO)


def write_file_and_return_all_lines(value):
    file = open('text.txt', 'w+')
    file.write(value)
    file.close()
    file = open('text.txt', 'r')
    return file.readlines()


class SSHClient:
    def __init__(self):
        try:
            logging.info('Start connection...')
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(IP, PORT, USERNAME, PASSWORD)
            self.client = client
            logging.info('Successful connect!')
        except Exception as e:
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

    def get_all_tasks_and_men_statistics(self):
        tasks = self.run('top -n 1 -b').decode("utf-8")
        lines = write_file_and_return_all_lines(tasks)
        men_dic = {}
        task_list = []
        for i, line in enumerate(lines):
            # get men usage
            if i == 3:
                men = [int(x) for x in line.split(' ') if (re.match('([0-9])', x))]
                for k, value in enumerate(men):
                    men_dic[MEN_LABEL[k]] = value
            # get tasks
            if i > 6:
                dic = {}
                data = [x.replace('\n', '') for x in line.split(' ') if x.strip() != '']
                if len(data) == 13:
                    s = data[11] + ' ' + data[12]
                    data.pop()
                    data.pop()
                    data.append(s)
                for j, value in enumerate(data):
                    dic[TASK_LABEL[j]] = value
                task_list.append(dic)
        return task_list, men_dic

    def kill_task(self, pid):
        return self.run(f'kill {pid}')

    def get_disc_usage(self):
        disc_usage = self.run('df').decode("utf-8")
        test = write_file_and_return_all_lines(disc_usage)
        arr = [0, 0, 0, 0]
        dic = {}
        for i, value in enumerate(test):
            if i > 0:
                s = [int(x.replace('%', '')) for x in value.split(' ') if x.strip() != '' and (re.match('([0-9])', x))]
                for j, v in enumerate(s):
                    arr[j] += v
        for k, x in enumerate(arr):
            dic[DISC_LABEL[k]] = x
        return dic

    def disconnect(self):
        self.client.close()
