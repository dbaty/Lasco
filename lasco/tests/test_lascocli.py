"""Tests for ``lascocli`` module."""

from functools import partial
from unittest import TestCase

from sqlalchemy.orm.session import Session


class FakeAPI(object):
    def __init__(self, **callables):
        self.callables = callables
        self.called = []

    def log_me(self, method_name, *args):
        logged_args = args
        if isinstance(logged_args[0], Session):
            logged_args = logged_args[1:]
        self.called.append((method_name, ) + args[1:])
        return self.callables[method_name](*args)

    def __getattr__(self, name):
        return partial(self.log_me, name)


class TestExceptionWrapper(TestCase):

    def _make_one(self, module):
        from lasco.lascocli import ExceptionWrapper
        return ExceptionWrapper(module)

    def test_exception_wrapper_not_callable(self):
        import os
        wrapped_os = self._make_one(os)
        self.assertEqual(wrapped_os.sep, os.sep)

    def test_exception_wrapper_callable_w_exception(self):
        import base64
        from StringIO import StringIO
        import sys
        wrapped_base64 = self._make_one(base64)
        stdout = StringIO()
        sys.stdout = stdout
        try:
            res = wrapped_base64.b64encode(1)
        finally:
            sys.stdout = sys.__stdout__
        expected = ('TypeError: must be string or buffer, not int')
        self.assert_(expected in stdout.getvalue())
        self.assertEqual(res, False)

    def test_exception_wrapper_callable_wo_exception(self):
        import base64
        wrapped_base64 = self._make_one(base64)
        self.assertEqual(wrapped_base64.b64encode('data'),
                         base64.b64encode('data'))


class TestFixCompleter(TestCase):

    def _call_fut(self, *args, **kwargs):
        from lasco.lascocli import fix_completer
        return fix_completer(*args, **kwargs)

    def test_import(self):
        import lasco.lascocli
        lasco.lascocli

    def test_fix_completer(self):
        def completer():
            return ['1', '2', '3']
        fixed = self._call_fut(completer)
        self.assertEqual(fixed(), ['1 ', '2 ', '3 '])

    def test_fixCompleter_no_matches(self):
        def completer():
            return None
        fixed = self._call_fut(completer)
        self.assertEqual(fixed(), None)


