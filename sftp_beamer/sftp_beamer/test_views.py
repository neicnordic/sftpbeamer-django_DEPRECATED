from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from sftp_beamer.views import DashboardView

# Create your tests here.

class DashboardViewTests(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.view = DashboardView()
        self.session_middleware = SessionMiddleware()

    def test_get_with_a_session(self):
        request = self.request_factory.get('/sftp_beamer/dashboard')
        self.session_middleware.process_request(request)
        request.session.save()
        response = self.view.get(request)
        self.assertEqual(response.status_code, 200)

    # This currently would require to start backend_process.py
    # or possibly mock it in some way, before implementing.
    #def test_get_without_a_session(self):
    #    pass
