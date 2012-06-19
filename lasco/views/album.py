"""Album views."""

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound

from sqlalchemy.orm.exc import NoResultFound

from lasco.auth import get_user_role
from lasco.batch import Batch
from lasco.models import Album
from lasco.models import DBSession
from lasco.models import Gallery
from lasco.views.utils import TemplateAPI


def album_index(request):
    """An index page for an album """
    session = DBSession()
    gallery_name = request.matchdict['gallery_name']
    album_name = request.matchdict['album_name']
    page = int(request.GET.get('page', 1))
    try:
        gallery = session.query(Gallery).filter_by(name=gallery_name).one()
        album = session.query(Album).filter_by(gallery_id=gallery.id,
                                               name=album_name).one()
    except NoResultFound:
        raise HTTPNotFound(request.url)
    if not get_user_role(request, session, gallery, album):
        raise HTTPForbidden()
    pictures = sorted(album.pictures, key=lambda p: p.date)
    settings = request.registry.settings
    pictures = Batch(pictures,
                     batch_length=int(settings['lasco.pictures_per_page']),
                     current=page)
    api = TemplateAPI(request,
                      '%s - %s' % (gallery.title, album.title))
    url_of_page = '%s?page=%%s' % request.route_url(
        'album',
        gallery_name=gallery.name, album_name=album.name)
    if pictures.previous:
        api.previous_url = url_of_page % pictures.previous
    if pictures.next:
        api.next_url = url_of_page % pictures.next
    return {'api': api,
            'gallery': gallery,
            'album': album,
            'pictures': pictures,
            'url_of_page': url_of_page}
