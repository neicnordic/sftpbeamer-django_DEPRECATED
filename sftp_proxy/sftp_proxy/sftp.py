import stat
from os import sep
from datetime import datetime

from paramiko.transport import Transport

__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '09/Jun/2015'


class SftpConnectionManager:

    def __init__(self):
        """
        the structure of this dictionary is
        {"session_key": {"host1": sftp_connection, "host2": sftp_connection, "expiry_time": time}}
        """
        self.connections = {}

    def add_sftp_connection(self, session_key, source, sftp_client, expiry_time):
        if session_key in self.connections:
            self.connections[session_key][source] = sftp_client
        else:
            self.connections[session_key] = {source: sftp_client, 'expiry_time': expiry_time}

    def clean_sftp_connections(self):
        for key in list(iter(self.connections)):
            if 'expiry_time' in self.connections[key]:
                if datetime.now() > self.connections[key]['expiry_time']:
                    if 'host1' in self.connections[key]:
                        self.connections[key]['host1'].close()
                    if 'host2' in self.connections[key]:
                        self.connections[key]['host2'].close()
                    del self.connections[key]

    def open_sftp_client(self, source, session_key):
        return self.connections[session_key][source].open_sftp_client()

    def remove_sftp_connection(self, source, session_key):
        if session_key in self.connections:
            if source in self.connections[session_key]:
                self.connections[session_key][source].close()
                del self.connections[session_key][source]
                if len(self.connections[session_key].keys()) == 1:
                    del self.connections[session_key]

    @staticmethod
    def authenticate_sftp_user(user_name, password, otc, hostname, port):

        def sftp_auth_handler(title, instructions, prompt_list):
            if len(prompt_list) == 0:
                return []
            if 'Password' in prompt_list[0][0]:
                return [password]
            else:
                return [otc]

        transport = Transport((hostname, int(port)))

        if otc != '':
            transport.start_client()
            transport.auth_interactive(user_name, sftp_auth_handler)
        else:
            transport.connect(None, user_name, password)

        return transport

