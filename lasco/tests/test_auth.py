"""Test login/lgout views."""

from unittest import TestCase

from lasco.tests.base import LascoTestCase


class BaseTestCase(LascoTestCase):

    def setUp(self):
        from lasco.auth import setup_who_api_factory
        LascoTestCase.setUp(self)
        class DummyWhoApi(object):
            def __init__(self, environ):
                self.environ = environ
            def authenticate(self):
                identity = self.environ.get('repoze.who.identity')
                if identity is None:
                    return identity
                return identity.copy()
        setup_who_api_factory(self.config, None, None, DummyWhoApi)

    def _make_request(self, post=None, get=None, cookies=None):
        from pyramid.testing import DummyRequest
        if post is not None:
            from webob.multidict import MultiDict
            post = MultiDict(post)
        req = DummyRequest(post=post, params=get, cookies=cookies)
        return req


class TestGetUserRole(BaseTestCase):

    def setUp(self):
        from lasco.models import Album
        BaseTestCase.setUp(self)
        self.gallery = self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a', u'Album')
        self.album = self.session.query(Album).one()

    def _call_fut(self, *args, **kwargs):
        from lasco.auth import get_user_role
        return get_user_role(*args, **kwargs)

    def _make_request(self):
        from pyramid.testing import DummyRequest
        return DummyRequest()

    def fake_authentication(self, request, login):
        from lasco.models import User
        user = self.session.query(User).filter_by(login=login).one()
        request.environ['repoze.who.identity'] = dict(
            login=login,
            id=user.id,
            fullname=user.fullname)

    def test_anonymous(self):
        request = self._make_request()
        role = self._call_fut(request, 'whatever', 'whatever')
        self.assertEqual(role, None)

    def test_no_role(self):
        request = self._make_request()
        role = self._call_fut(request, self.session, 'g', 'a')
        self.assertEqual(role, None)

    def test_role_in_gallery(self):
        from lasco.auth import ROLE_GALLERY_ADMIN
        request = self._make_request()
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.add_gallery_admin('g', u'user')
        role = self._call_fut(request,
                              self.session,
                              gallery=self.gallery)
        self.assertEqual(role, ROLE_GALLERY_ADMIN)

    def test_role_in_album(self):
        from lasco.auth import ROLE_ALBUM_VIEWER
        request = self._make_request()
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.add_album_viewer('g', 'a', u'user')
        role = self._call_fut(request,
                              self.session,
                              gallery=self.gallery,
                              album=self.album)
        self.assertEqual(role, ROLE_ALBUM_VIEWER)


class TestGetUserMetadata(TestCase):

    def setUp(self):
        from pyramid.testing import setUp
        from lasco.auth import setup_who_api_factory
        class DummyWhoApi(object):
            def __init__(self, environ):
                self.environ = environ
            def authenticate(self):
                identity = self.environ.get('repoze.who.identity')
                if identity is None:
                    return identity
                return identity.copy()
        self.config = setUp()
        setup_who_api_factory(self.config, None, None, dummy=DummyWhoApi)

    def tearDown(self):
        from pyramid.testing import tearDown
        tearDown()

    def _call_fut(self, request):
        from lasco.auth import get_user_metadata
        return get_user_metadata(request)

    def test_anonymous(self):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        self.assertEqual(self._call_fut(request), {})

    def test_authenticated(self):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        identity = dict(
            login='jsmith',
            user_id=1,
            fullname='John Smith')
        request.environ['repoze.who.identity'] = identity
        self.assertEqual(self._call_fut(request), identity)

    def test_result_is_cached_in_request(self):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        identity = dict(
            login='jsmith',
            user_id=1,
            fullname='John Smith')
        request.environ['repoze.who.identity'] = identity
        got_first = self._call_fut(request)
        self.assertEqual(got_first, identity)
        got_second = self._call_fut(request)
        self.assert_(got_first is got_second)


class TestLoginForm(BaseTestCase):

    template_under_test = 'templates/login.pt'

    def test_login_form_first_display(self):
        from lasco.views.auth import login_form
        request = self._make_request()
        res = login_form(request)
        self.assertEqual(res['error_msg'], None)

    def test_login_form_after_failure(self):
        from lasco.views.auth import login_form
        request = self._make_request(post={'login': u'jsmith'})
        res = login_form(request, failed=True)
        self.assertEqual(res['error_msg'], u'Wrong user name or password.')
        self.assertEqual(res['login'], u'jsmith')


class TestLogin(BaseTestCase):

    template_under_test = 'templates/login.pt'

    def test_login_valid_credentials(self):
        from lasco.auth import setup_who_api_factory
        from lasco.views.auth import login
        class AlwaysLogsIn(object):
            def __init__(self, environ):
                pass
            def login(self, credentials):
                return True, {}
        setup_who_api_factory(self.config, None, None, AlwaysLogsIn)
        request = self._make_request(post={'login': u'jsmith',
                                           'password': u'password',
                                           'next': 'http://next'})
        response = login(request)
        self.assertEqual(response.status, '303 See Other')
        self.assertEqual(response.location, 'http://next')

    def test_login_try_invalid_credentials(self):
        from lasco.auth import setup_who_api_factory
        from lasco.views.auth import login
        class NeverLogsIn(object):
            def __init__(self, environ):
                pass
            def login(self, credentials):
                return False, {}
            def authenticate(self):  # required by 'login_form'
                return None
        setup_who_api_factory(self.config, None, None, NeverLogsIn)
        request = self._make_request(post={'login': u'jsmith',
                                           'password': u'password',
                                           'next': 'http://next'})
        res = login(request)
        self.assertEqual(res['error_msg'], u'Wrong user name or password.')
        self.assertEqual(res['login'], u'jsmith')


class TestLogout(BaseTestCase):

    def test_logout(self):
        from lasco.auth import setup_who_api_factory
        from lasco.views.auth import logout
        headers = {'logout-marker': 'marker'}
        class DummyWhoApi(object):
            def __init__(self, environ):
                pass
            def logout(self):
                return headers
        setup_who_api_factory(self.config, None, None, DummyWhoApi)
        request = self._make_request()
        request.application_url = 'http://application.url'
        response = logout(request)
        self.assertEqual(response.status, '303 See Other')
        self.assertEqual(response.location, request.application_url)
        self.assertEqual(response.headers['logout-marker'], 'marker')


class TestForbidden(TestCase):

    def test_forbidden(self):
        from urllib import quote_plus
        from pyramid.testing import DummyRequest
        from lasco.views.auth import forbidden
        request = DummyRequest()
        request.url = 'http://request.url'
        request.application_url = 'http://application.url'
        response = forbidden(request)
        self.assertEqual(response.status, '303 See Other')
        expected = 'http://application.url/login_form?next=%s' % quote_plus(
            request.url)
        self.assertEqual(response.location, expected)
