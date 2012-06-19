"""Tests for the ``whoplugins`` module."""

from unittest import TestCase

from pyramid import testing

from lasco.models import DBSession
from lasco.models import initialize_sql


class TestAuthPlugin(TestCase):

    def setUp(self):
        testing.setUp()
        initialize_sql('sqlite:///:memory:')
        self.session = DBSession

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def _make_one(self):
        from lasco.whoplugins import make_auth_plugin
        return make_auth_plugin()

    def test_make_auth_plugin(self):
        from lasco.whoplugins import make_auth_plugin
        from lasco.whoplugins import SQLAlchemyAuthPlugin
        p = make_auth_plugin()
        self.assert_(isinstance(p, SQLAlchemyAuthPlugin))

    def test_implements_IAuthenticator(self):
        from repoze.who.interfaces import IAuthenticator
        p = self._make_one()
        self.assert_(IAuthenticator.providedBy(p))

    def test_authenticate_empty_identity(self):
        p = self._make_one()
        user = p.authenticate(None, {})
        self.assertEqual(user, None)

    def test_authenticate_not_logged_in(self):
        p = self._make_one()
        user = p.authenticate(None, {'login': u'', 'password': ''})
        self.assertEqual(user, None)

    def test_authenticate_unknown_user(self):
        p = self._make_one()
        user = p.authenticate(None, {'login': u'user1', 'password': 'secret'})
        self.assertEqual(user, None)

    def test_authenticate_wrong_password(self):
        from lasco.models import User
        user = User(u'jsmith', u'John Smith', 'password')
        self.session.add(user)
        p = self._make_one()
        got = p.authenticate(None, {'login': u'jsmith', 'password': 'wrong'})
        self.assertEqual(got, None)

    def test_authenticate_success(self):
        from lasco.models import User
        user = User(u'jsmith', u'John Smith', 'password')
        self.session.add(user)
        p = self._make_one()
        got = p.authenticate(None,
                             {'login': u'jsmith', 'password': 'password'})
        self.assertEqual(got, user.id)


class TestMetadataPlugin(TestCase):

    def setUp(self):
        testing.setUp()
        initialize_sql('sqlite:///:memory:')
        self.session = DBSession

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def _make_one(self):
        from lasco.whoplugins import make_md_plugin
        return make_md_plugin()

    def test_make_metadata_plugin(self):
        from lasco.whoplugins import make_md_plugin
        from lasco.whoplugins import SQLAlchemyMetadataPlugin
        p = make_md_plugin()
        self.assert_(isinstance(p, SQLAlchemyMetadataPlugin))

    def test_implements_IMetadataProvider(self):
        from repoze.who.interfaces import IMetadataProvider
        p = self._make_one()
        self.assert_(IMetadataProvider.providedBy(p))

    def test_add_metadata_not_authenticated(self):
        identity = {'repoze.who.userid': None}
        p = self._make_one()
        p.add_metadata(None, identity)
        self.assertEqual(identity['login'], None)
        self.assertEqual(identity['fullname'], None)
        self.assertEqual(identity['id'], None)

    def test_add_metadata_authenticated(self):
        from lasco.models import User
        user = User(u'jsmith', u'John Smith', 'password')
        self.session.add(user)
        self.session.flush()  # set user.id
        identity = {'repoze.who.userid': user.id}
        p = self._make_one()
        p.add_metadata(None, identity)
        self.assertEqual(identity['login'], user.login)
        self.assertEqual(identity['fullname'], user.fullname)
        self.assertEqual(identity['id'], user.id)
