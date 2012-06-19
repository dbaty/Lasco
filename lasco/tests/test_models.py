"""Tests for the models."""

from unittest import TestCase

from lasco.tests.base import TESTING_DB


class TestModels(TestCase):

    def test_gallery(self):
        from lasco.models import Gallery
        g = Gallery('name', 'title')
        self.assertEqual(g.name, 'name')
        self.assertEqual(g.title, 'title')

    def test_album(self):
        from lasco.models import Album
        a = Album('name', 'title')
        self.assertEqual(a.name, 'name')
        self.assertEqual(a.title, 'title')

    def test_picture(self):
        from datetime import datetime
        from lasco.models import Picture
        date = datetime(2010, 07, 28, 13, 10, 00)
        p = Picture(u'path', date, u'caption', u'location')
        self.assertEqual(p.caption, u'caption')
        self.assertEqual(p.location, u'location')
        self.assertEqual(p.path, 'path')
        self.assertEqual(p.date, date)

    def test_picture_get_info(self):
        from datetime import datetime
        from lasco.models import Picture
        date = datetime(2010, 07, 28, 13, 10, 00)
        p1 = Picture(u'path', date, u'caption')
        self.assertEqual(p1.get_info, u'caption - 28 Jul 2010 13:10:00')
        p2 = Picture(u'path', date)
        self.assertEqual(p2.get_info, '28 Jul 2010 13:10:00')
        p3 = Picture(u'path', date, location=u'location')
        self.assertEqual(p3.get_info, u'location - 28 Jul 2010 13:10:00')
        p4 = Picture(u'path', date, u'caption', u'location')
        self.assertEqual(p4.get_info,
                         u'caption - location - 28 Jul 2010 13:10:00')


# The following test case is enabled only if the testing database
# fully implements cascading. PostgreSQL does, SQLite does not. As
# for MySQL, I believe that it depends on the settings of the
# database. This is why this test is only enabled if the testing
# database is PostgreSQL. See README.txt for further details on how
# to select a particular testing database.

class TestOnDeleteCascade(TestCase):

    def setUp(self):
        from pyramid import testing
        from lasco.models import DBSession
        from lasco.models import initialize_sql
        testing.setUp()
        initialize_sql(TESTING_DB)
        self.session = DBSession

    def tearDown(self):
        from pyramid import testing
        testing.tearDown()
        self.session.remove()

    def test_on_delete_gallery(self):
        from datetime import datetime
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        from lasco.models import Picture
        from lasco.models import User
        g = Gallery('name', u'title')
        self.session.add(g)
        a = Album(u'album', u'title')
        g.albums.append(a)
        u = User(u'user', u'fullname', 'password')
        self.session.add(u)
        self.session.flush()  # set 'g.id', 'a.id' and 'u.id'
        self.session.add(GalleryAdministrator(g.id, u.id))
        self.session.add(AlbumViewer(a.id, u.id))
        date = datetime(2010, 07, 28, 13, 10, 00)
        p = Picture(u'path', date)
        a.pictures.append(p)
        assert self.session.query(Gallery).one()
        assert self.session.query(GalleryAdministrator).one()
        assert self.session.query(Album).one()
        assert self.session.query(AlbumViewer).one()
        assert self.session.query(Picture).one()
        self.session.delete(g)
        self.assert_(not self.session.query(Gallery).all())
        self.assert_(not self.session.query(GalleryAdministrator).all())
        self.assert_(not self.session.query(Album).all())
        self.assert_(not self.session.query(AlbumViewer).all())
        self.assert_(not self.session.query(Picture).all())

    def test_on_delete_user(self):
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        from lasco.models import User
        g = Gallery('name', u'title')
        self.session.add(g)
        a = Album(u'album', u'title')
        g.albums.append(a)
        u = User(u'user', u'fullname', 'password')
        self.session.add(u)
        self.session.flush()  # set 'g.id', 'a.id' and 'u.id'
        self.session.add(GalleryAdministrator(g.id, u.id))
        self.session.add(AlbumViewer(a.id, u.id))
        self.session.flush()
        assert self.session.query(GalleryAdministrator).one()
        assert self.session.query(AlbumViewer).one()
        self.session.delete(u)
        self.assert_(not self.session.query(GalleryAdministrator).all())
        self.assert_(not self.session.query(AlbumViewer).all())

if not TESTING_DB.startswith('postgresql'):  # pragma: no coverage
    TestOnDeleteCascade = None
