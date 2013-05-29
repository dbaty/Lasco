#!/usr/bin/env python
"""A command-line client for Lasco."""


from ConfigParser import ConfigParser
from cmd import Cmd
from optparse import OptionParser
import os
import readline  # pyflakes: ignore
import shlex
import sys
import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import lasco.api
import lasco.models
from lasco.utils import repr_as_table


DEFAULT_ENCODING = 'utf-8'


class ExceptionWrapper(object):
    """A wrapper around ``lasco.api`` that catches any exception,
    prints it in a nice colour and avoids leaving the command-line
    client.
    """
    def __init__(self, module):
        self._module = module

    def __getattr__(self, attr):
        def wrapped(*args, **kwargs):
            try:
                return getattr(self._module, attr)(*args, **kwargs)
            except:
                print '\033[31m'
                traceback.print_exc(file=sys.stdout)
                print '\033[0m'
                return False
        orig = getattr(self._module, attr)
        if not callable(orig):
            return orig
        return wrapped


def fix_completer(completer):
    """Add a trailing space to the completion matches so that the user
    does not have to type a space to separate the completed command
    from its arguments.

    This mimics Bash completion.
    """
    def decorated(*args, **kwargs):
        matches = completer(*args, **kwargs)
        if matches is None:
            return None
        return map(lambda m: m + ' ', matches)
    return decorated


def get_args(line):
    """Return arguments given in a command line as Unicode strings."""
    args = shlex.split(line)
    return [unicode(arg, DEFAULT_ENCODING) for arg in args]


