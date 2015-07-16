import stat
import json
from os import sep

from django.views.generic import View
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotAllowed

from paramiko.ssh_exception import SSHException
from paramiko import SFTPError

from . import sftp
from .utils import session_key_required_in_cookie
from .ws import update_transmission_progress


# Create your views here.


class DashboardView(View):

    def get(self, request):
        if not request.session.session_key:
            request.session.save()
            response = render(request, 'dashboard.html')
            sftp.clean_sftp_connections()
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            return response
        else:
            return render(request, 'dashboard.html')


class LoginView(View):

    @session_key_required_in_cookie
    def post(self, request):
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            user_name = request.POST['username']
            otc = request.POST['otc']
            password = request.POST['password']
            hostname = request.POST['hostname']
            port = request.POST['port']
            source = request.POST['source']
            try:
                sftp_client = sftp.create_sftp_client(user_name, password, otc, hostname, port)
            except SSHException as exce:
                context = {"exception": exce.args[0]}
                return JsonResponse(context)
            else:

                sftp.add_sftp_connection(session_key, source, sftp_client, request.session.get_expiry_date())

                try:
                    content = sftp_client.listdir_iter()
                    data_list = []
                    for file_attr in content:
                        if stat.S_ISDIR(file_attr.st_mode):
                            data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                        else:
                            data_list.append([file_attr.filename, file_attr.st_size, "file"])
                except PermissionError as error:
                    return JsonResponse({"exception": error.strerror})
                except SFTPError as error:
                    return JsonResponse({"exception": error.args[0]})
                else:
                    return JsonResponse({"data": data_list})
        else:
            return HttpResponseNotAllowed()


class DisconnectSftpView(View):

    @session_key_required_in_cookie
    def get(self, request):
        if request.is_ajax():
            source = request.GET["source"]
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            sftp.remove_sftp_connection(source, session_key)
            return JsonResponse({"status": "success"})
        else:
            return HttpResponseNotAllowed()


class ListContentView(View):

    @session_key_required_in_cookie
    def get(self, request):
        if request.is_ajax():
            path = request.GET["path"]
            source = request.GET["source"]
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            data_list = []

            if source == 'host1' or source == 'host2':
                sftp_client = sftp.get_sftp_client(source, session_key)
            else:
                # Some exception
                return HttpResponseBadRequest()

            try:
                sftp_client.chdir(path)
                content = sftp_client.listdir_iter()
                for file_attr in content:
                    if stat.S_ISDIR(file_attr.st_mode):
                        data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                    else:
                        data_list.append([file_attr.filename, file_attr.st_size, "file"])
            except PermissionError as error:
                return JsonResponse({"exception": error.strerror})
            except SFTPError as error:
                return JsonResponse({"exception": error.args[0]})
            else:
                return JsonResponse({"data": data_list, "path": path})
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
            sftp_client_from = sftp.get_sftp_client(request_data['from']['name'], session_key)
            from_path = request_data['from']['path']

            sftp_client_to = sftp.get_sftp_client(request_data['to']['name'], session_key)
            to_path = request_data['to']['path']

            try:
                for item in request_data['from']['data']:
                    if item['type'] == 'file':
                        sftp_client_from.getfo(from_path + sep + item['name'],
                                               sftp_client_to.open(to_path + sep + item['name'], 'w'),
                                               lambda transferred_bytes, total_bytes: update_transmission_progress(transferred_bytes, total_bytes, file_name=item['name']))
                    else:
                        # sftp.transfer_folder(item['name'], from_path, sftp_client_from,
                        #                      to_path, sftp_client_to, TransferView._getfo_callback)
                        sftp.transfer_folder(item['name'], from_path, sftp_client_from,
                                             to_path, sftp_client_to)
            except PermissionError as error:
                return JsonResponse({"exception": error.strerror})
            except SFTPError as error:
                return JsonResponse({"exception": error.args[0]})
            else:
                return JsonResponse({"status": "success"})
        else:
            return HttpResponseNotAllowed()

    @staticmethod
    def _getfo_callback(transferred_bytes, total_bytes):
        update_transmission_progress(transferred_bytes, total_bytes)



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
            sftp_client = sftp.get_sftp_client(request_data['source'], session_key)
            path = request_data['path']

            try:
                for item in request_data['data']:
                    if item['type'] == 'file':
                        sftp_client.remove(path + sep + item['name'])
                    else:
                        sftp.delete_folder(item['name'], path, sftp_client)
            except PermissionError as error:
                    return JsonResponse({"exception": error.strerror})
            except SFTPError as error:
                return JsonResponse({"exception": error.args[0]})
            else:
                return JsonResponse({"status": "success"})
        else:
            return HttpResponseNotAllowed()
