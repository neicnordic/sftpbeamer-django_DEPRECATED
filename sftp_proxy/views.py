from django.shortcuts import render
from django.views.generic import View
from django.shortcuts import render

# Create your views here.


class DashboardView(View):

    def get(self, request):
        return render(request, 'dashboard.html')
