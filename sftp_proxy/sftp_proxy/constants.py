from enum import Enum

__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '20/Oct/2015'


class ZmqMessageValues(Enum):
    CLEAN = 'clean'
    SUCCESS = 'success'
    FAIL = 'fail'
    CONNECT = 'connect'
    LIST = 'list'
    DISCONNECT = 'disconnect'
    STARTED = 'started'
    DELETE = 'delete'


class HttpParameters(Enum):
    USERNAME = 'username'
    OTC = 'otc'
    PASSWORD = 'password'
    HOSTNAME = 'hostname'
    PORT = 'port'
    SOURCE = 'source'
    PATH = 'path'


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

