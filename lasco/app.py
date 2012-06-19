from pyramid.config import Configurator

from lasco.auth import setup_who_api_factory
from lasco.models import initialize_sql


def set_config(config):
    # i18n
    config.add_translation_dirs('lasco:locale')
    config.set_locale_negotiator('lasco.i18n.locale_negotiator')

    # Authentication
    config.add_forbidden_view(view='lasco.views.auth.forbidden')
    config.add_route('login', pattern='/login')
    config.add_view('lasco.views.auth.login', route_name='login',
                    request_method='POST',
                    renderer='templates/login.pt')
    config.add_view('lasco.views.auth.login_form', route_name='login',
                    request_method='GET',
                    renderer='templates/login.pt')
    config.add_route('logout', pattern='/logout')
    config.add_view('lasco.views.auth.logout', route_name='logout')

    # Help and options
    config.add_route('help', pattern='/help')
    config.add_view('lasco.views.gallery.help', route_name='help',
                    renderer='templates/help.pt')
    config.add_route('preferences', pattern='/preferences')
    config.add_view('lasco.views.preferences.preferences',
                    route_name='preferences',
                    renderer='templates/preferences.pt')
    config.add_route('set_lang', pattern='/set_lang', request_method='POST')
    config.add_view('lasco.views.preferences.set_lang', route_name='set_lang')
    config.add_route('set_color_theme', pattern='/set_color_theme',
                     request_method='POST')
    config.add_view('lasco.views.preferences.set_color_theme',
                    route_name='set_color_theme')

    # All other views
    config.add_notfound_view('lasco.views.gallery.not_found',
                             renderer='templates/notfound.pt')
    config.add_static_view('static', 'lasco:static')
    config.add_route('home', pattern='')
    config.add_view('lasco.views.gallery.lasco_index', route_name='home',
                    renderer='templates/index.pt')
    config.add_route('gallery', pattern='galleries/{gallery_name}')
    config.add_view('lasco.views.gallery.gallery_index', route_name='gallery',
                    renderer='templates/gallery.pt')
    config.add_route('album', pattern='galleries/{gallery_name}/{album_name}')
    config.add_view('lasco.views.album.album_index', route_name='album',
                    renderer='templates/album.pt')
    config.add_route(
        'picture_in_album',
        pattern='galleries/{gallery_name}/{album_name}/{picture_id}')
    config.add_view('lasco.views.picture.picture_in_album',
                    route_name='picture_in_album',
                    renderer='templates/picture.pt')
    config.add_route('picture_as_image', pattern='pics/{picture_id}')
    config.add_view('lasco.views.picture.picture_as_image',
                    route_name='picture_as_image')
    config.add_route(
        'ajax_update_picture',
        pattern='pics/{picture_id}/ajax_update',
        xhr=True)
    config.add_view('lasco.views.picture.ajax_update', renderer='json',
                    route_name='ajax_update_picture')


def make_app(global_settings, **settings):
    config = Configurator(settings=settings)
    set_config(config)
    initialize_sql(settings['lasco.db_string'])
    setup_who_api_factory(
        config, global_settings, settings['lasco.auth_config'])
    return config.make_wsgi_app()
