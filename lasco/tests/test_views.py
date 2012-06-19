"""Test for Lasco views and utilites for views."""

from pyramid.testing import DummyRequest as BaseRequest
from pyramid.url import URLMethodsMixin

from lasco.tests.base import LascoTestCase


class DummyWhoApiFactory(object):

    def __init__(self, environ):
        self.environ = environ

    def authenticate(self):
        return self.environ.get('repoze.who.identity')


class DummyRequest(BaseRequest, URLMethodsMixin):
    pass


class LascoViewsTestCase(LascoTestCase):

    def setUp(self):
        from lasco.auth import setup_who_api_factory
        from lasco.app import set_config
        LascoTestCase.setUp(self)
        set_config(self.config)
        self.config.testing_add_renderer('templates/layout.pt')
        setup_who_api_factory(self.config, None, None, DummyWhoApiFactory)

    def _make_request(self, matchdict=None, post=None, get=None, cookies=None):
        if post is not None:
            from webob.multidict import MultiDict
            post = MultiDict(post)
        req = DummyRequest(post=post, params=get, cookies=cookies)
        if matchdict:
            req.matchdict = matchdict
        return req

    def fake_authentication(self, request, login):
        from lasco.models import User
        user = self.session.query(User).filter_by(login=login).one()
        request.environ['repoze.who.identity'] = dict(
            login=login,
            id=user.id,
            fullname=user.fullname)


