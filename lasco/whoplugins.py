"""An authentication plugin for ``repoze.who`` and SQLAlchemy."""

from zope.interface import implements

from repoze.who.interfaces import IAuthenticator
from repoze.who.interfaces import IMetadataProvider

from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from lasco.models import User
from lasco.models import DBSession


class BasePlugin(object):

    def get_user(self, **kwargs):
        session = DBSession()
        user = None
        try:
            user = session.query(User).filter_by(**kwargs).one()
        except (NoResultFound, MultipleResultsFound):
            pass
        return user


class SQLAlchemyAuthPlugin(BasePlugin):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        try:
            login = identity['login']
            password = identity['password']
        except KeyError:
            return None
        user = self.get_user(login=login)
        if user is None:
            return None
        if not user.validate_password(password):
            return None
        return user.id


class SQLAlchemyMetadataPlugin(BasePlugin):
    implements(IMetadataProvider)

    def add_metadata(self, environ, identity):
        user = self.get_user(id=identity['repoze.who.userid'])
        if user is not None:
            login = user.login
            fullname = user.fullname
            user_id = user.id
        else:
            login = fullname = user_id = None
        identity.update(login=login,
                        fullname=fullname,
                        id=user_id)


def make_auth_plugin():
    return SQLAlchemyAuthPlugin()


def make_md_plugin():
    return SQLAlchemyMetadataPlugin()
