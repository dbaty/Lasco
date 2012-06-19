"""Tests for the ``run`` module."""

from unittest import TestCase


class TestMakeApp(TestCase):

    def test_make_app(self):
        import os.path
        from pyramid.router import Router
        from lasco.app import make_app
        from lasco.tests.base import TESTING_DB
        global_settings = {'here': 'here'}
        auth_config = os.path.join(os.path.dirname(__file__),
                                   'data',
                                   'who.ini')
        settings = {'lasco.db_string': TESTING_DB,
                    'lasco.auth_config': auth_config}
        wsgi_app = make_app(global_settings, **settings)
        self.assert_(isinstance(wsgi_app, Router))
