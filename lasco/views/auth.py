"""Login/logout views."""

from urllib import quote_plus
from urllib import unquote_plus

from pyramid.httpexceptions import HTTPSeeOther

from lasco.auth import get_who_api
from lasco.i18n import _
from lasco.views.utils import TemplateAPI


def login_form(request, failed=False):
    api = TemplateAPI(request, 'Log in')
    next = request.GET.get('next') or \
        request.POST.get('next') or \
        quote_plus(api.referrer or api.app_url)
    login = request.POST.get('login', '')
    if failed:
        error_msg = _(u'Wrong user name or password.')
    else:
        error_msg = None
    return {'api': api,
            'login': login,
            'next': next,
            'error_msg': error_msg}


def login(request):
    app_url = request.application_url
    next = request.POST.get('next', '') or app_url
    who_api = get_who_api(request)
    creds = {'login': request.POST['login'],
             'password': request.POST['password']}
    authenticated, headers = who_api.login(creds)
    if not authenticated:
        return login_form(request, failed=True)
    return HTTPSeeOther(location=unquote_plus(next), headers=headers)


def logout(request):
    who_api = get_who_api(request)
    headers = who_api.logout()
    return HTTPSeeOther(location=request.application_url, headers=headers)


def forbidden(request):
    # FIXME: he we should check whether the user is logged in. If so,
    # we should return a 403 Forbidden with an appropriate message
    # ("You are not allowed to access this page. Click here to go
    # back."). If the user is not logged in, then we return the
    # HTTPSeeOther as done below.

    # Called when a view raises Forbidden.
    location = '%s/login_form?next=%s' % (
        request.application_url,
        quote_plus(request.url))
    return HTTPSeeOther(location=location)
