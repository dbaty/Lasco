"""Preferences views."""

from pyramid.httpexceptions import HTTPSeeOther

from lasco.i18n import _
from lasco.i18n import LOCALE_COOKIE_NAME
from lasco.i18n import locale_negotiator
from lasco.views.utils import TemplateAPI


AVAILABLE_THEMES = ('default', 'white')


def preferences(request):
    api = TemplateAPI(request, _('Your preferences'))
    current_lang = locale_negotiator(request)
    settings = request.registry.settings
    available_langs = settings['lasco.available_languages'].split()
    current_theme = request.cookies.get('color_theme', 'default')
    return {'api': api,
            'current_theme': current_theme,
            'available_themes': AVAILABLE_THEMES,
            'current_lang': current_lang,
            'available_langs': available_langs}


def set_lang(request):
    new_lang = request.POST['lang']
    response = HTTPSeeOther(request.route_url('preferences'))
    cookie_path = '/'  # FIXME: not necessarily
    response.set_cookie(LOCALE_COOKIE_NAME, new_lang, path=cookie_path)
    return response


def set_color_theme(request):
    cookie_name = 'color_theme'
    current = request.cookies.get(cookie_name, 'default')
    new_theme = request.POST.get('color_theme')
    response = HTTPSeeOther(request.route_url('preferences'))
    if new_theme and new_theme != current:
        cookie_path = '/'  # FIXME: not necessarily
        if new_theme == 'default':
            response.delete_cookie(cookie_name, path=cookie_path)
        else:
            response.set_cookie(cookie_name, new_theme, path=cookie_path)
    return response
