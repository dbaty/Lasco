"""Base classes and utilities for tests."""

import os
import os.path
from ConfigParser import ConfigParser
from unittest import TestCase

from pyramid import testing

from lasco import api as lascoapi
from lasco.models import DBSession
from lasco.models import initialize_sql


TESTING_DB = os.environ.get('TESTING_DB', 'sqlite:///:memory:')
FAKE_CONFIG = ConfigParser()
FAKE_CONFIG.add_section('app:lasco')
FAKE_CONFIG.set('app:lasco',
                'lasco.pictures_base_path',
                os.path.dirname(__file__))


# Do not let bcrypt slow down our tests.
from cryptacular.bcrypt import BCRYPTPasswordManager
_check = lambda self, encoded, password: (encoded == self.encode(password))
BCRYPTPasswordManager.encode = lambda self, s: (s + 60 * '*')[:60]
BCRYPTPasswordManager.check = _check


class LascoTestCase(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initialize_sql(TESTING_DB)
        self.session = DBSession
        self._monkey_patch_exif_process(lambda f: {})

    def tearDown(self):
        testing.tearDown()
        # FIXME: temporary trick to close the connection that would
        # otherwise be left open. This is a problem on my PostgreSQL
        # database which has a low number of concurrent open
        # connections and cause the following database error:
        #   FATAL:  connection limit exceeded for non-superusers
        self.session.bind.dispose()
        self.session.remove()
        self._monkey_patch_exif_process(None)

    def _monkey_patch_exif_process(self, override=None):
        # Do not let the EXIF module slow down our tests. The
        # original code is enabled back on tests that require it.
        from lasco.ext import exif
        if override:
            self._orig_exif_process_file = exif.process_file
            exif.process_file = override
        else:
            exif.process_file = self._orig_exif_process_file

    def add_user(self, login, fullname=u''):
        return lascoapi.add_user(self.session, login, fullname, 'password')

    def add_gallery(self, name, title):
        return lascoapi.add_gallery(self.session, name, title)

    def add_album(self, gallery_name, album_name, album_title,
                  pictures_dir=u'data'):
        lascoapi.add_album(self.session, FAKE_CONFIG, gallery_name,
                           album_name, album_title, pictures_dir)

    def add_gallery_admin(self, gallery_name, login):
        lascoapi.manage_gallery_administrators(
            self.session, gallery_name, '+%s' % login)

    def add_album_viewer(self, gallery_name, album_name, login):
        lascoapi.manage_album_viewers(
            self.session, gallery_name, album_name, '+%s' % login)
