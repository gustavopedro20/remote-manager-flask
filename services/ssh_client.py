import logging
import paramiko

from util.constants import REMOTE_FILE_NAME, LOCAL_FILE_PATH

IP = '192.168.87.129'
PORT = '22'
USERNAME = 'gustavo'
PASSWORD = '130896'
VMSTAT = f'vmstat > {REMOTE_FILE_NAME}'

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

    def get_cpu_statistics(self):
        self.client.exec_command(VMSTAT)
        pwd = self.get_remote_current_path()
        remote_path = f'{pwd}/{REMOTE_FILE_NAME}'
        self.get_file_with_sftp(remote_path)
        return LOCAL_FILE_PATH

    def disconnect(self):
        self.client.close()