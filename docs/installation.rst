==============================
Installation and configuration
==============================

Dependencies and prerequisites
==============================

Lasco requires Python 2.7 and an RDBMS. I test with SQLite and use
PostgreSQL on production. Other RDBMS should work as well.


Installation and configuration
==============================

Here below is the shortest path to test Lasco. It is highly
recommended to install Lasco in a `virtual environment
<http://www.virtualenv.org/en/latest/index.html>`_:

.. code-block:: bash

   $ mkdir test-lasco
   $ cd test-lasco
   $ mkdir src pics cache
   $ cd src
   $ # As of this writing, Lasco relies on a feature of
     # 'repoze.bitblt' that has not yet been released
   $ wget -O - --no-check-certificate https://github.com/repoze/repoze.bitblt/tarball/master | tar xvz
   $ cd repoze-repoze.bitblt-*
   $ python setup.py install
   $ cd ../../
   $ easy_install Lasco

You may check the installation with the following command:

.. code-block:: bash

   $ lascocli --help
   Usage: lascocli [-i FILE]

   Options:
     -h, --help           show this help message and exit
     -i FILE, --ini=FILE  use FILE as the 'ini' file (default is './Lasco.ini')

On certain platforms (MacOS X 10.4, for example), you may have the
following error::

    ImportError: No module named readline

In this case, you need to install ``readline``:

.. code-block:: bash

   $ easy_install readline

Once you have installed the application, you need to fetch
configuration files. Some development files are available from the
source repository.

.. code-block:: bash

   $ wget --no-check-certificate https://raw.github.com/dbaty/Lasco/master/dev.ini
   $ wget --no-check-certificate https://raw.github.com/dbaty/Lasco/master/who.ini

Then edit ``dev.ini`` and change the following variables:

.. code-block:: ini

   lasco.pictures_base_path = /path/to/test-lasco/pics
   lasco.cache = /path/to/test-lasco/cache

You may also change the database, but a default SQLite will be good
enough for a test.

If you do have pictures, copy them in a directory under
``/path/to/test-lasco/pics`` (for example in
``/path/to/test-lasco/pics/holidays-2010``). If you do not have
pictures at hand... wait, why would you want a gallery, then? Anyway,
there are plenty of pictures set on the web, here is one with around
30 pictures:

.. code-block:: bash

   $ cd pics
   $ mkdir australia
   $ cd australia
   $ wget -r -np -nd -A "*.jpg" http://www.cs.washington.edu/research/imagedatabase/groundtruth/australia/
   $ ls *.jpg | wc -l
         30
   $ cd ../..

You now need to record these pictures in Lasco. There is no web
interface for this, you must use the command line interface.

.. code-block:: bash

   $ lascocli -c dev.ini
   lasco> gallery_add test "Test gallery"
   => Gallery has been added.
   lasco> album_add test australia Australia /path/to/test-lasco/pics/australia
   => Album has been added.

Ok, our pictures are in the database, but you need a user account to
access them. For this test, we will just create a gallery
administrator, but you may create simple album viewers as well.

.. code-block:: bash

   (continued from the 'lascocli' session above)
   lasco> user_add test test test
   lasco> gallery_users test +test
   lasco> quit

All right, you are almost ready, you just need to install a WSGI server:

.. code-block:: bash

   $ easy_install waitress

Finally, we can start the application:

.. code-block:: bash

   $ pserve dev.ini
   Starting server in PID 15304.
   serving on http://0.0.0.0:6543

If you visit http://0.0.0.0:6543 and connect with the ``test`` login
and the ``test`` password, you should be able to access the gallery
and see your pictures.