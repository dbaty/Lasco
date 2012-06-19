"""Tests for ``api`` module."""

from lasco.tests.base import LascoTestCase


class TestApi(LascoTestCase):

    #
    # I see no point in writing tests for each and every function of
    # ``lasco.api`` since most of them are used and fully covered by
    # tests for the views. Here below are tests for some parts that
    # are not covered elsewhere, used only in the command-line client
    # (which does not have tests of its own). There are also some
    # tests for ``getPicturesMetadata()``.
    #

    def test_empty_tables(self):
        from datetime import datetime
        from lasco import api
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        from lasco.models import Picture
        from lasco.models import User

        g = Gallery('name', u'title')
        a = Album('name', u'title')
        p = Picture(u'path', datetime.now(), u'caption', u'location')
        u = User(u'jsmith', u'John Smith', 'password')
        a.pictures.append(p)
        g.albums.append(a)
        self.session.add(g)
        self.session.add(u)
        self.session.flush()
        self.session.add(GalleryAdministrator(g.id, u.id))
        self.session.add(AlbumViewer(a.id, u.id))

        assert self.session.query(Album).one()
        assert self.session.query(AlbumViewer).one()
        assert self.session.query(Gallery).one()
        assert self.session.query(GalleryAdministrator).one()
        assert self.session.query(Picture).one()
        assert self.session.query(User).one()

        api.empty_tables(self.session)

        self.assert_(not self.session.query(Album).all())
        self.assert_(not self.session.query(AlbumViewer).all())
        self.assert_(not self.session.query(Gallery).all())
        self.assert_(not self.session.query(GalleryAdministrator).all())
        self.assert_(not self.session.query(Picture).all())
        self.assert_(not self.session.query(User).all())

    def test_get_users(self):
        from lasco import api
        from lasco.models import User
        self.assertEqual(api.get_users(self.session), [])
        user = User(u'user1', u'fullname', 'password')
        self.session.add(user)
        self.assertEqual(api.get_users(self.session), [user])

    def test_add_user(self):
        from lasco import api
        from lasco.models import User
        api.add_user(self.session, u'login', u'fullname', 'password')
        user = self.session.query(User).one()
        self.assertEqual(user.login, u'login')
        self.assertEqual(user.fullname, u'fullname')

    def test_remove_user(self):
        from lasco import api
        from lasco.models import User
        user = User(u'user1', u'fullname', 'password')
        self.session.add(user)
        self.assertEqual(len(api.get_users(self.session)), 1)
        api.remove_user(self.session, u'user1')
        self.assertEqual(api.get_users(self.session), [])

    def test_get_galleries(self):
        from lasco import api
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        galleries = api.get_galleries(self.session)
        self.assertEqual(len(galleries), 1)
        self.assertEqual(galleries[0].title, u'title')

    def test_add_gallery(self):
        from lasco import api
        from lasco.models import Gallery
        assert not self.session.query(Gallery).count()
        api.add_gallery(self.session, u'name', u'title')
        g = self.session.query(Gallery).one()
        self.assertEqual(g.name, u'name')
        self.assertEqual(g.title, u'title')

    def test_remove_gallery(self):
        from lasco import api
        from lasco.models import Gallery
        self.session.add(Gallery('name', u'title'))
        assert self.session.query(Gallery).one()
        api.remove_gallery(self.session, 'name')
        self.assert_(not self.session.query(Gallery).all())

    def test_manage_gallery_administrators(self):
        from lasco import api
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        user1 = self.add_user(u'user1')
        user2 = self.add_user(u'user2')
        user3 = self.add_user(u'user3')
        g = Gallery('name', u'title')
        self.session.add(g)
        api.manage_gallery_administrators(self.session, 'name', u'+user1')
        admin = self.session.query(GalleryAdministrator).one()
        self.assertEqual(admin.gallery_id, g.id)
        self.assertEqual(admin.user_id, user1.id)
        api.manage_gallery_administrators(
            self.session, 'name', u'-user1', u'+user2', u'+user3')
        admins = self.session.query(GalleryAdministrator).all()
        self.assertEqual(sorted([a.user_id for a in admins]),
                         [user2.id, user3.id])

    def test_manage_gallery_administrators_wrong_syntax(self):
        from lasco import api
        from lasco.models import Gallery
        self.session.add(Gallery('name', u'title'))
        self.assertRaises(
            ValueError,
            api.manage_gallery_administrators, self.session, 'name', 'user')

    def test_manage_gallery_administrators_add_already_admin(self):
        from lasco import api
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        self.session.add(Gallery('name', u'title'))
        user = self.add_user(u'user1')
        api.manage_gallery_administrators(self.session, 'name', u'+user1')
        assert self.session.query(GalleryAdministrator).one()
        api.manage_gallery_administrators(self.session, 'name', u'+user1')
        admin = self.session.query(GalleryAdministrator).one()
        self.assertEqual(admin.user_id, user.id)

    def test_manage_gallery_administrators_remove_not_admin(self):
        from lasco import api
        from lasco.models import Gallery
        from lasco.models import GalleryAdministrator
        self.session.add(Gallery('name', u'title'))
        assert not self.session.query(GalleryAdministrator).all()
        self.add_user(u'user1')
        api.manage_gallery_administrators(self.session, 'name', u'-user1')
        self.assert_(not self.session.query(GalleryAdministrator).all())

    def test_get_gallery_administrators(self):
        from lasco import api
        from lasco.models import Gallery
        self.session.add(Gallery('name', u'title'))
        self.assertEqual(
            api.get_gallery_administrators(self.session, 'name'), [])
        self.add_user(u'user1')
        self.add_user(u'user2')
        self.add_user(u'user3')
        api.manage_gallery_administrators(
            self.session, 'name', u'-user1', u'+user2', u'+user3')
        admins = api.get_gallery_administrators(self.session, 'name')
        self.assertEqual([a.login for a in admins], ['user2', 'user3'])

    def test_add_album(self):
        import os.path
        from lasco import api
        from lasco.models import Album
        from lasco.models import Gallery

        class FakeConfig:
            def get(self, section, option):
                assert section == 'app:lasco'
                assert option == 'lasco.pictures_base_path'
                return os.path.dirname(__file__)
        g = Gallery('g', u'title')
        self.session.add(g)
        assert not self.session.query(Album).all()
        dir = unicode(os.path.join(os.path.dirname(__file__), 'data'))
        api.add_album(self.session, FakeConfig(),
                      'g', 'album', u'album_title', dir)
        album = self.session.query(Album).one()
        self.assertEqual(album.title, 'album_title')
        self.assertEqual(len(album.pictures), 2)

    def test_get_albums(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('name', u'album_title'))
        albums = api.get_albums(self.session, 'g')
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, u'album_title')

    def test_remove_album(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('name', u'album_title'))
        assert self.session.query(Album).one()
        api.remove_album(self.session, 'g', 'name')
        self.assert_(not self.session.query(Album).all())

    def test_manage_album_viewers(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        a = Album('album', u'title')
        self.session.add(g)
        g.albums.append(a)
        user1 = self.add_user(u'user1')
        user2 = self.add_user(u'user2')
        user3 = self.add_user(u'user3')
        api.manage_album_viewers(self.session, 'g', 'album', u'+user1')
        viewer = self.session.query(AlbumViewer).one()
        self.assertEqual(viewer.album_id, a.id)
        self.assertEqual(viewer.user_id, user1.id)
        api.manage_album_viewers(
            self.session, 'g', 'album', u'-user1', u'+user2', u'+user3')
        viewers = self.session.query(AlbumViewer).all()
        self.assertEqual(sorted([v.user_id for v in viewers]),
                         [user2.id, user3.id])

    def test_manage_album_viewers_wrong_syntax(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('album', u'title'))
        self.assertRaises(
            ValueError,
            api.manage_album_viewers, self.session, 'g', 'album', 'user')

    def test_manage_album_viewers_add_already_viewer(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('album', u'title'))
        user = self.add_user(u'user1')
        api.manage_album_viewers(self.session, 'g', 'album', u'+user1')
        assert self.session.query(AlbumViewer).one()
        api.manage_album_viewers(self.session, 'g', 'album', u'+user1')
        viewer = self.session.query(AlbumViewer).one()
        self.assertEqual(viewer.user_id, user.id)

    def test_manage_album_viewers_remove_not_viewer(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import AlbumViewer
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('album', u'title'))
        assert not self.session.query(AlbumViewer).all()
        self.add_user(u'user1')
        api.manage_album_viewers(self.session, 'g', 'album', u'-user1')
        self.assert_(
            not self.session.query(AlbumViewer).all())

    def test_get_album_viewers(self):
        from lasco import api
        from lasco.models import Album
        from lasco.models import Gallery
        g = Gallery('g', u'title')
        self.session.add(g)
        g.albums.append(Album('album', u'title'))
        self.assertEqual(
            api.get_album_viewers(self.session, 'g', 'album'),
            [])
        self.add_user(u'user1')
        api.manage_album_viewers(self.session, 'g', 'album', u'+user1')
        viewers = api.get_album_viewers(self.session, 'g', 'album')
        self.assertEqual([v.login for v in viewers], ['user1'])

    def test_get_picture_metadata(self):
        from datetime import datetime
        import os.path
        from lasco import api
        self._monkey_patch_exif_process(None)  # uninstall our monkey-patch
        path = os.path.join(
            os.path.dirname(__file__), 'data', 'w_exif.jpg')
        md = api.get_picture_metadata(path)
        expected_date = datetime(2010, 07, 23, 22, 14, 22)
        self.assertEqual(md, dict(date=expected_date))

    def test_get_picture_metadata_no_exif(self):
        from datetime import datetime
        import os
        import os.path
        from lasco import api
        path = os.path.join(
            os.path.dirname(__file__), 'data', 'wo_exif.jpg')
        md = api.get_picture_metadata(path)
        expected_date = datetime.fromtimestamp(os.stat(path).st_ctime)
        self.assertEqual(md, dict(date=expected_date))
