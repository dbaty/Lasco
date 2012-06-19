"""Base API for Lasco."""

from datetime import datetime
import logging
import os.path

from sqlalchemy.orm import join as orm_join

from lasco.ext import exif
from lasco.models import Album
from lasco.models import AlbumViewer
from lasco.models import Gallery
from lasco.models import GalleryAdministrator
from lasco.models import Picture
from lasco.models import User


logging.basicConfig(format='%(levelname)s: %(message)s',
                    level=logging.DEBUG)
PICTURE_EXTENSIONS = ('.jpg', '.png', '.gif')


def empty_tables(session):
    session.execute('DELETE FROM users')
    session.execute('DELETE FROM galleries')
    session.execute('DELETE FROM albums')
    session.execute('DELETE FROM pictures')
    session.execute('DELETE FROM gallery_administrators')
    session.execute('DELETE FROM album_viewers')


def get_users(session):
    return session.query(User).order_by(User.fullname).all()


def add_user(session, login, fullname, password):
    user = User(login, fullname, password)
    session.add(user)
    return user


def remove_user(session, login):
    user = session.query(User).filter_by(login=login).one()
    session.delete(user)


def get_galleries(session):
    return session.query(Gallery).order_by(Gallery.name).all()


def add_gallery(session, name, title):
    g = Gallery(name, title)
    session.add(g)
    return g


def remove_gallery(session, name):
    gallery = session.query(Gallery).filter_by(name=name).one()
    session.delete(gallery)


def manage_gallery_administrators(session, name, *users):
    gallery = session.query(Gallery).filter_by(name=name).one()
    to_delete = []
    to_add = []
    for user in users:
        if user[0] == '-':
            to_delete.append(user[1:])
        elif user[0] == '+':
            to_add.append(user[1:])
        else:
            raise ValueError('Logins must be prefixed with '
                             '"+" or "-". Got: "%s"' % user)
    for login in to_add:
        user_id = session.query(User).filter_by(login=login).one().id
        is_already_admin = session.query(GalleryAdministrator).filter_by(
            gallery_id=gallery.id, user_id=user_id).first()
        if not is_already_admin:
            session.add(GalleryAdministrator(gallery.id, user_id))
    if to_delete:
        logins = ', '.join("'%s'" % login for login in to_delete)
        session.execute('DELETE FROM gallery_administrators '
                        'WHERE gallery_id = :gallery_id AND user_id IN ( '
                        '    SELECT id FROM users '
                        "    WHERE users.login IN (%s))" % logins,
                        {'gallery_id': gallery.id})


def get_gallery_administrators(session, name):
    return session.query(User).from_statement(
        'SELECT users.* FROM users, galleries, gallery_administrators '
        'WHERE galleries.name = :name '
        'AND gallery_administrators.gallery_id = galleries.id '
        'AND users.id = gallery_administrators.user_id'
        ).params(name=name).all()


def get_albums(session, gallery_name):
    gallery = session.query(Gallery).filter_by(name=gallery_name).one()
    return gallery.albums


def add_album(session, config, gallery_name, album_name, album_title,
              pictures_dir):
    gallery = session.query(Gallery).filter_by(name=gallery_name).one()
    album = Album(album_name, album_title)
    gallery.albums.append(album)
    return upload_pictures(config, album, pictures_dir)


def upload_pictures(config, album, pictures_dir):
    base_path = config.get('app:lasco', 'lasco.pictures_base_path')
    base_path = os.path.normpath(base_path)
    if not os.path.isabs(pictures_dir):
        pictures_dir = os.path.join(base_path, pictures_dir)
    else:
        pictures_dir = os.path.normpath(pictures_dir)
    n_pictures = 0
    for path in os.listdir(pictures_dir):
        if path[0] == '.':
            continue  # could be .DS_Store or a friend of his
        if not path.lower().endswith(PICTURE_EXTENSIONS):
            logging.info('Ignoring "%s"', path)
            continue
        full_path = os.path.join(pictures_dir, path)
        relative_path = full_path[len(base_path) + 1:]
        pic_metadata = get_picture_metadata(full_path)
        picture = Picture(relative_path,
                          pic_metadata['date'],
                          u'', u'')
        album.pictures.append(picture)
        n_pictures += 1
    return n_pictures


def remove_album(session, gallery_name, album_name):
    gallery = session.query(Gallery).filter_by(name=gallery_name).one()
    album = session.query(Album).select_from(orm_join(Album, Gallery)).\
        filter(Album.gallery_id==gallery.id).\
        filter(Album.name==album_name).one()
    session.delete(album)


def manage_album_viewers(session, gallery_name, album_name, *users):
    album = session.query(Album).select_from(orm_join(Album, Gallery)).\
        filter(Gallery.name==gallery_name).\
        filter(Album.gallery_id==Gallery.id).\
        filter(Album.name==album_name).one()
    to_delete = []
    to_add = []
    for user in users:
        if user[0] == '-':
            assert user[1:]
            to_delete.append(user[1:])
        elif user[0] == '+':
            assert user[1:]
            to_add.append(user[1:])
        else:
            raise ValueError('Logins must be prefixed with '
                             '"+" or "-". Got: "%s"' % user)
    for login in to_add:
        user_id = session.query(User).filter_by(login=login).one().id
        is_already_viewer = session.query(AlbumViewer).filter_by(
            album_id=album.id, user_id=user_id).all()
        if is_already_viewer:
            logging.info('User "%s" was already a viewer.', login)
        else:
            session.add(AlbumViewer(album.id, user_id))
    if to_delete:
        logins = ', '.join("'%s'" % login for login in to_delete)
        session.execute('DELETE FROM album_viewers '
                        'WHERE album_id = :album_id AND user_id IN ( '
                        '    SELECT id FROM users '
                        "    WHERE users.login IN (%s))" % logins,
                        {'album_id': album.id})


def get_album_viewers(session, gallery_name, album_name):
    return session.query(User).from_statement(
        'SELECT users.* FROM users, galleries, albums, album_viewers '
        'WHERE galleries.name = :gallery_name '
        'AND albums.gallery_id = galleries.id '
        'AND albums.name = :album_name '
        'AND album_viewers.album_id = albums.id '
        'AND users.id = album_viewers.user_id'
        ).params(gallery_name=gallery_name, album_name=album_name).all()


def get_picture_metadata(path):
    f = open(path)
    from_exif = exif.process_file(f)
    date = None
    if from_exif:
        date = from_exif.get('EXIF DateTimeOriginal', None)
        date = datetime.strptime(date.values, '%Y:%m:%d %H:%M:%S')
    if not date:
        date = datetime.fromtimestamp(os.stat(path).st_ctime)
        logging.warning('Warning: could not find EXIF metadata in %s. '
                        'We used the creation date of the file, which '
                        'might be incorrect!' % path)
    f.close()
    return dict(date=date)
