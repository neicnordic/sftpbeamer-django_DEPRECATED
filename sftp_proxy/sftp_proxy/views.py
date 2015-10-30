import json
from os import sep

from django.views.generic import View
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotAllowed

import zmq

from .utils import session_key_required_in_cookie
from .constants import ZmqMessageKeys, ZmqMessageValues, HttpParameters

# Create your views here.

zmq_ctx = zmq.Context.instance()
sftp_connection_socket_address = 'tcp://localhost:4444'
sftp_transfer_socket_address = 'tcp://localhost:4445'


def create_sftp_connection_socket():
    socket = zmq_ctx.socket(zmq.REQ)
    socket.connect(sftp_connection_socket_address)
    return socket


def create_sftp_transfer_socket():
    socket = zmq_ctx.socket(zmq.REQ)
    socket.connect(sftp_transfer_socket_address)
    return socket


class DashboardView(View):

    def get(self, request):
        if not request.session.session_key:
            request.session.save()
            response = render(request, 'dashboard.html')
            socket = create_sftp_connection_socket()
            socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.CLEAN.value})  # clean the sftp connections
            resp_msg = socket.recv_json()
            socket.close()
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            return response
        else:
            return render(request, 'dashboard.html')


class LoginView(View):

    @session_key_required_in_cookie
    def post(self, request):
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            user_name = request.POST[HttpParameters.USERNAME.value]
            otc = request.POST[HttpParameters.OTC.value]
            password = request.POST[HttpParameters.PASSWORD.value]
            hostname = request.POST[HttpParameters.HOSTNAME.value]
            port = request.POST[HttpParameters.PORT.value]
            source = request.POST[HttpParameters.SOURCE.value]
            expiry_date = request.session.get_expiry_date()

            socket = create_sftp_connection_socket()
            socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.CONNECT.value,
                              ZmqMessageKeys.SESSION_KEY.value: session_key,
                              ZmqMessageKeys.USERNAME.value: user_name,
                              ZmqMessageKeys.OTC.value: otc,
                              ZmqMessageKeys.PASSWORD.value: password,
                              ZmqMessageKeys.HOSTNAME.value: hostname,
                              ZmqMessageKeys.PORT.value: port,
                              ZmqMessageKeys.SOURCE.value: source,
                              ZmqMessageKeys.EXPIRY.value: expiry_date.timestamp()})
            resp_msg = socket.recv_json()
            if ZmqMessageKeys.EXCEPTION.value in resp_msg:
                socket.close()
                return JsonResponse(resp_msg)
            if ZmqMessageKeys.RESULT.value in resp_msg \
                    and resp_msg[ZmqMessageKeys.RESULT.value] == ZmqMessageValues.SUCCESS.value:
                socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.LIST.value,
                                  ZmqMessageKeys.SESSION_KEY.value: session_key,
                                  ZmqMessageKeys.SOURCE.value: source})
                resp_msg = socket.recv_json()
                socket.close()
                if ZmqMessageKeys.EXCEPTION.value in resp_msg:
                    return JsonResponse(resp_msg)
                if ZmqMessageKeys.DATA.value in resp_msg:
                    response = JsonResponse(resp_msg)
                    response.set_cookie(source, user_name)
                    return response
        else:
            return HttpResponseNotAllowed()


class DisconnectSftpView(View):

    @session_key_required_in_cookie
    def get(self, request):
        if request.is_ajax():
            source = request.GET["source"]
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]

            socket = create_sftp_connection_socket()
            socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.DISCONNECT.value,
                              ZmqMessageKeys.SOURCE.value: source,
                              ZmqMessageKeys.SESSION_KEY: session_key})
            resp_msg = socket.recv_json()
            socket.close()
            if ZmqMessageKeys.RESULT.value in resp_msg \
                    and resp_msg[ZmqMessageKeys.RESULT.value] == ZmqMessageValues.SUCCESS.value:
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse({"status": "fail"})
        else:
            return HttpResponseNotAllowed()


class ListContentView(View):

    @session_key_required_in_cookie
    def get(self, request):
        if request.is_ajax():
            path = request.GET["path"]
            source = request.GET["source"]
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]

            if source != 'host1' and source != 'host2':
                return HttpResponseBadRequest()

            socket = create_sftp_connection_socket()
            socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.LIST.value,
                              ZmqMessageKeys.SESSION_KEY.value: session_key,
                              ZmqMessageKeys.SOURCE.value: source,
                              ZmqMessageKeys.PATH.value: path})
            resp_msg = socket.recv_json()

            socket.close()
            if ZmqMessageKeys.EXCEPTION.value in resp_msg:
                return JsonResponse(resp_msg)
            if ZmqMessageKeys.DATA.value in resp_msg:
                resp_msg[ZmqMessageKeys.PATH.value] = path
                return JsonResponse(resp_msg)
        else:
            return HttpResponseNotAllowed()


class TransferView(View):

    @session_key_required_in_cookie
    def post(self, request):
        """
        The json structure received by this method is {"from" : {"path" : "the absolute path
        from which the transferred files come", "name" : "host1 or host2",
        "data" : [{"name" : "file name or folder name", "type" : "file or folder"},
        {"name" : "file name or folder name", "type" : "file or folder"}]},
        "to" : {"path" : "the absolute path into which the transferred files will be put", "name" : "host1 or host2"}}
        """
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            request_data = json.loads(request.body.decode('utf-8'))

            request_data[ZmqMessageKeys.SESSION_KEY.value] = session_key
            socket = create_sftp_transfer_socket()
            socket.send_json(request_data)
            resp_msg = socket.recv_json()
            socket.close()
            return JsonResponse({"status": "started"})
        else:
            return HttpResponseNotAllowed()


class DeleteView(View):

    @session_key_required_in_cookie
    def post(self, request):
        """
        The json structure received by this method is {"source": "host1 or host2", "path": "the parent path of the files
        and folders to be deleted", "data": [{"name": "file name or folder name", "type": "file or folder"},
        {"name": "file name or folder name", "type": "file or folder"}]}
        """
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            request_data = json.loads(request.body.decode('utf-8'))
            source = request_data['source']
            path = request_data['path']
            data = request_data['data']

            socket = create_sftp_connection_socket()
            socket.send_json({ZmqMessageKeys.ACTION.value: ZmqMessageValues.DELETE.value,
                              ZmqMessageKeys.SESSION_KEY.value: session_key,
                              ZmqMessageKeys.SOURCE.value: source,
                              ZmqMessageKeys.PATH.value: path,
                              ZmqMessageKeys.DATA.value: data})
            resp_msg = socket.recv_json()
            socket.close()
            return JsonResponse(resp_msg)
        else:
            return HttpResponseNotAllowed()
