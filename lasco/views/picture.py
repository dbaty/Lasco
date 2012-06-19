"""Picture views."""

import os

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import FileResponse

from sqlalchemy.orm import join as orm_join
from sqlalchemy.orm.exc import NoResultFound

from lasco.auth import get_user_role
from lasco.auth import get_user_metadata
from lasco.auth import ROLE_GALLERY_ADMIN
from lasco.models import DBSession
from lasco.models import Album
from lasco.models import Gallery
from lasco.models import Picture
from lasco.views.utils import TemplateAPI


def picture_in_album(request):
    session = DBSession()
    gallery_name = request.matchdict['gallery_name']
    album_name = request.matchdict['album_name']
    try:
        gallery = session.query(Gallery).filter_by(name=gallery_name).one()
        album = session.query(Album).filter_by(gallery_id=gallery.id,
                                               name=album_name).one()
    except NoResultFound:
        raise HTTPNotFound(request.url)
    role = get_user_role(request, session, gallery, album)
    if not role:
        raise HTTPForbidden()

    can_edit = role == ROLE_GALLERY_ADMIN
    pictures = sorted(album.pictures, key=lambda p: p.date)
    picture_index = None
    picture_id = int(request.matchdict['picture_id'])
    previous_id = next_id = None
    for i in range(len(pictures)):
        i_id = pictures[i].id
        if i_id == picture_id:
            picture_index = i
            break
        previous_id = i_id
    if picture_index is None:
        raise HTTPNotFound(request.url)
    picture = pictures[picture_index]
    if picture_index != len(pictures) - 1:
        next_id = pictures[picture_index + 1].id

    api = TemplateAPI(request,
                      '%s - %s' % (gallery.title, album.title))
    if previous_id:
        api.previous_url = request.route_url(
            'picture_in_album',
            gallery_name=gallery_name, album_name=album_name,
            picture_id=previous_id)
    if next_id:
        api.next_url = request.route_url(
            'picture_in_album',
            gallery_name=gallery_name, album_name=album_name,
            picture_id=next_id)
    return {'api': api,
            'gallery': gallery,
            'album': album,
            'picture': picture,
            'picture_index': picture_index,
            'previous_id': previous_id,
            'next_id': next_id,
            'can_edit': can_edit}


def picture_as_image(request):
    """Return an image file for the requested picture."""
    session = DBSession()
    picture_id = request.matchdict['picture_id']
    user_id = get_user_metadata(request).get('id', None)

    if user_id:
        query = (
            "SELECT DISTINCT pictures.* "
            "FROM pictures, album_viewers "
            "WHERE pictures.id=%(picture_id)s AND "
            "      pictures.album_id=album_viewers.album_id AND "
            "      album_viewers.user_id='%(user_id)s' "
            " UNION "
            "   SELECT DISTINCT pictures.* "
            "   FROM pictures, albums, gallery_administrators "
            "   WHERE pictures.id=%(picture_id)s AND "
            "         pictures.album_id=albums.id AND "
            "         albums.gallery_id=gallery_administrators.gallery_id AND "
            "         gallery_administrators.user_id='%(user_id)s' "
            ) % {'picture_id': picture_id, 'user_id': user_id}
        picture = session.execute(query).first()  # may return None
    else:
        picture = None

    if picture is None:
        # We always raise Forbidden, whether the picture exists (and
        # the user is not allowed to view it) or not.
        raise HTTPForbidden()

    base_path = request.registry.settings['lasco.pictures_base_path']
    full_path = os.path.join(base_path, picture.path)
    return FileResponse(full_path, request=request)


def ajax_update(request):
    session = DBSession()
    pic_id = int(request.matchdict['picture_id'])
    picture = session.query(Picture).filter_by(id=pic_id).one()
    gallery = session.query(Gallery).select_from(
        orm_join(Gallery, Album)).\
        filter(Album.id==picture.album_id).\
        filter(Gallery.id==Album.gallery_id).one()
    if get_user_role(request, session, gallery) != ROLE_GALLERY_ADMIN:
        raise HTTPForbidden()
    picture.caption = request.POST['caption']
    picture.location = request.POST['location']
    return {'pic_info': picture.get_info}
