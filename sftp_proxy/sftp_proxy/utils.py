__author__ = 'Xiaxi Li'
__email__ = 'xiaxi.li@ii.uib.no'
__date__ = '10/Jul/2015'


def session_key_required_in_cookie(func):
    def func_wrapper(self, request):
        from django.conf import settings
        if settings.SESSION_COOKIE_NAME in request.COOKIES:
            return func(self, request)
        else:
            from django.http import JsonResponse
            context = {"error": "Timeout, please login again"}
            return JsonResponse(context)
    return func_wrapper
