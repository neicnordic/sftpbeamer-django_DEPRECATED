import stat
from os import sep
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import zmq
from zmq.eventloop.ioloop import ZMQIOLoop
from zmq.eventloop.zmqstream import ZMQStream
from tornado.ioloop import IOLoop
from zmq.utils import jsonapi
from paramiko.ssh_exception import SSHException
from paramiko import SFTPError
from tornado.websocket import WebSocketHandler
from tornado.web import Application, asynchronous

from sftp_proxy.sftp import SftpConnectionManager, delete_folder
from sftp_proxy.constants import ZmqMessageKeys, ZmqMessageValues

__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '17/Oct/2015'

"""
This is a second process, which is used for managing sftp connections. It contains two parts.
One is the zmq, the other is the web socket handler.
"""


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


if __name__ == "__main__":
    sftp_connection_manager = SftpConnectionManager()
    Zmq(sftp_connection_manager)
    application = Application([(r"/ws", FileTransferWebSocket, dict(sftp=sftp_connection_manager)), ])
    application.listen(4445)
    IOLoop.current().start()
