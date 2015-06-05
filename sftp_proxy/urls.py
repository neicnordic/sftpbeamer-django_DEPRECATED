__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '05/Jun/2015'

from django.conf.urls import url
from sftp_proxy.views import DashboardView


urlpatterns = [
    url(r'^dashboard', DashboardView.as_view(), name='dashboard')
]