class TestLascoIndex(LascoViewsTestCase):

    def setUp(self):
        LascoViewsTestCase.setUp(self)
        self.add_gallery('g1', u'Gallery 1')
        self.add_gallery('g2', u'Gallery 2')
        self.add_album('g2', 'a1', u'Album 1')

    def _call_fut(self, request):
        from lasco.views.gallery import lasco_index
        return lasco_index(request)

    def test_anonymous(self):
        request = self._make_request()
        res = self._call_fut(request)
        self.assertEqual(res['galleries'], ())

    def test_no_role(self):
        request = self._make_request()
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(list(res['galleries']), [])

    def test_role_in_gallery(self):
        request = self._make_request()
        self.add_user(u'user')
        self.add_gallery_admin('g1', u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual([g.name for g in res['galleries']], [u'g1'])

    def test_role_in_album(self):
        request = self._make_request()
        self.add_user(u'user')
        self.add_album_viewer('g2', 'a1', u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual([g.name for g in res['galleries']], [u'g2'])

    def test_role_in_album_and_gallery(self):
        request = self._make_request()
        self.add_user(u'user')
        self.add_gallery_admin('g1', u'user')
        self.add_album_viewer('g2', 'a1', u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(sorted([g.name for g in res['galleries']]),
                         [u'g1', u'g2'])


class TestGalleryIndex(LascoViewsTestCase):

    def setUp(self):
        LascoViewsTestCase.setUp(self)
        self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a1', u'Album 1')

    def _call_fut(self, request):
        from lasco.views.gallery import gallery_index
        return gallery_index(request)

    def test_non_existent(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'non-existent'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_no_role(self):
        from pyramid.httpexceptions import HTTPForbidden
        matchdict = {'gallery_name': 'g'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.assertRaises(HTTPForbidden, self._call_fut, request)

    def test_role_in_gallery(self):
        matchdict = {'gallery_name': 'g'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.add_gallery_admin('g', u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(res['gallery'].name, 'g')
        self.assertEqual([a.name for a in res['albums']], [u'a1'])

    def test_role_in_album(self):
        matchdict = {'gallery_name': 'g'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.add_album_viewer('g', 'a1', u'user')
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(res['gallery'].name, 'g')
        self.assertEqual([a.name for a in res['albums']], [u'a1'])


class TestAlbumIndex(LascoViewsTestCase):

    def setUp(self):
        LascoViewsTestCase.setUp(self)
        self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a', u'Album')

    def _call_fut(self, request):
        from lasco.views.album import album_index
        return album_index(request)

    def test_non_existent_gallery(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'non-existent',
                     'album_name': 'whatever'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_non_existent_album(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'g',
                     'album_name': 'non-existent'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_no_role(self):
        from pyramid.httpexceptions import HTTPForbidden
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.assertRaises(HTTPForbidden, self._call_fut, request)

    def test_base(self):
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        self.fake_authentication(request, u'user')
        self.config.add_settings({'lasco.pictures_per_page': 8})
        res = self._call_fut(request)
        self.assertEqual(res['gallery'].name, 'g')
        self.assertEqual(res['album'].name, 'a')
        self.assertEqual([p.path for p in res['pictures']],
                         [u'data/w_exif.jpg', u'data/wo_exif.jpg'])

    def test_previous_url(self):
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a'}
        request = self._make_request(matchdict=matchdict,
                                     get={'page': 2})
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        self.fake_authentication(request, u'user')
        self.config.add_settings({'lasco.pictures_per_page': 1})
        res = self._call_fut(request)
        prev_url = res['api'].previous_url
        self.assertTrue(prev_url.endswith('galleries/g/a?page=1'))
        self.assertTrue('next_url' not in res)

    def test_next_url(self):
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        self.fake_authentication(request, u'user')
        self.config.add_settings({'lasco.pictures_per_page': 1})
        res = self._call_fut(request)
        next_url = res['api'].next_url
        self.assertTrue(next_url.endswith('galleries/g/a?page=2'))
        self.assertTrue('previous_url' not in res)


class TestPictureInAlbum(LascoViewsTestCase):

    def setUp(self):
        from lasco.models import Picture
        LascoViewsTestCase.setUp(self)
        self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a', u'Album')
        self.picture = self.session.query(Picture).first()

    def _call_fut(self, request):
        from lasco.views.picture import picture_in_album
        return picture_in_album(request)

    def test_non_existent_gallery(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'non-existent',
                     'album_name': 'whatever'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_non_existent_album(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'g',
                     'album_name': 'non-existent'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_non_existent_picture(self):
        from pyramid.httpexceptions import HTTPNotFound
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a',
                     'picture_id': '999'}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.add_album_viewer('g', 'a', u'user')
        self.assertRaises(HTTPNotFound, self._call_fut, request)

    def test_no_role(self):
        from pyramid.httpexceptions import HTTPForbidden
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a',
                     'picture_id': str(self.picture.id)}
        request = self._make_request(matchdict=matchdict)
        self.add_user(u'user')
        self.fake_authentication(request, u'user')
        self.assertRaises(HTTPForbidden, self._call_fut, request)

    def test_base_album_viewer_first_picture(self):
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a',
                     'picture_id': str(self.picture.id)}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(res['gallery'].name, 'g')
        self.assertEqual(res['album'].name, 'a')
        self.assertEqual(res['picture'].path, 'data/w_exif.jpg')
        self.assertEqual(res['picture_index'], 0)
        self.assertEqual(res['previous_id'], None)
        self.assertEqual(res['next_id'], 1 + self.picture.id)
        self.assertFalse(res['can_edit'])

    def test_base_album_viewer_last_picture(self):
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a',
                     'picture_id': str(1 + self.picture.id)}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertEqual(res['previous_id'], self.picture.id)
        self.assertEqual(res['next_id'], None)

    def test_base_gallery_admin(self):
        # The only difference is that 'can_edit' is True.
        from lasco.models import Picture
        self.add_user(u'user')
        self.add_gallery_admin('g', u'user')
        picture_id = self.session.query(Picture).first().id
        matchdict = {'gallery_name': 'g',
                     'album_name': 'a',
                     'picture_id': str(picture_id)}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        res = self._call_fut(request)
        self.assertTrue(res['can_edit'])


class TestPictureAsImage(LascoViewsTestCase):

    def setUp(self):
        from lasco.models import Picture
        LascoViewsTestCase.setUp(self)
        self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a', u'Album')
        self.picture = self.session.query(Picture).first()

    def _call_fut(self, request):
        from lasco.views.picture import picture_as_image
        return picture_as_image(request)

    def _make_request(self, **kwargs):
        # We need something a little less dummy than the usual
        # DummyRequest to test 'picture_as_image()', as it passes the
        # request to 'paste.FileApp'.
        from pyramid.testing import DummyRequest
        from webob.request import Request
        from webob.response import Response
        class SillyRequest(DummyRequest):
            ResponseClass = Response
        SillyRequest.get_response = Request.get_response.im_func
        SillyRequest.call_application = Request.call_application.im_func
        SillyRequest.is_body_seekable = Request.is_body_seekable
        kwargs['environ'] = {
            'wsgi.url_scheme': 'http',
            'wsgi.version': (1, 0),
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080',
            'REQUEST_METHOD': 'GET',
            }
        return SillyRequest(**kwargs)

    def test_anonymous(self):
        from pyramid.httpexceptions import HTTPForbidden
        matchdict = {'picture_id': '1'}
        request = self._make_request(matchdict=matchdict)
        self.assertRaises(HTTPForbidden, self._call_fut, request)

    def test_no_role(self):
        from pyramid.httpexceptions import HTTPForbidden
        self.add_user(u'user')
        matchdict = {'picture_id': '1'}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        self.assertRaises(HTTPForbidden, self._call_fut, request)

    def test_non_existent_picture(self):
        from pyramid.httpexceptions import HTTPForbidden
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        matchdict = {'picture_id': '999'}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        self.assertRaises(HTTPForbidden, self._call_fut, request)  # sic

    def test_base(self):
        import os.path
        from email.utils import formatdate
        self.add_user(u'user')
        self.add_album_viewer('g', 'a', u'user')
        matchdict = {'picture_id': unicode(self.picture.id)}
        request = self._make_request(matchdict=matchdict)
        self.fake_authentication(request, u'user')
        base_path = os.path.dirname(__file__)
        self.config.add_settings({'lasco.pictures_base_path': base_path})
        response = self._call_fut(request)
        headers = response.headers
        file_path = os.path.join(os.path.dirname(__file__),
                                 'data',
                                 'w_exif.jpg')
        lmt = os.path.getmtime(file_path)
        lmt = formatdate(lmt, usegmt=True)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(headers['Content-Length'], '5756')
        self.assertTrue(headers['Content-Type'].startswith('image/jpeg'))
        self.assertEqual(headers['Last-Modified'], lmt)
        self.assertEqual(response.body, open(file_path).read())


class TestPictureUpdateCaptionAndLocation(LascoTestCase):

    def setUp(self):
        from lasco.auth import setup_who_api_factory
        from lasco.models import Picture
        LascoTestCase.setUp(self)
        setup_who_api_factory(self.config, None, None, DummyWhoApiFactory)
        self.add_gallery('g', u'Gallery')
        self.add_album('g', 'a', u'Album')
        self.picture = self.session.query(Picture).first()

    def _make_request(self, matchdict, post):
        from pyramid.testing import DummyRequest
        req = DummyRequest(post=post)
        req.matchdict = matchdict
        return req

    def fake_authentication(self, request, login):
        from lasco.models import User
        user = self.session.query(User).filter_by(login=login).one()
        request.environ['repoze.who.identity'] = dict(
            login=login,
            id=user.id,
            fullname=user.fullname)

    def _call_fut(self, request):
        from lasco.views.picture import ajax_update
        return ajax_update(request)

    def test_not_allowed(self):
        from pyramid.httpexceptions import HTTPForbidden
        matchdict = {'picture_id': unicode(self.picture.id)}
        post = {'caption': u'New caption',
                'location': u'New location'}
        req = self._make_request(matchdict, post)
        self.assertRaises(HTTPForbidden, self._call_fut, req)

    def test_not_empty_values(self):
        matchdict = {'picture_id': unicode(self.picture.id)}
        post = {'caption': u'New caption', 'location': u'New location'}
        req = self._make_request(matchdict, post)
        self.add_user(u'admin')
        self.add_gallery_admin('g', u'admin')
        self.fake_authentication(req, u'admin')
        expected = u' - '.join(
            (post['caption'],
             post['location'],
             self.picture.date.strftime('%d %b %Y %H:%M:%S')))
        self.assertEqual(self._call_fut(req), {'pic_info': expected})
        self.assertEqual(self.picture.caption, post['caption'])
        self.assertEqual(self.picture.location, post['location'])

    def test_empty_values(self):
        matchdict = {'picture_id': unicode(self.picture.id)}
        post = {'caption': u'', 'location': u''}
        req = self._make_request(matchdict, post)
        self.add_user(u'admin')
        self.add_gallery_admin('g', u'admin')
        self.fake_authentication(req, u'admin')
        expected = self.picture.date.strftime('%d %b %Y %H:%M:%S')
        self.assertEqual(self._call_fut(req), {'pic_info': expected})
        self.assertEqual(self.picture.caption, post['caption'])
        self.assertEqual(self.picture.location, post['location'])


class TestHelp(LascoViewsTestCase):

    def test_help(self):
        from lasco.views.gallery import help
        request = self._make_request()
        # Just call the view handler: if there is no error, we are
        # fine.
        help(request)


class TestPreferences(LascoViewsTestCase):

    def test_preferences(self):
        from lasco.i18n import LOCALE_COOKIE_NAME
        from lasco.views.preferences import AVAILABLE_THEMES
        from lasco.views.preferences import preferences
        self.config.add_settings({'lasco.available_languages': 'en de'})
        request = self._make_request(cookies={LOCALE_COOKIE_NAME: 'de'})
        res = preferences(request)
        self.assertEqual(res['current_lang'], 'de')
        self.assertEqual(res['available_langs'], ['en', 'de'])
        self.assertEqual(res['current_theme'], 'default')
        self.assertEqual(res['available_themes'], AVAILABLE_THEMES)

    def test_set_lang_not_default(self):
        from lasco.i18n import LOCALE_COOKIE_NAME
        from lasco.views.preferences import set_lang
        request = self._make_request(post=dict({'lang': 'de'}))
        self.config.add_settings({'lasco.available_languages': 'en de'})
        response = set_lang(request)
        expected_cookie = '%s=de; Path=/' % LOCALE_COOKIE_NAME
        self.assertEqual(response.headers['Set-Cookie'], expected_cookie)

    def test_set_color_theme_not_default(self):
        from lasco.views.preferences import set_color_theme
        request = self._make_request(get={'color_theme': 'white'})
        response = set_color_theme(request)
        self.assertEqual(
            response.headers['Set-Cookie'], 'color_theme=white; Path=/')

    def test_set_color_theme_back_to_default(self):
        from lasco.views.preferences import set_color_theme
        request = self._make_request(post={'color_theme': 'default'},
                                     cookies={'color_theme': 'white'})
        response = set_color_theme(request)
        self.assertTrue('color_theme=;' in response.headers['Set-Cookie'])


class TestNotFound(LascoViewsTestCase):

    def test_not_found(self):
        from lasco.views.gallery import not_found
        request = self._make_request()
        res = not_found(request)
        self.assertEqual(request.response.status, '404 Not Found')
        self.assertEqual(res['resource_url'], request.url)


class TestTemplateAPI(LascoViewsTestCase):

    def add_user(self, login, fullname=u''):
        from lasco import api as lascoapi
        lascoapi.add_user(self.session, login, fullname, u'password')

    def fake_authentication(self, request, login):
        from lasco.models import User
        user = self.session.query(User).filter_by(login=login).one()
        request.environ['repoze.who.identity'] = dict(
            login=login,
            id=user.id,
            fullname=user.fullname)

    def _make_one(self, request=None, url='', referrer='', title=''):
        from pyramid.testing import DummyRequest
        from lasco.views.utils import TemplateAPI
        if request is None:
            request = DummyRequest()
            request.environ['HTTP_REFERER'] = referrer
            request.url = url
        return TemplateAPI(request, title)

    def test_base(self):
        api = self._make_one(url='http://exemple.com/the-url',
                             referrer='My referrer',
                             title='My title')
        self.assertTrue(api.layout is not None)
        self.assertEqual(api.page_title, 'My title')
        self.assertEqual(api.referrer, 'My referrer')
        self.assertEqual(api.here_url, 'http://exemple.com/the-url')
        self.assertTrue(api.show_footer)
        self.assertEqual(api.user_fullname, None)

    def test_has_cn(self):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        self.add_user(u'jsmith', u'John Smith')
        self.fake_authentication(request, u'jsmith')
        api = self._make_one(request=request, title='My title')
        self.assertEqual(api.user_fullname, u'John Smith')

    def test_no_login_link_in_login_form(self):
        api = self._make_one(url='http://exemple.com/login_form?next=foo')
        self.assertTrue(not api.show_footer)
        api = self._make_one(url='http://exemple.com/login')
        self.assertTrue(not api.show_footer)

    def test_route_url(self):
        class FakeRequest(DummyRequest):
            def __init__(self, *args, **kwargs):
                DummyRequest.__init__(self, *args, **kwargs)
                self.called = []
            def route_url(self, route_name, *args, **kwargs):
                self.called.append((route_name, args, kwargs))
        request = FakeRequest()
        api = self._make_one(request)
        api.route_url('route_name', foo=1, bar=2)
        self.assertEqual(request.called,
                         [('route_name', (), {'foo': 1, 'bar': 2})])

    def test_static_url(self):
        class FakeRequest(DummyRequest):
            def __init__(self, *args, **kwargs):
                DummyRequest.__init__(self, *args, **kwargs)
                self.called = []
            def static_url(self, path):
                self.called.append(path)
        request = FakeRequest()
        api = self._make_one(request)
        api.static_url('foo')
        api.static_url('spec:bar')
        self.assertEqual(request.called, ['lasco:static/foo', 'spec:bar'])