class TestLascoCmd(TestCase):
    """Those tests are not very easy to read because:

    1. I do not want to test the ``lasco.api`` module since it has its
       own tests. I hence inject a fake API that merely logs the
       calls.

    2. The command-line client prints data. Checking the output is not
        much fun. Perhaps writing these tests as doctests would have
        been easier to check output, but I do not find doctest very
        flexible.
    """

    def setUp(self):
        from lasco.models import initialize_sql
        from lasco.tests.base import TESTING_DB
        initialize_sql(TESTING_DB)
        self.printed = []

    def tearDown(self):
        from lasco.models import DBSession
        DBSession.remove()

    def _make_one(self, custom_api=None):
        import os.path
        from types import StringType
        from lasco.lascocli import LascoCmd
        ini_file = os.path.join(os.path.dirname(__file__), 'data', 'conf.ini')

        def custom_repr_as_table(headers, *args):
            assert len(headers) == len(args)
            return [headers] + zip(*args)

        def custom_print(msg):
            if isinstance(msg, StringType):
                # remove control characters for color and font weight
                self.printed.append(msg.replace('\033[0;32m=> ', '').\
                                        replace('\033[31m', '').\
                                        replace('\033[0m', ''))
            else:
                self.printed.append(msg)
        return LascoCmd(ini_file, custom_api=custom_api,
                        custom_print=custom_print,
                        custom_repr_as_table=custom_repr_as_table)

    def assertAllEqual(self, *args):
        """Assert that all given arguments are equal."""
        first = args[0]
        for i in range(1, len(args)):
            self.assertEqual(first, args[i])
        return True

    def _call_completer(self, func, text, line):
        begidx = line.find(text)
        endidx = begidx + len(text)
        return func(text, line, begidx, endidx)

    def test_user_list_empty(self):
        get_users = lambda session: ()
        api = FakeAPI(get_users=get_users)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('user_list')
        self.assertEqual(self.printed, [])
        self.assertEqual(api.called, [('get_users', )])

    def test_user_list_not_empty(self):
        from lasco.models import User
        get_users = lambda session: (User('jdoe', 'Jane Doe', ''),
                                     User('jsmith', 'John Smith', ''))
        api = FakeAPI(get_users=get_users)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('user_list')
        self.assertEqual(self.printed,
                         [[('Full name', 'Login'),
                           ('Jane Doe', 'jdoe'),
                           ('John Smith', 'jsmith')]])
        self.assertEqual(api.called, [('get_users', )])

    def test_user_add_wrong_arguments(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('user_add wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: user_add'))
        self.assertEqual(api.called, [])

    def test_user_add(self):
        add_user = lambda session, *args: True
        api = FakeAPI(add_user=add_user)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('user_add login fullname password')
        self.assert_(self.printed[0].startswith('User has been added.'))
        self.assertEqual(api.called,
                         [('add_user', u'login', u'fullname', 'password')])

    def test_user_remove_wrong_arguments(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('user_remove wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: user_remove'))
        self.assertEqual(api.called, [])

    def test_user_remove(self):
        remove_user = lambda session, *args: True
        api = FakeAPI(remove_user=remove_user)
        cmd = self._make_one(custom_api=api)
        cmd.confirm = lambda: True
        cmd.onecmd('user_remove login')
        self.assert_(self.printed[0].startswith('User has been removed.'))
        self.assertEqual(api.called, [('remove_user', u'login')])

    def test_lasco_list_empty(self):
        get_galleries = lambda session: ()
        api = FakeAPI(get_galleries=get_galleries)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('lasco_list')
        self.assertEqual(self.printed, [])
        self.assertEqual(api.called, [('get_galleries', )])

    def test_lasco_list_not_empty(self):
        from lasco.models import Gallery
        get_galleries = lambda session: (Gallery('g1', 'First gallery'),
                                         Gallery('g2', 'Second gallery'))
        api = FakeAPI(get_galleries=get_galleries)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('lasco_list')
        self.assertEqual(self.printed,
                         [[('Name', 'Title'),
                          ('g1', 'First gallery'),
                          ('g2', 'Second gallery')]])
        self.assertEqual(api.called, [('get_galleries', )])

    def test_gallery_add_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_add wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: gallery_add'))
        self.assertEqual(api.called, [])

    def test_gallery_add(self):
        api = FakeAPI(add_gallery=lambda session, *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_add g1 "First gallery"')
        self.assertEqual(self.printed, ['Gallery has been added.'])
        self.assertEqual(api.called, [('add_gallery', 'g1', 'First gallery')])

    def test_gallery_remove_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_remove wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: gallery_remove'))
        self.assertEqual(api.called, [])

    def test_gallery_remove(self):
        api = FakeAPI(remove_gallery=lambda session, *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.confirm = lambda: True
        cmd.onecmd('gallery_remove g1')
        self.assertEqual(self.printed, ['Gallery has been removed.'])
        self.assertEqual(api.called, [('remove_gallery', 'g1')])

    def test_gallery_list_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_list wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: gallery_list'))
        self.assertEqual(api.called, [])

    def test_gallery_list_empty(self):
        get_albums = lambda session, *args: ()
        api = FakeAPI(get_albums=get_albums)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_list g1')
        self.assertEqual(self.printed, [])
        self.assertEqual(api.called, [('get_albums', 'g1')])

    def test_gallery_list_not_empty(self):
        from lasco.models import Album
        get_albums = lambda session, g: (Album('a1', 'First album'),
                                         Album('a2', 'Second album'))
        api = FakeAPI(get_albums=get_albums)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_list g1')
        self.assertEqual(self.printed,
                         [[('Name', 'Title'),
                          ('a1', 'First album'),
                          ('a2', 'Second album')]])
        self.assertEqual(api.called, [('get_albums', 'g1')])

    def test_gallery_users_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_users')  # no arguments
        self.assert_(self.printed[1].startswith('Syntax: gallery_users'))
        self.assertEqual(api.called, [])

    def test_gallery_users_list_users(self):
        from lasco.models import User
        users = (User('jsmith', 'John Smith', ''),
                 User('jdoe', 'Jane Doe', ''))
        api = FakeAPI(
            get_gallery_administrators=lambda session, gallery: users)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_users g1')
        self.assertEqual(self.printed,
                         [[('Login', 'Full name'),
                           ('jsmith', 'John Smith'),
                           ('jdoe', 'Jane Doe')]])
        self.assertEqual(api.called, [('get_gallery_administrators', 'g1')])

    def test_gallery_users_change_rights(self):
        api = FakeAPI(manage_gallery_administrators=lambda *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('gallery_users g1 +jsmith -jdoe')
        self.assertEqual(self.printed, ['Changes have been applied.'])
        self.assertEqual(api.called,
                         [('manage_gallery_administrators', 'g1',
                           '+jsmith', '-jdoe')])

    def test_album_add_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_add a definitely wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: album_add'))
        self.assertEqual(api.called, [])

    def test_album_add(self):
        api = FakeAPI(add_album=lambda session, *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_add g1 a1 "First album" /path/to/album')
        self.assertEqual(self.printed, ['Album has been added.'])
        self.assertEqual(api.called, [('add_album', cmd.config,
                                       'g1', 'a1', 'First album',
                                       '/path/to/album')])

    def test_album_remove_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_remove wrong number of arguments')
        self.assert_(self.printed[0].startswith('Syntax: album_remove'))
        self.assertEqual(api.called, [])

    def test_album_remove(self):
        api = FakeAPI(remove_album=lambda session, *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.confirm = lambda: True
        cmd.onecmd('album_remove g1 a1')
        self.assertEqual(self.printed, ['Album has been removed.'])
        self.assertEqual(api.called, [('remove_album', 'g1', 'a1')])

    def test_album_users_wrong_args(self):
        api = FakeAPI()
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_users')  # no arguments
        self.assert_(self.printed[1].startswith('Syntax: album_users'))
        self.assertEqual(api.called, [])

    def test_album_users_list_users(self):
        from lasco.models import User
        users = (User('jsmith', 'John Smith', ''),
                 User('jdoe', 'Jane Doe', ''))
        api = FakeAPI(get_album_viewers=lambda session, gallery, album: users)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_users g1 a1')
        self.assertEqual(self.printed,
                         [[('Login', 'Full name'),
                           ('jsmith', 'John Smith'),
                           ('jdoe', 'Jane Doe')]])
        self.assertEqual(api.called, [('get_album_viewers', 'g1', 'a1')])

    def test_album_users_change_rights(self):
        api = FakeAPI(manage_album_viewers=lambda *args: True)
        cmd = self._make_one(custom_api=api)
        cmd.onecmd('album_users g1 a1 +jsmith -jdoe')
        self.assertEqual(self.printed, ['Changes have been applied.'])
        self.assertEqual(api.called,
                         [('manage_album_viewers', 'g1', 'a1',
                           '+jsmith', '-jdoe')])

    def test_do_quit(self):
        cmd = self._make_one()
        self.assertEqual(cmd.do_quit(), True)

    def test_help_functions(self):
        # I do not want to check the output of each help function, so
        # I just make sure that calling them do not throw an error
        cmd = self._make_one(custom_api=None)
        for func_name, option in (
            ('help_user_list', False),
            ('help_user_add', True),
            ('help_user_remove', True),
            ('help_lasco_list', False),
            ('help_gallery_add', True),
            ('help_gallery_remove', True),
            ('help_gallery_list', True),
            ('help_gallery_users', True),
            ('help_album_add', True),
            ('help_album_remove', True),
            ('help_album_users', True),
            ('help_shell', True)):
            func = getattr(cmd, func_name)
            func()
            if option:
                func(syntax_only=True)
        self.assert_(self.printed)

    def test_completenames(self):
        cmd = self._make_one()
        self.assertEqual(cmd.completenames('gallery'),
                         ['gallery_add ',
                          'gallery_list ',
                          'gallery_remove ',
                          'gallery_users '])

    def test_completers(self):
        # Check which completer function is used by each command.
        cmd = self._make_one()
        self.assertAllEqual(cmd.complete_gallery_list,
                            cmd.complete_gallery_remove,
                            cmd.complete_gallery_users)
        self.assertEqual(cmd.complete_album_remove,
                         cmd.complete_album_users)

    def test_complete_gallery_name(self):
        from lasco.models import Gallery
        get_galleries = lambda session: (Gallery('g1', 'First gallery'),
                                         Gallery('g2', 'Second gallery'))
        api = FakeAPI(get_galleries=get_galleries)
        cmd = self._make_one(custom_api=api)
        call_fut = lambda text, line: self._call_completer(
            cmd._complete_gallery_name, text, line)
        # >>> gallery_users
        self.assertEqual(call_fut('', 'gallery_users '), ['g1 ', 'g2 '])
        # >>> gallery_users g<Tab>
        self.assertEqual(call_fut('g', 'gallery_users g'), ['g1 ', 'g2 '])
        # >>> gallery_users g1<Tab>
        self.assertEqual(call_fut('g1', 'gallery_users g1'), ['g1 '])
        # >>> gallery_users g1 <Tab>
        self.assertEqual(call_fut('', 'gallery_users g1 '), [])
        self.assertEqual(api.called, [('get_galleries', ),
                                      ('get_galleries', ),
                                      ('get_galleries', )])

    def test_complete_album_name(self):
        from lasco.models import Album
        from lasco.models import Gallery
        get_galleries = lambda session: (Gallery('g1', 'First gallery'),
                                         Gallery('g2', 'Second gallery'))
        get_albums = lambda session, gallery: (Album('a1', 'First album'),
                                               Album('a2', 'Second album'))
        api = FakeAPI(get_galleries=get_galleries, get_albums=get_albums)
        cmd = self._make_one(custom_api=api)
        call_fut = lambda text, line: self._call_completer(
            cmd._complete_album_name, text, line)
        # >>> album_users <Tab>
        self.assertEqual(call_fut('', 'album_users '), ['g1 ', 'g2 '])
        # >>> album_users g<Tab>
        self.assertEqual(call_fut('g', 'album_users g'), ['g1 ', 'g2 '])
        # >>> album_users g1<Tab>
        self.assertEqual(call_fut('g1', 'album_users g1'), ['g1 '])
        # >>> album_users g1 <Tab>
        self.assertEqual(call_fut('', 'album_users g1 '), ['a1 ', 'a2 '])
        # >>> album_users g1 a<Tab>
        self.assertEqual(call_fut('a', 'album_users g1 a'), ['a1 ', 'a2 '])
        # >>> album_users g1 a1<Tab>
        self.assertEqual(call_fut('a1', 'album_users g1 a1'), ['a1 '])
        # >>> album_users g1 a1 <Tab>
        self.assertEqual(call_fut('', 'album_users g1 a1 '), [])
        self.assertEqual(api.called, [('get_galleries', ),
                                      ('get_galleries', ),
                                      ('get_galleries', ),
                                      ('get_albums', 'g1'),
                                      ('get_albums', 'g1'),
                                      ('get_albums', 'g1')])

    def test_complete_gallery_name_and_path(self):
        import os.path
        from lasco.models import Album
        from lasco.models import Gallery
        get_galleries = lambda session: (Gallery('g1', 'First gallery'),
                                         Gallery('g2', 'Second gallery'))
        get_albums = lambda session, gallery: (Album('a1', 'First album'),
                                               Album('a2', 'Second album'))
        api = FakeAPI(get_galleries=get_galleries, get_albums=get_albums)
        cmd = self._make_one(custom_api=api)
        call_fut = lambda text, line: self._call_completer(
            cmd._complete_gallery_name_and_path, text, line)
        # >>> album_add <Tab>
        self.assertEqual(call_fut('', 'album_add '), ['g1 ', 'g2 '])
        # >>> album_add g<Tab>
        self.assertEqual(call_fut('g', 'album_add g'), ['g1 ', 'g2 '])
        # >>> album_add g1<Tab>
        self.assertEqual(call_fut('g1', 'album_add g1'), ['g1 '])
        # >>> album_add g1 <Tab>
        self.assertEqual(call_fut('', 'album_add g1 '), [])
        # >>> album_add g1 a<Tab>
        self.assertEqual(call_fut('a', 'album_add g1 a'), [])
        # >>> album_add g1 a1<Tab>
        self.assertEqual(call_fut('a1', 'album_add g1 a1'), [])
        # >>> album_add g1 a1 <Tab>
        self.assertEqual(call_fut('', 'album_add g1 a1 '), [])
        # >>> album_add g1 a1 Title<Tab>
        self.assertEqual(call_fut('Title', 'album_add g1 a1 Title'), [])
        # >>> album_add g1 a1 Title <Tab>
        self.assertEqual(call_fut('', 'album_add g1 a1 Title '), [])
        # >>> album_add g1 a1 Title /does/not/exist
        self.assertEqual(call_fut('/does/not/exist',
                                  'album_add g1 a1 Title /does/not/exist'),
                         [])
        try:
            root_dirs = ['%s/' % dir for dir in os.listdir('/') \
                             if os.path.isdir('/%s' % dir) and \
                             not dir.startswith('.')]
        except OSError:  # pragma: no coverage
            root_dirs = None
        if root_dirs:
            # >>> album_add g1 a1 Title /<Tab>
            self.assertEqual(call_fut('/', 'album_add g1 a1 Title /'),
                             root_dirs)
            # >>> album_add g1 a1 Title /sb<Tab>
            self.assertEqual(call_fut('/sb', 'album_add g1 a1 Title /sb'),
                             [r for r in root_dirs if r.startswith('sb')])
        current_dir = os.path.dirname(__file__)  # "/path/to/lasco/tests"
        parent_dir = os.path.dirname(current_dir)  # "/path/to/lasco"
        # >>> album_add g1 a1 Title /path/to/lasco<Tab>
        # lasco/
        query = 'album_add g1 a1 Title %s' % parent_dir
        expected = ['%s%s' % (os.path.basename(parent_dir), os.path.sep)]
        self.assertEqual(call_fut(parent_dir, query), expected)
        # >>> album_add g1 a1 Title /path/to/lasco/<Tab>
        # ext/ locale/ static/ templates/ tests/ views/
        query = 'album_add g1 a1 Title %s%s' % (parent_dir, os.path.sep)
        self.assertEqual(sorted(call_fut(parent_dir + os.path.sep, query)),
                         ['ext/', 'locale/', 'static/', 'templates/',
                          'tests/', 'views/'])
        # >>> album_add g1 a1 Title /path/to/lasco/tes<Tab>
        # tests/
        query = 'album_add g1 a1 Title %s%stes' % (parent_dir, os.path.sep)
        expected = ['tests/']
        self.assertEqual(
            call_fut('%s%stes' % (parent_dir, os.path.sep), query), expected)
        self.assertEqual(api.called, [('get_galleries', ),
                                      ('get_galleries', ),
                                      ('get_galleries', )])
