"""Internationalization utilities."""

from webob.acceptparse import NilAccept

from pyramid.i18n import TranslationStringFactory


_ = TranslationStringFactory('lasco')
LOCALE_COOKIE_NAME = '_LOCALE_'


def locale_negotiator(request, available_languages=None):
    """Return a locale name by first looking in the cookies and, if no
    locale has been found, by looking at the ``Accept-Language`` HTTP
    header.
    """
    locale = request.cookies.get(LOCALE_COOKIE_NAME, None)
    if locale is not None:
        return locale

    settings = request.registry.settings
    available_languages = settings['lasco.available_languages'].split()
    header = request.accept_language
    if isinstance(header, NilAccept):
        # If the header is absent or empty, we get a 'NilAccept'
        # object, whose 'best_match()' method returns the first item
        # in 'available_languages'. This may or may not be our default
        # locale name, so here we will work around this.
        return None
    return header.best_match(available_languages)
