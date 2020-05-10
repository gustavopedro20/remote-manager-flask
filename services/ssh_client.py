import logging
import paramiko

from util.constants import REMOTE_FILE_NAME, LOCAL_FILE_PATH

IP = '192.168.1.9'
PORT = '22'
USERNAME = 'gustavo'
PASSWORD = '130896'

logging.basicConfig(level=logging.INFO)


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

    def get_all_tasks(self):
        tasks = self.run('top -n 1 -b').decode("utf-8")
        file = open('text.txt', 'w+')
        file.write(tasks)
        file.close()
        file = open('text.txt', 'r')
        lines = file.readlines()
        file.close()
        label = ['PID', 'USER', 'PR', 'NI', 'VIRT', 'RES', 'SHR', 'S', '%CPU', '%MEM', 'TIME+', 'COMMAND']
        new_list = []
        for i, line in enumerate(lines):
            if i > 6:
                dic = {}
                data = [x.replace('\n', '') for x in line.split(' ') if x.strip() != '']
                if len(data) == 13:
                    s = data[11] + ' ' + data[12]
                    data.pop()
                    data.pop()
                    data.append(s)
                for j, value in enumerate(data):
                    dic[label[j]] = value
                new_list.append(dic)
        return new_list

    def kill_task(self, pid):
        return self.run(f'kill {pid}')

    def disconnect(self):
        self.client.close()
