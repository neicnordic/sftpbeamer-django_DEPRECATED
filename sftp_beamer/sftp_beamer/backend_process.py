import stat
from os import sep
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from enum import Enum

import zmq
from zmq.eventloop.ioloop import ZMQIOLoop
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from zmq.utils import jsonapi
from paramiko.ssh_exception import SSHException
from paramiko import SFTPError
from paramiko.transport import Transport
from tornado.websocket import WebSocketHandler
from tornado.web import Application, asynchronous

__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '17/Oct/2015'

"""
This is a second process, which is used for managing sftp connections. It contains two parts.
One is the zmq, the other is the web socket handler.
"""


class ZmqMessageValues(Enum):
    CLEAN = 'clean'
    SUCCESS = 'success'
    FAIL = 'fail'
    CONNECT = 'connect'
    LIST = 'list'
    DISCONNECT = 'disconnect'
    STARTED = 'started'
    DELETE = 'delete'


class ZmqMessageKeys(Enum):
    ACTION = 'action'
    RESULT = 'result'
    SESSION_KEY = 'session_key'
    EXCEPTION = 'exception'
    EXPIRY = 'expiry'
    DATA = 'data'
    USERNAME = 'username'
    OTC = 'otc'
    PASSWORD = 'password'
    HOSTNAME = 'hostname'
    PORT = 'port'
    SOURCE = 'source'
    PATH = 'path'


class Zmq:
    """
    This class is to manage the zmq's socket. There is one opening zmq socket,
    which is for managing the synchronous tasks, for example, connecting with sftp server, disconnecting with sftp server,
    listing content and so on.
    """

    def __init__(self, sftp):
        loop = ZMQIOLoop.instance()

        ctx = zmq.Context.instance()
        sftp_connection_socket = ctx.socket(zmq.REP)
        sftp_connection_socket.bind("tcp://*:4444")
        self.sftp_connection_stream = ZMQStream(sftp_connection_socket, loop)
        self.sftp_connection_stream.on_recv(self._sftp_connection_stream_receive_callback)

        self.sftp_connection_manager = sftp

    def _sftp_connection_stream_receive_callback(self, msg):
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
                    if file_attr.filename[0:1] != '.': # Exclude hidden files (files starting with a dot)
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
                        Zmq.delete_folder(item['name'], path, sftp_client)
            except PermissionError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.strerror})
            except SFTPError as error:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.EXCEPTION.value: error.args[0]})
            else:
                self.sftp_connection_stream.send_json({ZmqMessageKeys.RESULT.value: ZmqMessageValues.SUCCESS.value})

    @staticmethod
    def delete_folder(folder_name, path, sftp_client):
        for file_attr in sftp_client.listdir_attr(path + sep + folder_name):
            if stat.S_ISDIR(file_attr.st_mode):
                Zmq.delete_folder(file_attr.filename, path + sep + folder_name, sftp_client)
            else:
                sftp_client.remove(path + sep + folder_name + sep + file_attr.filename)
        sftp_client.rmdir(path + sep + folder_name)


EXECUTOR = ThreadPoolExecutor(max_workers=100)


class FileTransferWebSocket(WebSocketHandler):

    def initialize(self, sftp):
        self.sftp_connection_manager = sftp

    def open(self):
        print("WebSocket opened")

    @asynchronous
    def on_message(self, message):
        data = jsonapi.loads(message)

        def callback(future):
            self.write_message("done")

        EXECUTOR.submit(
            partial(self._transfer_data, data)
        ).add_done_callback(
            lambda future: IOLoop.instance().add_callback(
                partial(callback, future)))

    def on_close(self):
        print("WebSocket closed")

    def _transfer_data(self, data):
        """
        The structure of data is {"session_key" : "sessionid from cookie",
        "from" : {"path" : "the absolute path from which the transferred files come", "name" : "host1 or host2",
        "data" : [{"name" : "file name or folder name", "type" : "file or folder"},
        {"name" : "file name or folder name", "type" : "file or folder"}]},
        "to" : {"path" : "the absolute path into which the transferred files will be put", "name" : "host1 or host2"}}
        """

        session_key = data[ZmqMessageKeys.SESSION_KEY.value]
        sftp_client_from = self.sftp_connection_manager.open_sftp_client(data['from']['name'], session_key)
        from_path = data['from']['path']

        sftp_client_to = self.sftp_connection_manager.open_sftp_client(data['to']['name'], session_key)
        to_path = data['to']['path']

        for item in data['from']['data']:
            if item['type'] == 'file':
                self._transfer_file(from_path, sftp_client_from, to_path, sftp_client_to, item['name'])
            else:
                self._transfer_folder(item['name'], from_path, sftp_client_from, to_path, sftp_client_to)

    def _transfer_folder(self, folder_name, from_path, sftp_client_from, to_path, sftp_client_to, callback=None):
        sftp_client_to.chdir(to_path)
        sftp_client_to.mkdir(folder_name)
        sftp_client_to.chdir(to_path + sep + folder_name)
        to_cwd = sftp_client_to.getcwd()

        sftp_client_from.chdir(from_path + sep + folder_name)
        from_cwd = sftp_client_from.getcwd()
        content = sftp_client_from.listdir_attr(from_cwd)
        for file_attr in content:
            if stat.S_ISDIR(file_attr.st_mode):
                self._transfer_folder(file_attr.filename, from_cwd, sftp_client_from, to_cwd, sftp_client_to)
            else:
                self._transfer_file(from_cwd, sftp_client_from, to_cwd, sftp_client_to, file_attr.filename)

    def _transfer_file(self, from_path, sftp_client_from, to_path, sftp_client_to, file_name, callback=None):
        sftp_client_from.getfo(from_path + sep + file_name,
                               sftp_client_to.open(to_path + sep + file_name, 'w'),
                               lambda transferred_bytes, total_bytes:
                               self.write_message({"file_name": file_name,
                                                   "transferred_bytes": transferred_bytes,
                                                   "total_bytes": total_bytes}))


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


if __name__ == "__main__":
    sftp_connection_manager = SftpConnectionManager()
    Zmq(sftp_connection_manager)
    application = Application([(r"/ws", FileTransferWebSocket, dict(sftp=sftp_connection_manager)), ])
    application.listen(4445)
    IOLoop.current().start()
