__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '09/Jun/2015'

import base64
import stat
from os import sep

from paramiko.transport import Transport
from paramiko.rsakey import RSAKey

HOST1_CONNECTIONS = {}
HOST2_CONNECTIONS = {}

def get_sftp_client(source, session_key):
    if source == 'host1':
        return HOST1_CONNECTIONS[session_key]
    elif source == 'host2':
        return HOST2_CONNECTIONS[session_key]

def create_sftp_client(source, user_name, password, otc, hostname, port):
    # TODO: Replace this check with a checkbox in the dashboard on whether to
    #       concatenate password and one time key (otc)
    if source == 'host1':
        return _create_host1_sftp_client(user_name, password, otc, hostname, port)
    elif source == 'host2':
        return _create_host2_sftp_client(user_name, password + otc, hostname, port)

def _create_host1_sftp_client(user_name, password, otc, hostname, port):
    if hostname is None:
        hostname = "tsd-fx01.tsd.usit.no"
    if port is None:
        port = 22
    else:
        port = int(port)
    transport = Transport((hostname, port))
    transport.start_client()

    def sftp_auth_handler(title, instructions, prompt_list):
        if len(prompt_list) == 0:
            return []
        if 'Password' in prompt_list[0][0]:
            return [password]
        else:
            return [otc]

    transport.auth_interactive(user_name, sftp_auth_handler)
    return transport.open_sftp_client()

def _create_host2_sftp_client(user_name, password, hostname, port):
    if hostname is None:
        hostname = "mosler.bils.se"
    if port is None:
        port = 22
    else:
        port = int(port)
    transport = Transport((hostname, port))
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
                                   sftp_client_to.open(to_cwd + sep + file_attr.filename, 'w'))

def delete_folder(folder_name, path, sftp_client):
    for file_attr in sftp_client.listdir_attr(path + sep + folder_name):
        if stat.S_ISDIR(file_attr.st_mode):
            delete_folder(file_attr.filename, path + sep + folder_name, sftp_client)
        else:
            sftp_client.remove(path + sep + folder_name + sep + file_attr.filename)
    sftp_client.rmdir(path + sep + folder_name)