class LascoCmd(Cmd):

    prompt = 'lasco> '

    def __init__(self, conf_file,
                 custom_api=None,
                 custom_print=None,
                 custom_repr_as_table=None):
        Cmd.__init__(self)
        here = os.path.abspath(os.path.dirname(conf_file))
        self.config = ConfigParser(defaults={'here': here})
        self.config.read(conf_file)
        db_string = self.config.get('app:lasco', 'lasco.db_string')
        self.engine = create_engine(db_string)
        self.session = sessionmaker(self.engine)()
        # Create tables if they do not exist yet.
        metadata = lasco.models.metadata
        metadata.bind = self.engine
        metadata.create_all(self.engine)
        # The following customizations are here for our tests.
        if custom_api:
            self.api = custom_api
        else:
            self.api = ExceptionWrapper(lasco.api)
        if custom_print:
            self.print_ = custom_print
        else:  # pragma: no coverage
            self.print_ = lambda msg: sys.stdout.write(
                msg.encode(DEFAULT_ENCODING) + os.linesep)
        if custom_repr_as_table:
            self.repr_as_table = custom_repr_as_table
        else:  # pragma: no coverage
            self.repr_as_table = repr_as_table

    def confirm(self, prompt='Are you sure?'):  # pragma: no coverage
        if raw_input(prompt + ' [yes/no] ') == 'yes':
            return True
        else:
            self.print_error('Action has been cancelled.')
            return False

    def print_success(self, msg):
        self.print_('\033[0;32m=> %s\033[0m' % msg)

    def print_error(self, msg):  # pragma: no coverage
        self.print_('\033[31m%s\033[0m' % msg)

    @fix_completer
    def completenames(self, text, *ignored):
        return Cmd.completenames(self, text, *ignored)

    def complete_help(self, *args):
        """A completer function for the ``help`` command.

        Since our version of ``completenames()`` adds a trailing
        whitespace, we need to override ``Cmd.complete_help()``
        otherwise all commands are listed twice (once with a trailing
        space, once without).
        """
        commands = [name.rstrip() for name in self.completenames(*args)]
        commands = set(commands)
        # The rest of the method is the same as the original
        # implementation ('Cmd.complete_help()').
        topics = set(a[5:] for a in self.get_names()
                     if a.startswith('help_' + args[0]))
        return list(commands | topics)

    @fix_completer
    def _complete_gallery_name(self, text, line, begidx, endidx):
        """A completer function for all commands that require a
        gallery name.
        """
        args = get_args(line)
        # We check the last character of the line to know whether the
        # user wants to type a new argument or complete one for which
        # one or more letters have been typed already.
        if len(args) > 2 or (len(args) == 2 and line[-1] == ' '):
            return []
        names = [g.name for g in self.api.get_galleries(self.session)]
        return filter(lambda n: n.startswith(text), names)

    @fix_completer
    def _complete_album_name(self, text, line, begidx, endidx):
        """A completer function for all commands that require a
        gallery name followed by an album name.
        """
        args = get_args(line)
        # We check the last character of the line to know whether the
        # user wants to type a new argument or complete one for which
        # one or more letters have been typed already.
        if len(args) > 3 or (len(args) == 3 and line[-1] == ' '):
            return []
        if len(args) == 1 or (len(args) == 2 and line[-1] != ' '):
            # Called to complete the name of the gallery
            names = [g.name for g in self.api.get_galleries(self.session)]
            return filter(lambda n: n.startswith(text), names)
        if len(args) == 2 or (len(args) == 3 and line[-1] != ' '):
            # Called to complete the name of the album
            names = [a.name for a in \
                         self.api.get_albums(self.session, args[1])]
            return filter(lambda n: n.startswith(text), names)

    def _complete_gallery_name_and_path(self, text, line, begidx, endidx):
        """A completer function for the 'album_add' command."""
        args = get_args(line)
        # We check the last character of the line to know whether the
        # user wants to type a new argument or complete one for which
        # one or more letters have been typed already.
        if len(args) == 1 or (len(args) == 2 and line[-1] != ' '):
            # Called to complete the name of the gallery
            names = [g.name for g in self.api.get_galleries(self.session)]
            # I only wanted to call the 'fix_completer()' function,
            # and then I got slightly carried away... Still, these two
            # lambda's on a single line, isn't that pretty?
            return fix_completer(
                lambda: filter(lambda n: n.startswith(text), names))()
        if len(args) == 2 or (len(args) == 3 and line[-1] != ' '):
            # Name of the album. Nothing to complete
            return []
        if len(args) == 3 or (len(args) == 4 and line[-1] != ' '):
            # Title of the album. Nothing to complete.
            return []
        if len(args) == 4 or (len(args) == 5 and line[-1] != ' '):
            # readline seems to take the slash character as a
            # separator (like a space) in 'text', and thefore sets
            # 'text' as the final portion of the path. For example,
            # with the following line:
            #     action /path/to/foo<Tab>
            # 'text' is 'foo', not the whole path.
            # I am not sure whether this bug affects any readline
            # implementation or only the one I use on OS X 10.4
            # FIXME: check on FreeBSD.
            if line[begidx - 1] == os.sep:  # pragma: no coverage
                text = line[1 + line[:begidx].rfind(' '):]
            dir = os.path.dirname(text)
            if not os.path.exists(dir):
                return []
            if dir == '/':
                rest = text[len(dir):]  # otherwise we eat the first letter
            else:
                rest = text[len(dir) + 1:]
            matches = []
            for candidate in os.listdir(dir):
                if candidate.startswith('.'):
                    continue
                if not candidate.startswith(rest):
                    continue
                full_path = os.path.join(dir, candidate)
                if not os.path.isdir(full_path):
                    continue
                matches.append('%s%s' % (candidate, os.path.sep))
            return matches

    def do_user_list(self, __ignored_line_remainder):
        users = self.api.get_users(self.session)
        if users:
            self.print_(
                self.repr_as_table(
                    ('Full name', 'Login'),
                    [u.fullname for u in users],
                    [u.login for u in users]))

    def help_user_list(self):
        self.print_('List all users.')

    def do_user_add(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 3:
            return self.help_user_add(syntax_only=True)
        self.api.add_user(self.session, *args)
        self.print_success('User has been added.')

    def help_user_add(self, syntax_only=False):
        if not syntax_only:
            self.print_('Add a new user.')
        self.print_('Syntax: user_add <login> <full-name> <password>')

    def do_user_remove(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 1:
            return self.help_user_remove(syntax_only=True)
        if self.confirm():
            self.api.remove_user(self.session, args[0])
            self.print_success('User has been removed.')

    def help_user_remove(self, syntax_only=False):
        if not syntax_only:
            self.print_('Remove a user.')
        self.print_('Syntax: user_remove <login>')

    def do_lasco_list(self, __ignored_line_remainder):
        galleries = self.api.get_galleries(self.session)
        if galleries:
            self.print_(
                self.repr_as_table(
                    ('Name', 'Title'),
                    [g.name for g in galleries],
                    [g.title for g in galleries]))

    def help_lasco_list(self):
        self.print_('List all galleries.')

    def do_gallery_add(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 2:
            return self.help_gallery_add(syntax_only=True)
        self.api.add_gallery(self.session, *args)
        self.print_success('Gallery has been added.')

    def help_gallery_add(self, syntax_only=False):
        if not syntax_only:
            self.print_('Add a new gallery.')
        self.print_('Syntax: gallery_add <name> <title>')

    def do_gallery_remove(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 1:
            return self.help_gallery_remove(syntax_only=True)
        if self.confirm():
            self.api.remove_gallery(self.session, *args)
            self.print_success('Gallery has been removed.')

    def help_gallery_remove(self, syntax_only=False):
        if not syntax_only:
            self.print_('Remove a gallery.')
        self.print_('Syntax: gallery_remove <name>')

    complete_gallery_remove = _complete_gallery_name

    def do_gallery_list(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 1:
            return self.help_gallery_list(syntax_only=True)
        albums = self.api.get_albums(self.session, *args)
        if albums:
            self.print_(
                self.repr_as_table(
                    ('Name', 'Title'),
                    [a.name for a in albums],
                    [a.title for a in albums]))

    def help_gallery_list(self, syntax_only=False):
        if not syntax_only:
            self.print_('List albums of a gallery.')
        self.print_('Syntax: gallery_list <name>')

    complete_gallery_list = _complete_gallery_name

    def do_gallery_users(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) < 1:
            return self.help_gallery_users()
        elif len(args) == 1:
            admins = self.api.get_gallery_administrators(self.session, *args)
            self.print_(
                self.repr_as_table(
                    ('Login', 'Full name'),
                    [a.login for a in admins],
                    [a.fullname for a in admins]))
        else:
            self.api.manage_gallery_administrators(self.session, *args)
            self.print_success('Changes have been applied.')

    def help_gallery_users(self, syntax_only=False):
        if not syntax_only:
            self.print_("Grant or revoke user's rights in a gallery.")
        self.print_('Syntax: gallery_users <gallery_name> {+,-}<login>')
        self.print_('If no user id is provided, this command lists all '
                    'administrators of this gallery.')

    complete_gallery_users = _complete_gallery_name

    def do_album_add(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 4:
            return self.help_album_add(syntax_only=True)
        self.api.add_album(self.session, self.config, *args)
        self.print_success('Album has been added.')

    def help_album_add(self, syntax_only=False):
        if not syntax_only:
            self.print_('Add a new album.')
        self.print_('Syntax: album_add <gallery_name> '
                    '<album_name> <album_title> <pictures_dir>')

    complete_album_add = _complete_gallery_name_and_path

    def do_album_remove(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) != 2:
            return self.help_album_remove(syntax_only=True)
        if self.confirm():
            self.api.remove_album(self.session, *args)
            self.print_success('Album has been removed.')

    def help_album_remove(self, syntax_only=False):
        if not syntax_only:
            self.print_('Remove an album.')
        self.print_('Syntax: album_remove <gallery_name> <album_name>')

    complete_album_remove = _complete_album_name

    def do_album_users(self, line_remainder):
        args = get_args(line_remainder)
        if len(args) < 1:
            return self.help_album_users()
        elif len(args) == 2:
            viewers = self.api.get_album_viewers(self.session, *args)
            self.print_(
                self.repr_as_table(
                    ('Login', 'Full name'),
                    [v.login for v in viewers],
                    [v.fullname for v in viewers]))
        else:
            self.api.manage_album_viewers(self.session, *args)
            self.print_success('Changes have been applied.')

    def help_album_users(self, syntax_only=False):
        if not syntax_only:
            self.print_("Grant or revoke user's rights in an album.")
        self.print_('Syntax: album_users <gallery_name> <album_name> '
                    '{+,-}<login>')
        self.print_('If no user id is provided, this command lists all '
                    'viewers of this album.')

    complete_album_users = _complete_album_name

    def do_shell(self, __ignored_line_remainder):  # pragma: no coverage
        engine = self.engine    # must be available in the shell below
        session = self.session  # (do not remove)
        try:
            self.print_('Shell mode. Changes must be committed manually:')
            self.print_('        session.commit()')
            self.print_("Type 'locals()' to know what you may play with.")
            self.print_('Press Control-C to leave the shell.')
            while True:
                try:
                    self.print_(unicode(input('>>> ')))
                except KeyboardInterrupt:
                    raise
                except:
                    self.print_error('Exception in user code:')
                    traceback.print_exc(file=sys.stdout)
        except KeyboardInterrupt:
            self.print_('Leaving shell.')

    def help_shell(self, syntax_only=False):
        if not syntax_only:
            self.print_('Takes you to a Python shell where you can '
                        'directly interact with the database connection '
                        'session.')
        self.print_('Syntax: shell')

    def do_quit(self, *__ignored_line_remainder):
        return True  # instruct 'postcmd()' to leave the main loop

    do_q = do_quit

    def postcmd(self, stop, line):  # pragma: no coverage
        if not line.startswith('shell'):
            self.session.commit()
        else:
            self.session.rollback()
        if stop:
            self.session.close()
        return stop


def main():  # pragma: no coverage
    parser = OptionParser(usage='%prog [-c FILE]')
    parser.add_option(
        "-c", "--conf", dest="conf_file", default='./Lasco.ini',
        help="use FILE as the configuration file (default is './Lasco.ini')",
        metavar="FILE")
    options, args = parser.parse_args()
    if not os.path.exists(options.conf_file):
        error = 'Could not find configuration file ("%s").' % options.conf_file
        sys.exit(error)
    cmd = LascoCmd(options.conf_file)
    cmd.cmdloop()


if __name__ == '__main__':  # pragma: no coverage
    main()
