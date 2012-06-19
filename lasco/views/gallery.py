"""General and gallery-related views."""

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound

from sqlalchemy.orm import join as orm_join
from sqlalchemy.orm.exc import NoResultFound

from lasco.i18n import _
from lasco.models import Album
from lasco.models import AlbumViewer
from lasco.models import DBSession
from lasco.models import Gallery
from lasco.auth import get_user_metadata
from lasco.auth import get_user_role
from lasco.auth import ROLE_GALLERY_ADMIN
from lasco.views.utils import TemplateAPI


def not_found(request):
    api = TemplateAPI(request, _(u'Page not found'))
    api.show_login_link = False
    request.response.status = 404
    return {'api': api,
            'resource_url': request.url}


def help(request):
    api = TemplateAPI(request, _('Help'))
    return {'api': api}


def lasco_index(request):
    session = DBSession()
    user_id = get_user_metadata(request).get('id', None)
    if user_id:
        query = ("SELECT DISTINCT galleries.* "
                 "FROM galleries, albums, "
                 "     album_viewers "
                 "WHERE (galleries.id = albums.gallery_id AND "
                 "       albums.id = album_viewers.album_id AND "
                 "       album_viewers.user_id = :user_id)"
                 " UNION SELECT DISTINCT galleries.* "
                 "       FROM galleries, gallery_administrators "
                 "   WHERE (galleries.id=gallery_administrators.gallery_id AND"
                 "       gallery_administrators.user_id = :user_id)")
        galleries = session.execute(query, {'user_id': user_id})
    else:
        galleries = ()
    api = TemplateAPI(request, 'Lasco')
    return {'api': api,
            'galleries': galleries}


def gallery_index(request):
    session = DBSession()
    gallery_name = request.matchdict['gallery_name']
    try:
        gallery = session.query(Gallery).filter_by(name=gallery_name).one()
    except NoResultFound:
        raise HTTPNotFound(request.url)

    role = get_user_role(request, session, gallery)
    if role == ROLE_GALLERY_ADMIN:
        albums = sorted(gallery.albums, key=lambda a: a.title)
    else:
        user_id = get_user_metadata(request).get('id', None)
        albums = session.query(Album).select_from(
            orm_join(Album, AlbumViewer)).\
            filter(Album.gallery_id==gallery.id).\
            filter(Album.id==AlbumViewer.album_id).\
            filter(AlbumViewer.user_id==user_id).order_by(Album.title).all()
        if not albums:
            raise HTTPForbidden()
    api = TemplateAPI(request, gallery.title)
    return {'api': api,
            'gallery': gallery,
            'albums': albums}
