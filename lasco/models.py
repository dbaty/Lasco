"""Data models."""

from cryptacular.bcrypt import BCRYPTPasswordManager

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapper
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension


DBSession = scoped_session(
    sessionmaker(extension=ZopeTransactionExtension()))
metadata = MetaData()


class User(object):
    def __init__(self, login, fullname, password):
        self.login = login
        self.fullname = fullname
        pwd_manager = BCRYPTPasswordManager()
        self.password = pwd_manager.encode(password)

    def validate_password(self, password):
        pwd_manager = BCRYPTPasswordManager()
        return pwd_manager.check(self.password, password)


users_table = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('login', Unicode(30), unique=True, nullable=False),
    Column('password', String(60), nullable=False),
    Column('fullname', Unicode(50), nullable=False),
    )

mapper(User, users_table)


class Gallery(object):
    def __init__(self, name, title):
        self.name = name
        self.title = title

galleries_table = Table(
    'galleries',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(30), nullable=False, unique=True),
    Column('title', Unicode(255), nullable=False),
    )


class Album(object):
    def __init__(self, name, title):
        self.name = name
        self.title = title

albums_table = Table(
    'albums',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('gallery_id', Integer, ForeignKey('galleries.id',
                                             ondelete='CASCADE')),
    Column('name', String(30), nullable=False),
    UniqueConstraint('gallery_id', 'name'),
    Column('title', Unicode(255), nullable=False),
    )


class Picture(object):
    def __init__(self, path, date, caption=u'', location=u''):
        self.path = path
        self.date = date
        self.caption = caption
        self.location = location

    @property
    def get_info(self):
        info = filter(None, (self.caption,
                             self.location,
                             self.date.strftime('%d %b %Y %H:%M:%S')))
        return u' - '.join(info)


pictures_table = Table(
    'pictures',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('album_id', Integer, ForeignKey('albums.id', ondelete='CASCADE')),
    Column('caption', Unicode(255)),
    Column('location', Unicode(100)),
    Column('path', Unicode(255), nullable=False, unique=True),
    Column('date', DateTime, nullable=False),
    )


mapper(Gallery, galleries_table,
       properties={
        'albums': relationship(Album,
                               cascade='all, delete')})
mapper(Album, albums_table,
       properties={
        'pictures': relationship(Picture,
                                 cascade='all, delete-orphan')})
mapper(Picture, pictures_table)


class GalleryAdministrator(object):
    def __init__(self, gallery_id, user_id):
        self.gallery_id = gallery_id
        self.user_id = user_id

gallery_administrators_table = Table(
    'gallery_administrators',
    metadata,
    Column('gallery_id', Integer, ForeignKey('galleries.id',
                                             ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id',
                                          ondelete='CASCADE'), nullable=False),
    UniqueConstraint('gallery_id', 'user_id'),
    )

mapper(GalleryAdministrator, gallery_administrators_table,
       primary_key=(gallery_administrators_table.c.gallery_id,
                    gallery_administrators_table.c.user_id))


class AlbumViewer(object):
    def __init__(self, album_id, user_id):
        self.album_id = album_id
        self.user_id = user_id

album_viewers_table = Table(
    'album_viewers',
    metadata,
    Column('album_id', Integer, ForeignKey('albums.id',
                                           ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id',
                                          ondelete='CASCADE'), nullable=False),
    UniqueConstraint('album_id', 'user_id'),
    )

mapper(AlbumViewer, album_viewers_table,
       primary_key=(album_viewers_table.c.album_id,
                    album_viewers_table.c.user_id))


def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    metadata.bind = engine
    metadata.create_all(engine)
    return engine
