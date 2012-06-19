import os
from setuptools import find_packages
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
DESCRIPTION = ('Lasco is a web picture gallery.')

requires = ('cryptacular',
            'pyramid',
            'pyramid_tm',
            'repoze.bitblt',
            'repoze.tm2',
            'repoze.who',
            'sqlalchemy',
            'zope.sqlalchemy')

setup(name='Lasco',
      version='0.1.0',
      description=DESCRIPTION,
      long_description='\n\n'.join((README, CHANGES)),
      classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Multimedia :: Graphics :: Presentation'),
      author='Damien Baty',
      author_email='damien.baty.remove@gmail.com',
      url='http://readthedocs.org/projects/lasco',
      keywords='web pyramid image picture gallery',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      message_extractors={'.': [
            ('**.py', 'lingua_python', None),
            ('**.pt', 'lingua_xml', None),
            ]},
      test_suite='lasco.tests',
      entry_points='''\
      [paste.app_factory]
      app = lasco.app:make_app

      [console_scripts]
      lascocli = lasco.lascocli:main
      '''
      )
