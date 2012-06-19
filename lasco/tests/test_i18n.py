"""Tests for the i18n helper functions."""

from unittest import TestCase


_no_header = object()


class TestI18n(TestCase):

    def _make_one(self, v=_no_header):
        from pyramid.request import Request
        r = Request(environ={})

        class FakeRegistry(object):
            settings = {'lasco.available_languages': 'en fr'}
        r.registry = FakeRegistry()
        if v is not _no_header:
            r.headers['Accept-Language'] = v
        return r

    def test_accept_language(self):
        from lasco.i18n import locale_negotiator
        for accepts, expected in (
            ('fr, en;q=0.5', 'fr'),
            ('xx, yy;q=0.9, fr;q=0.8', 'fr'),
            ('fr-zz, en;q=0.9', 'fr'),
            ('zz', None),
            ('', None),
            (_no_header, None)):
            request = self._make_one(accepts)
            locale = locale_negotiator(request)
            self.assertEqual(locale, expected)

    def test_cookie(self):
        from lasco.i18n import LOCALE_COOKIE_NAME
        from lasco.i18n import locale_negotiator
        request = self._make_one()
        request.cookies[LOCALE_COOKIE_NAME] = 'fr'
        self.assertEqual(locale_negotiator(request), 'fr')
