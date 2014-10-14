.. toctree::
   :maxdepth: 4

API Objects
###########
The classes and functions documented on this page constitute the public API to
the okcupyd library.

:class:`~okcupyd.user.User`
===========================

:class:`~okcupyd.user.User` serves as the primary entry point to the okcupyd
library. Most of the objects mentioned on this page are accessible in some way
or another from instances of :class:`~okcupyd.user.User`.

.. autoclass:: okcupyd.user.User
    :members:
    :special-members: __init__

:class:`~okcupyd.profile.Profile`
=================================

.. autoclass:: okcupyd.profile.Profile
    :members:
    
:class:`~okcupyd.looking_for.LookingFor`
========================================
.. autoclass:: okcupyd.looking_for.LookingFor
    :members:
    
:class:`~okcupyd.details.Details`
=================================
.. autoclass:: okcupyd.details.Details
    :members:
    :undoc-members:
    
:class:`~okcupyd.essay.Essays`
==============================
.. autoclass:: okcupyd.essay.Essays
    :members:

    .. py:attribute:: self_summary

        The contents of the essay labeled 'Self Summary'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: my_life

        The contents of the essay labeled 'What I'm doing with my life'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: good_at

        The contents of the essay labeled 'I'm really good at'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: people_first_notice

        The contents of the essay labeled 'The first thing people notice about me'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: favorites

        The contents of the essay labeled 'Favorite books, movies, shows, music, and food'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: six_things

        The contents of the essay labeled 'Six things I could never live without'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: think_about

        The contents of the essay labeled 'I spend a lot of time thinking about'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: friday_night

        The contents of the essay labeled 'On a typical friday night I am'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: private_admission

        The contents of the essay labeled 'The most private thing I'm willing to admit'. Write to this attribute to change its value for the logged in user.

    .. py:attribute:: message_me_if

        The contents of the essay labeled 'You should message me if'. Write to this attribute to change its value for the logged in user.


:class:`~okcupyd.photo.PhotoUploader`
=====================================

.. autoclass:: okcupyd.photo.PhotoUploader
    :members:
    
:class:`~okcupyd.photo.Info`
============================
.. autoclass:: okcupyd.photo.Info
    :members:
    
:class:`~okcupyd.messaging.MessageThread`
=========================================
.. autoclass:: okcupyd.messaging.MessageThread
    :members:
    
:class:`~okcupyd.messaging.Message`
===================================
.. autoclass:: okcupyd.messaging.Message
    :members:
    
:class:`~okcupyd.question.Questions`
====================================
.. autoclass:: okcupyd.question.Questions
    :members:

    .. py:attribute:: mandatory

       A :class:`~okcupyd.util.fetchable.Fetchable` of
       :class:`~okcupyd.question.UserQuestion` instances that correspond to
       questions that have been answered by the logged in user and assigned the
       'mandatory' importance.

    .. py:attribute:: very_important

       A :class:`~okcupyd.util.fetchable.Fetchable` of
       :class:`~okcupyd.question.UserQuestion` instances that correspond to
       questions that have been answered by the logged in user and assigned the
       'very_important' importance.

    .. py:attribute:: somewhat_important

       A :class:`~okcupyd.util.fetchable.Fetchable` of
       :class:`~okcupyd.question.UserQuestion` instances that correspond to
       questions that have been answered by the logged in user and assigned the
       'somewhat_important' importance.

    .. py:attribute:: little_important

       A :class:`~okcupyd.util.fetchable.Fetchable` of
       :class:`~okcupyd.question.UserQuestion` instances that correspond to
       questions that have been answered by the logged in user and assigned the
       'little_important' importance.

    .. py:attribute:: not_important

       A :class:`~okcupyd.util.fetchable.Fetchable` of
       :class:`~okcupyd.question.UserQuestion` instances that correspond to
       questions that have been answered by the logged in user and assigned the
       'not_important' importance.

    
:class:`~okcupyd.question.Question`
===================================
.. autoclass:: okcupyd.question.Question
    :members:

:class:`~okcupyd.question.UserQuestion`
=======================================

.. autoclass:: okcupyd.question.UserQuestion
    :members:

:class:`~okcupyd.question.AnswerOption`
=======================================

.. autoclass:: okcupyd.question.AnswerOption
    :members:
    
:func:`~okcupyd.search.SearchFetchable`
========================================
.. autofunction:: okcupyd.search.SearchFetchable
    
:class:`~okcupyd.attractiveness_finder._AttractivenessFinder`
=============================================================
.. autoclass:: okcupyd.attractiveness_finder._AttractivenessFinder
    :members:

:class:`~okcupyd.profile_copy.Copy`
========================================
.. autoclass:: okcupyd.profile_copy.Copy
    :members:
    :special-members: __init__
    
:class:`~okcupyd.statistics.Statistics`
=======================================
.. autoclass:: okcupyd.statistics.Statistics
    :members:

:func:`~okcupyd.util.misc.add_command_line_options`
===================================================
.. autofunction:: okcupyd.util.misc.add_command_line_options

:func:`~okcupyd.util.misc.handle_command_line_options`
======================================================
.. autofunction:: okcupyd.util.misc.handle_command_line_options
