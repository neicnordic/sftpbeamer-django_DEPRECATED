__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '05/Jun/2015'

from django.conf.urls import url
from sftp_beamer.views import DashboardView, LoginView, ListContentView, TransferView, DeleteView, DisconnectSftpView


urlpatterns = [
    url(r'^dashboard$', DashboardView.as_view(), name='dashboard'),
    url(r'^dashboard/login$', LoginView.as_view(), name='login'),
    url(r'^dashboard/list$', ListContentView.as_view(), name='list'),
    url(r'^dashboard/transfer$', TransferView.as_view(), name='transfer'),
    url(r'^dashboard/delete$', DeleteView.as_view(), name='delete'),
    url(r'^dashboard/disconnect$', DisconnectSftpView.as_view(), name='disconnect')
]
