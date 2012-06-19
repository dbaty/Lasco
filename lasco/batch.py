# This file is part of Faceted Navigation.
#
# Copyright (c) 2008 by ENA (http://www.ena.fr)
#
# Faceted Navigation is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
"""A simple class that aims to help building batch navigations.

Purpose
=======

It allows to build navigation as in Google (among a lot of others),
i.e. something like this::

    _previous_ 1 2 3 4 [5] 6 7 8 9 10 _next_

If the user clicked on "6" or the "next" link, (s)he would then have
the following navigation::

    _previous_ 2 3 4 5 [6] 7 8 9 10 11 _next_

Note that the navigation is always "centered" on the current page.

Everything is configurable in the constructor of the class:

- ``batch_length``: (maximum) number of items shown on each page
  (default is 10);

- ``batch_n_pages``: (maximum) number of pages to be shown. Default
  value is 10, as in the example above. If this value was 5, the
  navigation would have looked like this::

     _previous_ 3 4 [5] 6 7 _next_


How to use (a.k.a. API)
=======================

We will use a very simple example: a list with 100 elements, 10
elements per page, 5 pages to show, showing the last page::

    >>> from batch import Batch
    >>> items = range(1, 101) ## 1..100
    >>> batch = Batch(items, batch_n_pages=5, current=5)

Hopefully, we can access all items::

    >>> list(batch) == items
    True
    >>> [i for i in batch if i == 2]
    [2]
    >>> batch.total_length == len(items)
    True

We can also access the current "slice", i.e. the current page of the
batch::

    >>> batch.current
    5
    >>> batch.slice == range(41, 51) ## 41..50
    True

We can also access the numbers of the pages of the batch::

    >>> batch.pages
    [3, 4, 5, 6, 7]

We know whether or not there is a previous and/or next page::

    >>> batch.next
    6
    >>> batch.previous
    4

And we know the number of the last page::

    >>> batch.last
    10

If there were no previous and next page, the values of the
corresponding properties would be ``None``::

    >>> batch = Batch([])
    >>> batch.previous == None
    True
    >>> batch.next == None
    True

Actually, this is a special case::

    >>> batch.total_length
    0
    >>> batch.pages
    []
    >>> batch.slice
    []

The ``current`` parameter is a counter that starts at 1:

    >>> batch = Batch([1, 2, 3], current=0)
    Traceback (most recent call last):
    ...
    ValueError: Value for current (0) must be >= 1

And it cannot be greater than the number of pages, naturally:

    >>> batch = Batch([1, 2, 3], batch_length=5, current=2)
    Traceback (most recent call last):
    ...
    ValueError: Value for current (2) must be less than or equal to the number of pages (1)
"""


class Batch(object):

    def __init__(self, all_items,
                 batch_length=10, batch_n_pages=10, current=1):
        """See module docstring for further details."""
        self._total_length = len(all_items)
        self._all_items = all_items

        if not self._total_length:
            # Special case when we get an empty sequence
            self._current = current
            self._pages = []
            self._slice = self._all_items
            self._previous = self._next = None
            return

        n_pages = 1 + (self._total_length - 1) / batch_length
        if current < 1:
            raise ValueError('Value for current (%s) must be >= 1' %
                             current)
        if current > n_pages:
            raise ValueError('Value for current (%s) must be less '
                             'than or equal to the number of pages '
                             '(%s)' % (current, n_pages))

        self._current = current

        start = (self._current - 1) * batch_length
        end = start + batch_length
        self._slice = self._all_items[start:end]

        before = batch_n_pages / 2
        first = max(1, self._current - before)
        last = min(n_pages, first + batch_n_pages - 1)
        first = max(1, last - batch_n_pages + 1)

        self._previous = self._next = None
        if current > 1:
            self._previous = self._current - 1
        if current < n_pages:
            self._next = self._current + 1
        self._pages = range(first, last + 1)
        self._last = n_pages

    def __getitem__(self, index):
        return self._all_items.__getitem__(index)

    @property
    def slice(self):
        return self._slice

    @property
    def total_length(self):
        return self._total_length

    @property
    def current(self):
        return self._current

    @property
    def pages(self):
        return self._pages

    @property
    def previous(self):
        return self._previous

    @property
    def next(self):
        return self._next

    @property
    def last(self):
        return self._last
