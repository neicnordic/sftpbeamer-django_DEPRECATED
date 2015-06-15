import stat,json

from django.views.generic import View
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseBadRequest, JsonResponse, HttpResponseNotAllowed

from paramiko.sftp_attr import SFTPAttributes

from . import sftp

# Create your views here.


class DashboardView(View):

    def get(self, request):
        if not request.session.session_key:
            request.session.save()
            response = render(request, 'dashboard.html')
            response.set_cookie(settings.SESSION_COOKIE_NAME, request.session.session_key)
            return response
        else:
            return render(request, 'dashboard.html')


class LoginView(View):

    def post(self, request):
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            user_name = request.POST['username']
            otc = request.POST['otc']
            password = request.POST['password']
            source = request.POST['source']
            sftp_client = sftp.create_sftp_client(source, user_name, password, otc)
            if source == 'tsd':
                sftp.TSD_CONNECTIONS[session_key] = sftp_client

            if source == 'mosler':
                sftp.MOSLER_CONNECTIONS[session_key] = sftp_client

            content = sftp_client.listdir_iter()
            data_list = []
            for file_attr in content:
                if stat.S_ISDIR(file_attr.st_mode):
                    data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                else:
                    data_list.append([file_attr.filename, file_attr.st_size, "file"])
            context = {"data": data_list}
            return JsonResponse(context)
        else:
            return HttpResponseNotAllowed()

class ListContentView(View):

    def get(self, request):
        if request.is_ajax():
            path = request.GET["path"]
            source = request.GET["source"]
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            data_list = []
            if source == 'tsd':
                sftp_client = sftp.TSD_CONNECTIONS[session_key]
                sftp_client.chdir(path)
                content = sftp_client.listdir_iter()
                for file_attr in content:
                    if stat.S_ISDIR(file_attr.st_mode):
                        data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                    else:
                        data_list.append([file_attr.filename, file_attr.st_size, "file"])

            if source == 'mosler':
                sftp_client = sftp.MOSLER_CONNECTIONS[session_key]
                sftp_client.chdir(path)
                content = sftp_client.listdir_iter()
                for file_attr in content:
                    if stat.S_ISDIR(file_attr.st_mode):
                        data_list.append([file_attr.filename, file_attr.st_size, "folder"])
                    else:
                        data_list.append([file_attr.filename, file_attr.st_size, "file"])

            context = {"data": data_list, "path": path}
            return JsonResponse(context)
        else:
            return HttpResponseNotAllowed()

class TransferView(View):

    def post(self, request):
        if request.is_ajax():
            session_key = request.COOKIES[settings.SESSION_COOKIE_NAME]
            request_data = json.loads(request.body.decode('utf-8'))
            sftp_client_from = sftp.get_sftp_client(request_data['from']['name'], session_key)
            from_path = request_data['from']['path']

            sftp_client_to = sftp.get_sftp_client(request_data['to']['name'], session_key)
            to_path = request_data['to']['path']

            for item in request_data['from']['data']:
                if item['type'] == 'file':
                    sftp_client_from.getfo(from_path + '/' + item['name'],
                                           sftp_client_to.open(to_path + '/' + item['name'], 'w'))

            return JsonResponse({"status": "success"})
        else:
            return HttpResponseNotAllowed()
