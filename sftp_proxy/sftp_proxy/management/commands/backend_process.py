import stat
from os import sep
from datetime import datetime
from threading import Thread

import zmq
from zmq.eventloop.ioloop import ZMQIOLoop
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from zmq.utils import jsonapi
from paramiko.ssh_exception import SSHException
from paramiko import SFTPError
from django.core.management.base import NoArgsCommand

from sftp_proxy.sftp import SftpConnectionManager, transfer_folder, delete_folder
from sftp_proxy.constants import ZmqMessageKeys, ZmqMessageValues
from sftp_proxy.ws import update_transmission_progress

__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '17/Oct/2015'


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        BackendProcess()


class BackendProcess:
    """
    This is a second process, which is used for managing the sftp connections. In order to run this process, run command
    "python manage.py backend_process". There are two opening zmq sockets. One is for managing the synchronous tasks,
    for example, connecting with sftp server, disconnecting with sftp server, listing content and so on. The other is
    dedicated to file transfer.
    """

    def __init__(self):
        loop = ZMQIOLoop.instance()

        ctx = zmq.Context.instance()
        sftp_connection_socket = ctx.socket(zmq.REP)
        sftp_connection_socket.bind("tcp://*:4444")
        self.sftp_connection_stream = ZMQStream(sftp_connection_socket, loop)

        sftp_transfer_socket = ctx.socket(zmq.REP)
        sftp_transfer_socket.bind("tcp://*:4445")
        self.sftp_transfer_stream = ZMQStream(sftp_transfer_socket, loop)

        self.sftp_connection_stream.on_recv(self.__sftp_connection_stream_receive_callback__)
        self.sftp_transfer_stream.on_recv(self.__sftp_transfer_stream_receive_callback__)

        self.sftp_connection_manager = SftpConnectionManager()

        IOLoop.instance().start()

    def __sftp_connection_stream_receive_callback__(self, msg):
        """
        This is the callback method when the sftp_connection_stream socket receives the message. Every message should
        include one field, which is called "action" representing the purpose of this request. At the end of this method,
        self.sftp_connection_stream.send_json method should be invoked.
        :param msg: received message by sftp_connection_stream
        """
        resp_msg = jsonapi.loads(msg[0])
        if resp_msg[ZmqMessageKeys.ACTION.value] == ZmqMessageValues.CLEAN.value:
            self.sftp_connection_manager.clean_sftp_connections()
            self.sftp_connection_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.SUCCESS.value})
        elif resp_msg[ZmqMessageKeys.ACTION.value] == ZmqMessageValues.CONNECT.value:
            session_key = resp_msg[ZmqMessageKeys.SESSION_KEY.value]
            user_name = resp_msg[ZmqMessageKeys.USERNAME.value]
            otc = resp_msg[ZmqMessageKeys.OTC.value]
            password = resp_msg[ZmqMessageKeys.PASSWORD.value]
            hostname = resp_msg[ZmqMessageKeys.HOSTNAME.value]
            port = resp_msg[ZmqMessageKeys.PORT.value]
            source = resp_msg[ZmqMessageKeys.SOURCE.value]
            expiry = resp_msg[ZmqMessageKeys.EXPIRY.value]

            try:
                transport = self.sftp_connection_manager.authenticate_sftp_user(user_name, password, otc, hostname, port)
            except SSHException as exce:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: exce.args[0]})
            else:
                self.sftp_connection_manager.add_sftp_connection(session_key, source, transport, datetime.fromtimestamp(expiry))
                self.sftp_connection_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.SUCCESS.value})
        elif resp_msg[ZmqMessageKeys.ACTION.value] == ZmqMessageValues.LIST.value:
            session_key = resp_msg[ZmqMessageKeys.SESSION_KEY.value]
            source = resp_msg[ZmqMessageKeys.SOURCE.value]
            path = resp_msg[ZmqMessageKeys.PATH.value] if ZmqMessageKeys.PATH.value in resp_msg else sep
            try:
                content = self.sftp_connection_manager.open_sftp_client(source, session_key).listdir_iter(path)
                data_list = []
                for file_attr in content:
                    if stat.S_ISDIR(file_attr.st_mode):
                        data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                    else:
                        data_list.append([file_attr.filename, file_attr.st_size, "file"])
            except PermissionError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.strerror})
            except SFTPError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.args[0]})
            else:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.DATA.value: data_list})
        elif resp_msg[ZmqMessageKeys.ACTION.value] == ZmqMessageValues.DISCONNECT.value:
            session_key = resp_msg[ZmqMessageKeys.SESSION_KEY.value]
            source = resp_msg[ZmqMessageKeys.SOURCE.value]
            self.sftp_connection_manager.remove_sftp_connection(source, session_key)
            self.sftp_connection_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.SUCCESS.value})
        elif resp_msg[ZmqMessageKeys.ACTION.value] == ZmqMessageValues.DELETE.value:
            session_key = resp_msg[ZmqMessageKeys.SESSION_KEY.value]
            source = resp_msg[ZmqMessageKeys.SOURCE.value]
            path = resp_msg[ZmqMessageKeys.PATH.value]
            try:
                sftp_client = self.sftp_connection_manager.open_sftp_client(source, session_key)
                for item in resp_msg[ZmqMessageKeys.DATA.value]:
                    if item['type'] == 'file':
                        sftp_client.remove(path + sep + item['name'])
                    else:
                        delete_folder(item['name'], path, sftp_client)
            except PermissionError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.strerror})
            except SFTPError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.args[0]})
            else:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.SUCCESS.value})

    def __sftp_transfer_stream_receive_callback__(self, msg):
        """
        This is the callback method when the sftp_transfer_stream socket receives the message. At the end of this method,
        self.sftp_transfer_stream.send_json method should be invoked.
        :param msg: received message by sftp_transfer_stream. The structure of this message is {"from" :
        {"path" : "the absolute path from which the transferred files come", "name" : "host1 or host2",
        "data" : [{"name" : "file name or folder name", "type" : "file or folder"},
        {"name" : "file name or folder name", "type" : "file or folder"}]},
        "to" : {"path" : "the absolute path into which the transferred files will be put", "name" : "host1 or host2"}}
        """
        request_data = jsonapi.loads(msg[0])
        session_key = request_data[ZmqMessageKeys.SESSION_KEY.value]
        sftp_client_from = self.sftp_connection_manager.open_sftp_client(request_data['from']['name'], session_key)
        from_path = request_data['from']['path']

        sftp_client_to = self.sftp_connection_manager.open_sftp_client(request_data['to']['name'], session_key)
        to_path = request_data['to']['path']

        # start a new thread, which is used to transfer files.
        thread = Thread(target=BackendProcess.transfer_data,
                        args=(sftp_client_from, from_path, request_data['from']['data'],
                              sftp_client_to, to_path, request_data['from']['name'],))
        thread.start()
        self.sftp_transfer_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.STARTED.value})

    @staticmethod
    def transfer_data(source_sftp, source_path, transferred_data, destination_sftp, destination_path, channel_name):

        for item in transferred_data:
            if item['type'] == 'file':
                source_sftp.getfo(source_path + sep + item['name'],
                                  destination_sftp.open(destination_path + sep + item['name'], 'w'),
                                  lambda transferred_bytes, total_bytes: update_transmission_progress(
                                      channel_name, transferred_bytes, total_bytes, file_name=item['name']))
            else:
                transfer_folder(item['name'], source_path, source_sftp, destination_path, destination_sftp, channel_name)



