===========
Development
===========

Contributions
=============

Comments, feedback and contributions are most welcome. Do not hesitate
to report bugs in the `issue tracker`_ or send a pull request on
GitHub.

The source code evolved slowly over the last few years, from
``repoze.bfg`` to the latest versions of Pyramid, so the code may seem
dated here and there...

.. _issue tracker: https://github.com/dbaty/Lasco/issues


How to run the tests
====================

The test suite may be run with ``nosetests`` if you have installed
Nose, or ``python setup.py test`` otherwise. By default, an in-memory
SQLite database is used (which is fast). You may indicate a different
database by setting a ``TESTING_DB`` environment variable. It should
be a valid SQLAlchemy connection string, e.g.::

    postgresql+psycopg2://lasco:lasco@localhost/lasco

The code should be 100% covered with the exception of a few lines in
the command-line interface and the third-party EXIF module.


Development utilities
=====================

The source ships with a `Makefile` that contains a few utility rules,
amongst which:

``coverage`` (or simply ``cov``)
    ``make coverage`` runs Coverage.py, generates an HTML report and
    open it in your web browser.

``distcheck``
    ``make distcheck`` verifies that your current version of the code
    can be correctly installed on a virgin virtual environment. It
    basically builds a source distribution, creates a temporary
    virtual environment, installs the distribution there and run the
    tests.


Credits
=======

Lasco contains a module to extract EXIF information written by Gene
Cash (see ``ext/exif.py`` for the license). The pencil icon comes from
Mark James' `FamFamFam`_ `Silk icon set`_ that is licensed under the
`Creative Commons Attribution 3.0 License`_ (CC BY 3.0).

.. _`FamFamFam`: http://www.famfamfam.com/

.. _`Silk icon set`: http://www.famfamfam.com/lab/icons/silk/

.. _`Creative Commons Attribution 3.0 License`: http://creativecommons.org/licenses/by/3.0/

Lasco is written by Damien Baty and is licensed under the 3-clause BSD
license, a copy of which is included in the source and reproduced
below:

.. include:: ../LICENSE.txt