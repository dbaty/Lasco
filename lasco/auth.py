from repoze.who.config import make_api_factory_with_config
from repoze.who.interfaces import IAPIFactory

from lasco.models import AlbumViewer
from lasco.models import GalleryAdministrator


ROLE_GALLERY_ADMIN = 'Gallery administrator'
ROLE_ALBUM_VIEWER = 'Album viewer'


def setup_who_api_factory(config, global_settings, conf_file, dummy=None):
    if dummy is not None:
        who_api_factory = dummy
    else:
        who_api_factory = make_api_factory_with_config(
            global_settings, conf_file)
    config.registry.registerUtility(who_api_factory, IAPIFactory)


def get_who_api(request):
    factory = request.registry.queryUtility(IAPIFactory)
    return factory(request.environ)


def get_user_metadata(request):
    md = getattr(request, '__user_metadata', None)
    if md is not None:
        return md
    who_api = get_who_api(request)
    md = who_api.authenticate() or {}
    request.__user_metadata = md
    return md


def get_user_role(request, session, gallery, album=None):
    """Return role of the logged-in user in the given gallery or in
    the given album.

    The policy is as follows:

    - an anonymous user has no role;

    - a user may be an administrator of a gallery. It also means that
      she is an administrator of all albums of this gallery;

    - if a user is not an administrator of the gallery, she may have a
      Viewer role in the given album.
    """
    user_id = get_user_metadata(request).get('id', None)
    if not user_id:
        return None

    if session.query(GalleryAdministrator).\
            filter_by(gallery_id=gallery.id,
                      user_id=user_id).first():
        return ROLE_GALLERY_ADMIN

    if album:
        if session.query(AlbumViewer).\
                filter_by(album_id=album.id,
                          user_id=user_id).first():
            return ROLE_ALBUM_VIEWER

    return None
