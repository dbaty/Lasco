"""View utilities."""

from pyramid.renderers import get_renderer

from lasco.auth import get_user_metadata


class TemplateAPI(object):
    """Provides a master template and various information and
    utilities that can be used in any template.

    Idea and name borrowed from the KARL project.
    """
    def __init__(self, request, title):
        self.layout = get_renderer('../templates/layout.pt').implementation()
        self.page_title = title
        self.request = request
        self.app_url = request.application_url
        self.referrer = request.environ.get('HTTP_REFERER', None)
        self.here_url = request.url
        self.previous_url = None
        self.next_url = None
        self.show_footer = True
        if self.here_url.split('?')[0].endswith(('login_form', 'login')):
            self.show_footer = False
        user_md = get_user_metadata(request)
        self.logged_in = user_md
        self.user_fullname = user_md.get('fullname', None)
        self.color_theme = request.cookies.get('color_theme', 'default')

    def route_url(self, path, **kwargs):
        return self.request.route_url(path, **kwargs)

    def static_url(self, path):
        if ':' not in path:
            path = 'lasco:static/%s' % path
        return self.request.static_url(path)
