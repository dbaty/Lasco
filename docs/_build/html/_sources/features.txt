========
Features
========

Galleries, albums, pictures
===========================

With Lasco, you can set up any number of galleries. Each gallery is
independent and may be managed by different users. The manager of a
gallery may add albums. Albums may contain pictures, video and/or
sound recordings. Items may have meta data: title, description, date
and time. That is all. Only the title and the descriptin can be
changed through a web interface. Extra picture metadata (camera model,
exposure time, focal length, etc.) are not stored or shown anywhere in
Lasco (although this could be added easily).


Access
======

Each gallery has a list of administrators. Each album has a list of
viewers (that include administrators of the corresponding gallery).
Users' rights can be granted and revoked through the command-line
interface.


Storage
=======

Pictures are stored on the file system. Only one version (size) of a
picture is needed. Lasco takes care of generating thumbnails of each
picture when requested (and store them in a cache if you wish).
Additional data is stored in a relational database.


Views
=====

There are three views:

- an album view that lists 8 thumbnails (or a different number
  depending on the configuration);

- a picture view that shows a single picture resized to fit on a
  regular screen (that is, the screen of a computer, not the screen of
  a tablet or a phone);

- the picture itself in its original size.


Misc
====

The user interface is available in English and French (auto-detection
of the user's preferred language, possibly overriden by the user in
the application) and comes with two themes (black or white
background). Several access keys are implemented to facilitate the
navigation in an album.