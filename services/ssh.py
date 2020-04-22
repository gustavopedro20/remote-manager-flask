import paramiko


def connect(ip, port, username, password):
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        #
        # client.connect(ip, port, username, password)
        #
        # stdin, stdout, stderr = client.exec_command("top > teste.txt")
        # stdin, stdout, stderr = client.exec_command("cat teste.txt")
        #
        # for row in stdout.readlines():
        #     data = row.split()
        return []

    finally:
        client.close()

    return []
