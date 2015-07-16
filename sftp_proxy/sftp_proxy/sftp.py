__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '09/Jun/2015'

import stat
from os import sep

from django.utils.timezone import now
from paramiko.transport import Transport

from .ws import update_transmission_progress



# the structure of this dictionary is
# {"session_key": {"host1": sftp_connection, "host2": sftp_connection, "expiry_time": time}}
SFTP_CONNECTIONS = {}


def add_sftp_connection(session_key, source, sftp_client, expiry_time):
    if session_key in SFTP_CONNECTIONS:
        SFTP_CONNECTIONS[session_key][source] = sftp_client
    else:
        SFTP_CONNECTIONS[session_key] = {source: sftp_client, 'expiry_time': expiry_time}


def clean_sftp_connections():
    for key in list(iter(SFTP_CONNECTIONS)):
        if 'expiry_time' in SFTP_CONNECTIONS[key]:
            if now() > SFTP_CONNECTIONS[key]['expiry_time']:
                del SFTP_CONNECTIONS[key]


def get_sftp_client(source, session_key):
    return SFTP_CONNECTIONS[session_key][source]


def remove_sftp_connection(source, session_key):
    if session_key in SFTP_CONNECTIONS:
        if source in SFTP_CONNECTIONS[session_key]:
            del SFTP_CONNECTIONS[session_key][source]


def create_sftp_client(user_name, password, otc, hostname, port):
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

    return transport.open_sftp_client()


def transfer_folder(folder_name, from_path, sftp_client_from, to_path, sftp_client_to):
    sftp_client_to.chdir(to_path)
    sftp_client_to.mkdir(folder_name)
    sftp_client_to.chdir(to_path + sep + folder_name)
    to_cwd = sftp_client_to.getcwd()

    sftp_client_from.chdir(from_path + sep + folder_name)
    from_cwd = sftp_client_from.getcwd()
    content = sftp_client_from.listdir_attr(from_cwd)
    for file_attr in content:
        if stat.S_ISDIR(file_attr.st_mode):
            transfer_folder(file_attr.filename, from_cwd, sftp_client_from, to_cwd, sftp_client_to)
        else:
            sftp_client_from.getfo(from_cwd + sep + file_attr.filename,
                                   sftp_client_to.open(to_cwd + sep + file_attr.filename, 'w'),
                                   lambda transferred_bytes, total_bytes: update_transmission_progress(transferred_bytes, total_bytes, file_name=file_attr.filename))


def delete_folder(folder_name, path, sftp_client):
    for file_attr in sftp_client.listdir_attr(path + sep + folder_name):
        if stat.S_ISDIR(file_attr.st_mode):
            delete_folder(file_attr.filename, path + sep + folder_name, sftp_client)
        else:
            sftp_client.remove(path + sep + folder_name + sep + file_attr.filename)
    sftp_client.rmdir(path + sep + folder_name)
