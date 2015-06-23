__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '09/Jun/2015'

import base64
import stat
from os import sep

from paramiko.transport import Transport
from paramiko.rsakey import RSAKey

TSD_CONNECTIONS = {}
MOSLER_CONNECTIONS = {}

def get_sftp_client(source, session_key):
    if source == 'tsd':
        return TSD_CONNECTIONS[session_key]
    elif source == 'mosler':
        return MOSLER_CONNECTIONS[session_key]

def create_sftp_client(source, user_name, password, otc):
    if source == 'tsd':
        return _create_tsd_sftp_client(user_name, password, otc)
    elif source == 'mosler':
        return _create_mosler_sftp_client(user_name, password + otc)

def _create_tsd_sftp_client(user_name, password, otc):
    host = "tsd-fx01.tsd.usit.no"
    port = 22
    transport = Transport((host, port))
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

def _create_mosler_sftp_client(user_name, password):
    host = "mosler.bils.se"
    port = 22
    transport = Transport((host, port))
    transport.connect(_get_mosler_key(), user_name, password)
    return transport.open_sftp_client()


def _get_mosler_key():
    """The RSA key for the sftp server"""
    key = 'AAAAB3NzaC1yc2EAAAADAQABAAABAQC36rThhzm4jeZFtXCbNhu/sArVRbDP50qhNJ5JsXB723UxXsE4g0/aOHcuezdIPl0KggHyRBX+gxFd3fkYmQW3ToBNEXlT/eWi3jL2L+4gqtAJI0pLiTNX/UmLxCoKjlAkWYIur+dqMDhcs73UE9vlG+zPCSZlJYxmrzWEKAJmhzUzb6Bjh0/npEUN1CaMylgRJ3dwQfRLTm4pmR4nl0CShgx2DOfntTJaQ7lVLngO7lhVSsj5V3qCWz4Y5Pay8QdPjz5Xf2gPbgVCsM2JuU7Lbkzc9pFZd5kzFQNM2Q20mUqiZBh9SeCioXDz17AOcYcBQhDW/kca8ncC3xb4Uhh7'
    binary = base64.decodebytes(bytes(key, 'utf8'))
    return RSAKey(data=binary)

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
